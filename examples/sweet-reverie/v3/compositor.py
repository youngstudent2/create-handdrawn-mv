"""Headless ModernGL/GLSL paired-pose compositor. Run render_v3.py for the film."""
import os,math,json,re
os.environ.setdefault('LP_NUM_THREADS','6')
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageChops,ImageOps
from scipy import ndimage
import moderngl
ROOT=Path(__file__).resolve().parent; ASSETS=ROOT.parent/'assets'; SH=ROOT/'shaders'
TAU=math.tau

def sat(v):return max(0.,min(1.,v))
def ease(v):v=sat(v);return 1-(1-v)**3
def smooth(v):v=sat(v);return v*v*(3-2*v)
def mix(a,b,t):return a+(b-a)*t

def prepare_images(allow_partial=False):
 ims={}
 for n in ['cosmos_bg','dream_bg','theatre_bg']:
  im=Image.open(ASSETS/(n+'.png')).convert('RGBA')
  if n.startswith('cookiya'):im=im.crop(im.getchannel('A').getbbox())
  ims[n]=im
 # Paired keyframes share one crop, retaining the generated alignment across A/B.
 for i in range(1,20):
  if allow_partial and not all((ROOT/'assets'/f'shot_{i:02d}_{k}.png').exists() for k in ['A','B']):continue
  a=Image.open(ROOT/'assets'/f'shot_{i:02d}_A.png').convert('RGBA')
  b=Image.open(ROOT/'assets'/f'shot_{i:02d}_B.png').convert('RGBA')
  if b.size!=a.size:b=b.resize(a.size,Image.Resampling.LANCZOS)
  bounds=ImageChops.lighter(a.getchannel('A'),b.getchannel('A')).getbbox()
  for name,im in [('A',a),('B',b)]:ims[f'shot_{i:02d}_{name}']=ImageOps.expand(im.crop(bounds),border=12,fill=(0,0,0,0))
 atlas=Image.open(ASSETS/'props_atlas.png').convert('RGBA')
 boxes={'cookie':(20,25,450,445),'ribbon':(455,135,1085,440),'eye':(1100,130,1535,425),'bouquet':(25,465,470,1000),'cup':(500,510,1045,950),'frame':(1050,455,1535,1015)}
 for n,b in boxes.items():
  im=atlas.crop(b);ims[n]=im.crop(im.getchannel('A').getbbox())
 at2=Image.open(ASSETS/'props_atlas_v2.png').convert('RGBA');arr=np.array(at2);lab,num=ndimage.label(arr[:,:,3]>30)
 boxes2={'cloud':(31,107,611,430),'butterfly':(587,56,1089,453),'clock':(1098,45,1502,468),'paperframe':(115,493,507,977),'daisy':(1080,537,1519,972),'chip0':(619,539,828,754),'chip1':(836,552,1024,810),'chip2':(610,744,741,910),'chip3':(735,740,987,949)}
 for n,b in boxes2.items():
  x0,y0,x1,y1=b;section=lab[y0:y1,x0:x1];counts=np.bincount(section.ravel());counts[0]=0;label=counts.argmax()
  mask=ndimage.binary_dilation(lab==label,iterations=3)
  a=arr.copy();a[:,:,3]=np.where(mask,a[:,:,3],0)
  im=Image.fromarray(a).crop((max(0,x0-3),max(0,y0-3),min(at2.width,x1+3),min(at2.height,y1+3)))
  ims[n]=im
 # Native graphic layers: ornamental marks, text and particle sprites.
 im=Image.new('RGBA',(1024,1024));d=ImageDraw.Draw(im)
 for r in [475,466,425,330]:d.ellipse((512-r,512-r,512+r,512+r),outline=(238,216,165,190),width=2)
 for i in range(120):
  a=i*TAU/120;r=440 if i%5==0 else 458
  d.line((512+math.cos(a)*r,512+math.sin(a)*r,512+math.cos(a)*474,512+math.sin(a)*474),fill=(251,237,208,200),width=2)
 for i in range(12):
  a=i*TAU/12;cx=512+330*math.cos(a);cy=512+330*math.sin(a);d.ellipse((cx-7,cy-7,cx+7,cy+7),outline=(210,231,245,220),width=2)
 ims['sigil']=im
 im=Image.new('RGBA',(96,96));d=ImageDraw.Draw(im)
 d.polygon([(48,1),(55,40),(95,48),(55,55),(48,95),(41,55),(1,48),(41,41)],fill=(247,239,219,245))
 ims['star']=im
 im=Image.new('RGBA',(96,96));d=ImageDraw.Draw(im);d.ellipse((30,30,66,66),fill=(182,220,255,170));im=im.filter(ImageFilter.GaussianBlur(9));ims['glow']=im
 im=Image.new('RGBA',(300,300));d=ImageDraw.Draw(im);d.ellipse((5,5,295,295),outline=(183,230,255,180),width=3);d.arc((12,12,284,284),205,278,fill=(244,250,255,235),width=9);ims['bubble']=im
 fonts={'serif':'/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf','italic':'/usr/share/fonts/opentype/urw-base35/P052-Italic.otf'}
 for key,text,fontname,size,tracking in [('title','COOKIYA','serif',140,22),('sweet','SWEET','serif',180,8),('reverie','REVERIE','serif',170,10),('subtitle','Sweet Reverie','italic',75,7),('small','A COOKIE-SCENTED DREAM','serif',34,8)]:
  font=ImageFont.truetype(fonts[fontname],size);length=sum(font.getlength(c) for c in text)+(len(text)-1)*tracking
  im=Image.new('RGBA',(int(length)+24,int(size*1.8)));d=ImageDraw.Draw(im);x=12
  for c in text:d.text((x,12),c,font=font,fill=(253,237,212,255));x+=font.getlength(c)+tracking
  ims[key]=im.crop(im.getbbox())
 return ims

