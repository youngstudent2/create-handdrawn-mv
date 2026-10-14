from pathlib import Path
import math, json, argparse, subprocess, time, bisect
from collections import Counter
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import moderngl
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output';OUT.mkdir(exist_ok=True)
W,H=1920,1080
CUTS=[0,2.194,4.017,6.571,8.719,11.447,13.375,16.742,18.564,21.455,23.638,25.832,30]
PAPER=(1.,.970,.924)
def sat(x):return max(0,min(1,x))
def smooth(x):x=sat(x);return x*x*(3-2*x)
def mix(a,b,t):return a+(b-a)*t
VERT='''#version 330
in vec2 in_pos; in vec2 in_uv; out vec2 uv;
uniform vec2 viewport; uniform vec2 center; uniform vec2 size; uniform float angle; uniform float tm; uniform float deform;
void main(){uv=in_uv; vec2 p=in_pos; p.x+=deform*sin(tm*2.1+p.y*6.)*pow(clamp(in_uv.y,0.,1.),2.);p.y+=deform*.3*sin(tm*1.6+in_uv.x*5.);p*=size;float a=radians(angle);p=mat2(cos(a),sin(a),-sin(a),cos(a))*p+center;gl_Position=vec4(p.x/viewport.x*2.-1.,1.-p.y/viewport.y*2.,0.,1.);}
'''
FRAG='''#version 330
in vec2 uv; out vec4 col;uniform sampler2D tex;uniform float opacity;uniform int art;uniform vec3 base;uniform float reveal;uniform int side;
void main(){vec4 c=texture(tex,uv);float a=c.a*opacity; if(art==1){vec3 pigment=clamp(c.rgb/base,0.,1.);c.rgb=vec3(1.,.970,.924)*pigment;float edge=smoothstep(0.,.025,uv.x)*smoothstep(0.,.025,1.-uv.x);a*=edge;}if(reveal<.999){float v=side==0?uv.x:uv.y; a*=1.-smoothstep(reveal-.04,reveal+.04,v);}col=vec4(c.rgb,a);}
'''
FULLVERT='''#version 330
in vec2 p;out vec2 uv;void main(){uv=p*.5+.5;gl_Position=vec4(p,0.,1.);}
'''
BGFRAG='''#version 330
in vec2 uv;out vec4 col;uniform float tm;
float noise(vec2 p){return fract(sin(dot(p,vec2(12.9898,78.233)))*43758.5453);}
void main(){float n=noise(floor(uv*vec2(1920.,1080.)))*.006;float d=length(uv-vec2(.5));vec3 c=vec3(1.,.970,.924)-n-d*.011;col=vec4(c,1.);}
'''
POST='''#version 330
in vec2 uv;out vec4 col;uniform sampler2D a;uniform sampler2D b;uniform float progress;uniform int mode;uniform float tm;uniform float fade;
void main(){vec4 x=texture(a,uv),y=texture(b,uv);float p=progress;vec4 paper=vec4(1.,.970,.924,1.);vec4 c=x;
// A brief dip through paper never superimposes two bodies or hands.
if(mode==5){c=p<.5?mix(x,paper,smoothstep(0.,.5,p)):mix(paper,y,smoothstep(.5,1.,p));}
c.rgb=mix(vec3(1.,.970,.924),c.rgb,fade);col=c;}
'''
class Renderer:
 def __init__(self,width=1920):
  self.width=width;self.height=round(width*9/16);self.ctx=moderngl.create_standalone_context(backend='egl');c=self.ctx
  self.prog=c.program(vertex_shader=VERT,fragment_shader=FRAG)
  N=26;vs=[]
  for j in range(N):
   for i in range(N):
    for dx,dy in [(0,0),(1,0),(0,1),(1,0),(1,1),(0,1)]:
     x=(i+dx)/N;y=(j+dy)/N;vs.extend([x-.5,y-.5,x,y])
  self.vbo=c.buffer(np.array(vs,'f4').tobytes());self.vao=c.vertex_array(self.prog,[(self.vbo,'2f 2f','in_pos','in_uv')])
  full=c.buffer(np.array([-1,-1,1,-1,-1,1,1,-1,1,1,-1,1],'f4').tobytes())
  self.bg=c.program(vertex_shader=FULLVERT,fragment_shader=BGFRAG);self.bgv=c.vertex_array(self.bg,[(full,'2f','p')])
  self.post=c.program(vertex_shader=FULLVERT,fragment_shader=POST);self.postv=c.vertex_array(self.post,[(full,'2f','p')])
  self.fbos=[c.framebuffer(color_attachments=[c.texture((self.width,self.height),3)]) for _ in range(3)]
  self.tex={};self.spec={};self.tm=0;self.asset_paths={};self.shown=Counter();self.frame_assets=set()
  c.enable(moderngl.BLEND);c.blend_func=(moderngl.SRC_ALPHA,moderngl.ONE_MINUS_SRC_ALPHA)
  self.font=ROOT/'assets/WenKai.ttf'
  for i in range(1,13):
   for k in ['A','B']:
    revised=i in (7,10,11)
    rel=f'assets/{"revised/" if revised else ""}shot_{i:02d}_{k}.png'
    im=Image.open(ROOT/rel).convert('RGBA');self.add(f'{i}{k}',im,art=not revised);self.asset_paths[f'{i}{k}']=rel
  self.build_graphics()
 def add(self,key,im,art=False):
  im=im.convert('RGBA');arr=np.asarray(im)
  if art:
   edge=np.concatenate([arr[:12,:,:3].reshape(-1,3),arr[-12:,:,:3].reshape(-1,3),arr[:,:12,:3].reshape(-1,3),arr[:,-12:,:3].reshape(-1,3)])
   base=tuple(np.percentile(edge,90,axis=0)/255)
  else:base=(1,1,1)
  t=self.ctx.texture(im.size,4,im.tobytes());t.filter=(moderngl.LINEAR,moderngl.LINEAR);self.tex[key]=t;self.spec[key]=(im.width,im.height,art,base)
 def text(self,key,lines,fontsize=56,color=(133,107,95,255),align='left',spacing=20):
  if isinstance(lines,str):lines=[lines]
  font=ImageFont.truetype(str(self.font),fontsize);w=max(int(font.getlength(s)) for s in lines)+20;h=(fontsize+spacing)*len(lines)+25
  im=Image.new('RGBA',(w,h));d=ImageDraw.Draw(im)
  for i,s in enumerate(lines):
   x=10 if align=='left' else (w-font.getlength(s))/2;d.text((x,i*(fontsize+spacing)),s,font=font,fill=color)
  self.add(key,im)
 def build_graphics(self):
  self.text('title',['因为喜欢你'],90,(111,128,120,255));self.text('subtitle','克琪亚 · 中华娘手书',34,(155,127,115,255));self.text('english','a little love, every day',29,(172,145,127,255))
  lines={1:['忍不住，','再多看你一眼。'],2:['嗨，','今天也想见到你。'],3:['你的消息，','会让我偷偷开心。'],4:['这杯茶，','想和你一起喝。'],5:['最后一块小饼干，','也留给你。'],6:['你看——'],7:['呀，被发现了。'],8:['有句话，','练习了好久。'],9:['今天，','想再靠近一点。'],10:['和你在一起，','就会不自觉地笑。']}
  for i,txt in lines.items():self.text('caption'+str(i),txt,53)
  self.text('final','喜欢你，是每一天的小事。',40,(147,118,108,255))
  self.text('cookie_note','给你 ♡',35,(178,132,129,255));self.text('hello','嗨！',48,(163,130,120,255));self.text('ellipsis','……',45)
  for key in ['petal','heart','star','ring','line']:
   im=Image.new('RGBA',(200,200));d=ImageDraw.Draw(im)
   if key=='petal':
    d.polygon([(105,22),(151,60),(157,115),(102,165),(48,122),(44,65)],fill=(224,162,163,110));d.arc((48,32,152,171),10,160,fill=(194,131,142,140),width=2)
   elif key=='heart':
    pts=[]
    for th in np.linspace(0,math.tau,140):pts.append((100+4.3*16*math.sin(th)**3,95-4.3*(13*math.cos(th)-5*math.cos(2*th)-2*math.cos(3*th)-math.cos(4*th))))
    d.line(pts,fill=(182,111,121,185),width=3);d.line([(x+2,y+1) for x,y in pts],fill=(196,133,139,75),width=2)
   elif key=='star':
    d.line([(100,34),(111,88),(158,100),(111,110),(100,161),(88,109),(40,100),(89,90),(100,34)],fill=(153,157,130,180),width=3)
   elif key=='ring':
    d.ellipse((25,25,175,175),outline=(161,174,155,105),width=2);d.arc((21,28,178,181),32,240,fill=(176,147,127,80),width=2)
   else:
    d.line([(15,105),(50,103),(87,108),(124,104),(180,106)],fill=(190,141,141,150),width=3)
   self.add(key,im)
 def draw(self,key,x,y,w=None,h=None,angle=0,alpha=1,deform=0,reveal=1,side=0):
  if alpha<.001:return
  if key in self.asset_paths:self.frame_assets.add(self.asset_paths[key])
  iw,ih,art,base=self.spec[key];w=iw if w is None else w;h=w*ih/iw if h is None else h
  p=self.prog;p['viewport'].value=(W,H);p['center'].value=(x,y);p['size'].value=(w,h);p['angle'].value=angle;p['tm'].value=self.tm;p['deform'].value=deform;p['opacity'].value=sat(alpha);p['art'].value=int(art);p['base'].value=base;p['reveal'].value=reveal;p['side'].value=side
  self.tex[key].use(0);p['tex'].value=0;self.vao.render()
 def pose(self,i,u,x,y,w,angle=0,deform=.003):
  # One opaque pose per frame. No A/B ghosting and no reverse B-A-B loop.
  change={7:.47,10:.48,11:.45}.get(i,.45)
  key='A' if u<change else 'B'
  self.draw(f'{i}{key}',x,y,w=w,angle=angle,deform=deform)
 def caption(self,idx,x,y,u,scale=1,center=False):
  key='caption'+str(idx);iw,ih,*_=self.spec[key]
  self.draw(key,x+(0 if center else iw*scale/2),y,w=iw*scale,alpha=smooth(u/.17),reveal=smooth(u/.25))
 def petals(self,t,count=13,intensity=1):
  for k in range(count):
   x=((k*173+t*(18+k%3*10))%(W+240))-120;y=((k*241+t*(32+k%4*8))%(H+300))-150
   self.draw('petal',x,y,w=22+(k%4)*16,angle=k*53+t*(14+k),alpha=.28*intensity)
 def scene(self,i,t,slot):
  f=self.fbos[slot];f.use();self.ctx.viewport=(0,0,self.width,self.height);self.ctx.disable(moderngl.BLEND);self.bgv.render();self.ctx.enable(moderngl.BLEND)
  self.tm=t;s=t-CUTS[i];duration=CUTS[i+1]-CUTS[i];u=sat(s/duration);q=smooth(u);sw=math.sin(t*1.8)
  if i==0:
   self.pose(1,u,1370-25*q,600,1490+40*q,angle=-1+2*q)
   self.draw('title',485,414,w=610,alpha=smooth(s/.6),reveal=smooth(s/.85));self.draw('subtitle',468,514,w=415,alpha=smooth((s-.3)/.5));self.draw('english',437,577,w=350,alpha=smooth((s-.5)/.55))
   self.draw('line',476,475,w=580,h=110,reveal=smooth((s-.3)/.65));self.petals(t,15)
  elif i==1:
   self.pose(2,u,600+22*q,536,1120+90*q,angle=1-2*q,deform=.001)
   self.caption(i,1290,535,u);self.draw('heart',1630,310,w=60+6*sw,alpha=smooth(s/.4)*.6)
  elif i==2:
   self.pose(3,u,1310-30*q,552,1130+24*sw,angle=-1.4+2*q)
   self.caption(i,222,480,u);self.draw('hello',980,253,w=120,angle=-12,alpha=smooth((s-.4)/.3));self.draw('star',1730,315,w=76,angle=t*12,alpha=.6);self.petals(t,9)
  elif i==3:
   self.pose(4,u,605+18*sw,551,1210+30*q,angle=1-q)
   self.caption(i,1265,445,u);self.draw('heart',1575,260-20*q,w=62,angle=12,alpha=smooth((u-.42)/.2)*.7)
   self.draw('heart',1715,315-40*q,w=37,angle=-8,alpha=smooth((u-.48)/.2)*.5)
  elif i==4:
   self.pose(5,u,1255-30*q,583,1200+40*q,angle=-1+q)
   self.caption(i,215,422,u);self.draw('ring',565,740,w=175+18*q,alpha=.28);self.petals(t,8)
  elif i==5:
   self.pose(6,u,655+18*q,558,1170+90*q,angle=1-2*q)
   self.caption(i,1215,458,u);self.draw('cookie_note',1360,654,w=175,angle=6,alpha=smooth((u-.43)/.12));self.draw('star',1660,675,w=66+12*sw,angle=-t*8,alpha=.6)
  elif i==6:
   self.draw('ring',1145,554,w=1090,alpha=.09)
   self.pose(7,u,1145,550,640,angle=0,deform=0)
   self.caption(i,252,474,u);self.petals(t,9,.7)
  elif i==7:
   self.pose(8,u,1285+10*sw,581,1230+45*q,angle=-1.4+q,deform=.002)
   self.caption(i,250,523,u);self.draw('petal',1040+70*q,50+240*q,w=64,angle=t*25,alpha=(1-smooth((u-.42)/.12))*.65)
  elif i==8:
   self.pose(9,u,640+20*q,550,1150+45*q,angle=1.2-1.7*q,deform=.002)
   self.caption(i,1250,440,u);self.draw('ellipsis',1600,636,w=123,alpha=1-smooth((u-.48)/.12))
   self.draw('heart',1600,647,w=75,alpha=smooth((u-.48)/.12)*.65);self.petals(t,7)
  elif i==9:
   self.pose(10,u,960,570,1920,angle=0,deform=0)
   self.caption(i,1280,180,u,scale=.86);self.draw('heart',1520,350,w=58,alpha=smooth((u-.50)/.15)*.65)
  elif i==10:
   self.pose(11,u,1290,590,1100,angle=0,deform=0)
   self.caption(i,215,495,u);self.draw('star',1630,227,w=55,angle=t*8,alpha=.5);self.petals(t,13)
  elif i==11:
   self.pose(12,u,1320-35*q,530,1200+28*q,angle=.4*sw,deform=.002)
   self.draw('title',486,397,w=610,alpha=smooth(s/.65),reveal=smooth(s/.7));self.draw('final',472,508,w=557,alpha=smooth((s-.3)/.6));self.draw('subtitle',460,589,w=380,alpha=smooth((s-.5)/.7))
   self.draw('line',468,463,w=580,h=110,reveal=smooth((s-.35)/.5));self.draw('heart',709,288,w=55+6*sw,angle=-6,alpha=.7*smooth(s/.5));self.petals(t,16)
  return f
 def frame(self,t):
  self.frame_assets=set()
  i=min(11,bisect.bisect_right(CUTS,t)-1);mode=0;p=0
  # Beat cuts elsewhere; short paper dips only at changes of scene scale.
  trans={5:.18,8:.16,10:.18}.get(i,0)
  self.scene(i,t,0)
  if trans and i<11 and CUTS[i+1]-t<trans:
   p=(t-(CUTS[i+1]-trans))/trans
   if p>=.5:self.frame_assets.clear()
   outgoing=set(self.frame_assets)
   self.scene(i+1,CUTS[i+1],1);mode=5
   if p<.5:self.frame_assets=outgoing
  self.fbos[2].use();self.ctx.disable(moderngl.BLEND);self.fbos[0].color_attachments[0].use(0);self.fbos[1].color_attachments[0].use(1)
  z=self.post;z['a'].value=0;z['b'].value=1;z['progress'].value=p;z['mode'].value=mode;z['fade'].value=min(smooth(t/.28),smooth((30-t)/.7))
  self.postv.render()
  if z['fade'].value>.001:self.shown.update(self.frame_assets)
  return self.fbos[2].read(components=3,alignment=1)
 def sample(self,t,path):
  b=self.frame(t);Image.frombytes('RGB',(self.width,self.height),b).transpose(Image.Transpose.FLIP_TOP_BOTTOM).save(path,quality=94)