class Compositor:
 def __init__(self,width=1440,allow_partial=False):
  self.w=width;self.h=width*3//4;self.ctx=moderngl.create_standalone_context(backend='egl')
  c=self.ctx
  self.images=prepare_images(allow_partial);self.textures={}
  for k,im in self.images.items():
   tx=c.texture(im.size,4,im.tobytes());tx.build_mipmaps();tx.filter=(moderngl.LINEAR_MIPMAP_LINEAR,moderngl.LINEAR);tx.repeat_x=False;tx.repeat_y=False;self.textures[k]=tx
  self.sprite=c.program(vertex_shader=(SH/'sprite.vert').read_text(),fragment_shader=(SH/'sprite.frag').read_text())
  grid=[];nx,ny=16,24
  for y in range(ny):
   for x in range(nx):
    a=(x/nx,y/ny);b=((x+1)/nx,y/ny);dd=(x/nx,(y+1)/ny);e=((x+1)/nx,(y+1)/ny);grid.extend([a,b,dd,b,e,dd])
  self.grid=c.vertex_array(self.sprite,[(c.buffer(np.array(grid,'f4').tobytes()),'2f','in_uv')])
  self.quad=c.vertex_array(self.sprite,[(c.buffer(np.array([[0,0],[1,0],[0,1],[1,0],[1,1],[0,1]],'f4').tobytes()),'2f','in_uv')])
  self.fullbuf=c.buffer(np.array([[-1,-1],[1,-1],[-1,1],[1,-1],[1,1],[-1,1]],'f4').tobytes())
  self.bg=c.program(vertex_shader=(SH/'full.vert').read_text(),fragment_shader=(SH/'background.frag').read_text())
  self.bgvao=c.vertex_array(self.bg,[(self.fullbuf,'2f','in_pos')])
  self.fx=c.program(vertex_shader=(SH/'full.vert').read_text(),fragment_shader=(SH/'effects.frag').read_text())
  self.fxvao=c.vertex_array(self.fx,[(self.fullbuf,'2f','in_pos')])
  self.fb=[];self.ft=[]
  for i in range(7):
   tx=c.texture((self.w,self.h),4);tx.filter=(moderngl.LINEAR,moderngl.LINEAR);tx.repeat_x=False;tx.repeat_y=False
   self.ft.append(tx);self.fb.append(c.framebuffer([tx]))
  self.transitions={};self.setup_transitions()
  rng=np.random.default_rng(462)
  self.particles=rng.random((90,6))
  self.cam=(0.,0.,0.,1.);self.time=0.;self.active_shot=1;self.pose_start=0.;self.pose_end=1.;self.pose_offset=0.;self.used_keys=set()
  print('ModernGL',c.info['GL_RENDERER'],'render',self.w,self.h,flush=True)
 def set(self,program,**vals):
  for k,v in vals.items():
   if k in program:program[k].value=v
 def setup_transitions(self):
  header='''#version 330
in vec2 vuv;out vec4 frag;
uniform sampler2D fromTex;uniform sampler2D toTex;uniform float progress;uniform float ratio;
vec2 mirrored(vec2 uv){return 1.-abs(mod(uv,2.)-1.);}
vec4 getFromColor(vec2 p){return texture(fromTex,mirrored(p));}
vec4 getToColor(vec2 p){return texture(toTex,mirrored(p));}
'''
  defaults={'CrossZoom':{'strength':.48},'DreamyZoom':{'rotation':9.,'scale':1.55},'Swirl':{},'ripple':{'amplitude':90.,'speed':35.},'GlitchMemories':{},'morph':{'strength':.18},'kaleidoscope':{'speed':1.2,'angle':1.0,'power':1.5},'ButterflyWaveScrawler':{'amplitude':1.,'waves':28.,'colorSeparation':.18},'burn':{'color':(1.,.3,.05)},'crosswarp':{},'directionalwarp':{'direction':(1.,0.),'smoothness':.15}}
  for name,params in defaults.items():
   path=ROOT/'vendor'/'gl-transitions'/(name+'.glsl')
   if not path.exists():continue
   source=path.read_text().replace('texture2D(','texture(')
   if name=='Swirl':source=source.replace('8.0 * 3.14159','3.4 * 3.14159')
   p=self.ctx.program(vertex_shader=(SH/'full.vert').read_text(),fragment_shader=header+source+'\nvoid main(){frag=transition(vuv);}\n')
   self.set(p,fromTex=0,toTex=1,ratio=4/3,**params)
   self.transitions[name]=(p,self.ctx.vertex_array(p,[(self.fullbuf,'2f','in_pos')]))
  custom={
  'paper':'''vec4 transition(vec2 uv){float band=floor(uv.y*9.);float local=clamp(progress*1.65-band*.065,0.,1.);float shift=local*local*(3.-2.*local);vec2 q=uv;float dir=mod(band,2.)<.5?1.:-1.;q.x+=shift*dir;vec4 a=getFromColor(q);vec4 b=getToColor(uv-vec2((1.-shift)*dir,0.));float m=dir>0.?step(1.,q.x):step(q.x,0.);vec4 c=mix(a,b,m);float edge=abs(fract(q.x));c.rgb-=exp(-min(edge,1.-edge)*100.)*.2*sin(local*3.14159);return c;}''',
  'iris':'''vec4 transition(vec2 uv){float p=progress*progress*(3.-2.*progress);vec2 d=(uv-.5)*vec2(ratio,1.);float r=length(d);float wave=sin(atan(d.y,d.x)*9.+progress*12.)*.025*sin(progress*3.14159);float m=1.-smoothstep(p*.9-.035,p*.9+.035,r+wave);vec4 a=getFromColor((uv-.5)/(1.+p*.5)+.5);vec4 b=getToColor((uv-.5)/(.72+.28*p)+.5);vec4 c=mix(a,b,m);c.rgb+=vec3(.4,.65,.85)*exp(-abs(r-p*.9)*75.)*sin(progress*3.14159)*.45;return c;}''',
  'whip':'''vec4 transition(vec2 uv){float p=progress*progress*(3.-2.*progress);float s=sin(progress*3.14159);vec4 c=vec4(0.);for(int i=0;i<15;i++){float o=(float(i)/14.-.5)*.16*s;vec2 q=uv+vec2(p+o,0.);c+=mix(getFromColor(q),getToColor(q-vec2(1.,0.)),step(1.,q.x));}return c/15.;}'''
  }
  for name,src in custom.items():
   p=self.ctx.program(vertex_shader=(SH/'full.vert').read_text(),fragment_shader=header+src+'\nvoid main(){frag=transition(vuv);}')
   self.set(p,fromTex=0,toTex=1,ratio=4/3);self.transitions[name]=(p,self.ctx.vertex_array(p,[(self.fullbuf,'2f','in_pos')]))
 def begin(self,slot,t,cam=(720,540,1,0),mode=0,energy=1):
  self.slot=slot;self.time=t;self.cam=((cam[0]-720)/100,(540-cam[1])/100,math.radians(cam[3]),cam[2])
  self.fb[slot].use();self.ctx.viewport=(0,0,self.w,self.h);self.ctx.disable(moderngl.BLEND);self.fb[slot].clear(0,0,0,1)
  self.set(self.bg,time=t,mode=mode,energy=energy);self.bgvao.render()
  self.ctx.enable(moderngl.BLEND);self.ctx.blend_func=(moderngl.SRC_ALPHA,moderngl.ONE_MINUS_SRC_ALPHA)
 def draw(self,key,x=720,y=540,w=700,z=0,angle=0,tilt=(0,0),op=1,tint=(1,1,1),mono=0,deform=None,mask=0,reveal=1,screen=False,stretch=1):
  if op<=.0001 or w<=.1:return
  character=key.startswith('cookiya') or key.startswith('shot_')
  blend=0.
  if character:
   key=f'shot_{self.active_shot:02d}_A';key_b=f'shot_{self.active_shot:02d}_B'
   pivot=(self.pose_start+self.pose_end)/2+self.pose_offset
   blend=smooth((self.time-pivot+.045)/.09)
   self.textures[key_b].use(1)
   if blend<1:self.used_keys.add(key)
   if blend>0:self.used_keys.add(key_b)
  else:self.textures[key].use(1)
  im=self.images[key];p=self.sprite;self.textures[key].use(0)
  self.set(p,tex=0,texB=1,pose_mix=blend,pos=((x-720)/100,(540-y)/100,z),size=(w/100,w*im.height/im.width/100*stretch),rot=(math.radians(tilt[0]),math.radians(tilt[1]),math.radians(angle)),camera=(0,0,0,1) if screen else self.cam,time=self.time,deform=(.8 if character else 0.) if deform is None else deform,opacity=sat(op),tint=tint,mono=mono,maskmode=mask,reveal=reveal)
  (self.grid if character or deform else self.quad).render()
 def backdrop(self,key,t,op=1,angle=0):
  self.draw(key,720,540,2650,z=-10,angle=angle,op=op)
 def stars(self,t,n=60,speed=.5):
  for x,y,z,r,a,b in self.particles[:n]:
   depth=((z*18+t*speed)%18)-10
   self.draw('star' if r>.86 else 'glow',x*2200-380,y*1700-310,7+r*17,z=depth,angle=t*4,op=.2+.6*(.5+.5*math.sin(t*2+a*12)))
 def flying(self,t,n=12,kind='butterfly',speed=1):
  for i,(x,y,z,r,a,b) in enumerate(self.particles[:n]):
   depth=((z*20+t*speed)%20)-12
   xx=x*2100-330;yy=y*1450-185
   if 410<xx<1030 and 160<yy<760:yy-=600
   self.draw(kind,xx,yy,65+r*95,z=depth,angle=t*(8+r*16)+a*360,tilt=(math.sin(t*4+a)*25,math.sin(t*3+a)*45),op=min(1,(depth+12)/3))
 def effectpass(self,src,dst,t,effect=0,amount=0,zoomblur=0,chroma=0,bloom=0,fade=1,exposure=1):
  self.fb[dst].use();self.ctx.disable(moderngl.BLEND);self.ft[src].use(0)
  self.set(self.fx,tex=0,time=t,effect=effect,amount=amount,zoomblur=zoomblur,chroma=chroma,bloom=bloom,fade=fade,exposure=exposure);self.fxvao.render()
 def transition(self,name,p,a=2,b=3,out=4):
  pr,vao=self.transitions[name];self.fb[out].use();self.ctx.disable(moderngl.BLEND);self.ft[a].use(0);self.ft[b].use(1);self.set(pr,progress=sat(p));vao.render()
 def read(self,slot=5):return self.fb[slot].read(components=3,alignment=1)
 def image(self,slot=5):return Image.frombytes('RGB',(self.w,self.h),self.read(slot)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