def main():
 p=argparse.ArgumentParser();p.add_argument('--width',type=int,default=1920);p.add_argument('--fps',type=int,default=30);p.add_argument('--samples',action='store_true');p.add_argument('--output');a=p.parse_args();r=Renderer(a.width)
 if a.samples:
  imgs=[]
  for i in range(12):
   t=mix(CUTS[i],CUTS[i+1],.68);path=OUT/f'shot{i+1:02d}.jpg';r.sample(t,path);im=Image.open(path);im.thumbnail((480,270));imgs.append(im)
  board=Image.new('RGB',(1920,810),'#fff7e8')
  for i,im in enumerate(imgs):board.paste(im,(i%4*480,i//4*270))
  board.save(OUT/'storyboard.jpg',quality=95);print('samples ready');return
 dst=Path(a.output) if a.output else OUT/'Cookiya_Because_I_Like_You_30s.mp4'
 cmd=['ffmpeg','-hide_banner','-loglevel','warning','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{r.width}x{r.height}','-r',str(a.fps),'-i','-','-i',str(ROOT/'assets/music.m4a'),'-map','0:v','-map','1:a:0','-t','30','-vf','vflip','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-af','afade=t=in:d=0.12,afade=t=out:st=28.6:d=1.4','-movflags','+faststart',str(dst)]
 proc=subprocess.Popen(cmd,stdin=subprocess.PIPE);start=time.time()
 for n in range(30*a.fps):
  proc.stdin.write(r.frame(n/a.fps))
  if n%90==0:print(f'{n}/{30*a.fps} frames, elapsed {time.time()-start:.1f}s',flush=True)
 proc.stdin.close();rc=proc.wait();assert rc==0,rc
 (OUT/'render_manifest.json').write_text(json.dumps({'revision':2,'duration':30,'dimensions':[r.width,r.height],'fps':a.fps,'cuts':CUTS,'shots':12,'keyframes':24,'poses':list(r.asset_paths.values()),'audio':'user-supplied reference video 00:00–00:30','process':'Single-pose exposure; grounded fullbody; simple palm contact; corrected laughing gesture; beat cuts and brief paper dips; no footer credits'},ensure_ascii=False,indent=2))
 (OUT/'usage.json').write_text(json.dumps({'used_keyframes':sorted(r.shown),'shown_frames':dict(r.shown),'note':'Counts are draw submissions contributing to the post-composite; visual review separately checks visibility.'},indent=2));print(str(dst),flush=True)
if __name__=='__main__':main()
