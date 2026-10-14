"""Cookiya / Sweet Reverie v3 — 38 independent character keyframes.

python v3/render_v3.py --width 1440 --fps 30
python v3/render_v3.py --width 720 --samples
"""
import argparse,bisect,json,math,subprocess,time
from pathlib import Path
from PIL import Image,ImageDraw
from compositor import Compositor,sat,ease,smooth,mix
import moderngl
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'output';OUT.mkdir(exist_ok=True)
TAU=math.tau
CUTS=[0,1.382,2.786,4.191,5.596,7.233,8.882,10.286,11.796,13.56,15.441,16.614,18.483,20.12,22.001,23.87,25.728,27.133,28.537,30]
NAMES=['The eye opens','A stolen wink','Paper memories','Reach into the dream','Through the frames','Cookie theatre','The liquid eye','Underwater fall','Botanical kaleidoscope','Falling echoes','Signal / wink','Unfolding paper','Starlight flight','Five-world match cuts','Recursive reverie','Take my hand','Shutter portraits','The final orbit','Cookiya']
TRANS=[('CrossZoom',.48),('paper',.46),('DreamyZoom',.42),('Swirl',.50),('whip',.42),('ripple',.56),('iris',.50),('morph',.38),('ButterflyWaveScrawler',.46),('GlitchMemories',.26),('paper',.40),('CrossZoom',.44),('directionalwarp',.38),('DreamyZoom',.42),('Swirl',.48),('burn',.40),('CrossZoom',.44),('iris',.48)]

class Film:
 def __init__(self,width,allow_partial=False):self.r=Compositor(width,allow_partial)
 def framed(self,key,x,y,w,angle=0,z=0,tilt=(0,0),op=1,paper=False):
  r=self.r
  r.draw(key,x,y,w*.88,z=z,angle=angle,tilt=tilt,op=op,mask=1,deform=.55)
  r.draw('paperframe' if paper else 'frame',x,y,w,z=z+.01,angle=angle,tilt=tilt,op=op)
 def orbit(self,t,n=8,radius=630,cy=540,w=110,z=-1):
  r=self.r
  for i in range(n):
   a=t*.38+i*TAU/n;x=720+math.cos(a)*radius;y=cy+math.sin(a)*radius*.64
   r.draw(['cookie','daisy','butterfly','clock'][i%4],x,y,w*(1+.16*math.sin(a)),z=z+math.sin(a)*2,angle=-a*180/math.pi,tilt=(10*math.sin(a),25*math.cos(a)))
 def flowerburst(self,t,u,cx=720,cy=540,n=15):
  r=self.r;p=ease(u)
  for i in range(n):
   a=i*TAU/n+.23;radius=140+p*(490+(i%3)*90)
   r.draw(['daisy','chip0','chip1','butterfly','chip3'][i%5],cx+math.cos(a)*radius,cy+math.sin(a)*radius*.73,60+70*p,z=-2+(i%4)*1.3,angle=i*41+t*(20 if i%2 else -30),tilt=(t*13,i*24+t*18),op=smooth(u*5))
 def scene(self,idx,t,slot):
  r=self.r;start,end=CUTS[idx:idx+2];v=(t-start)/(end-start);u=sat(v);s=t-start;h=math.sin;co=math.cos
  r.active_shot=idx+1;r.pose_start=start;r.pose_end=end;r.pose_offset=0.
  fx=dict(effect=0,amount=0,zoomblur=0,chroma=.0004,bloom=.15,exposure=1.0)
  if idx==0:
   r.begin(slot,t,cam=(720+30*h(s*2),540,mix(.92,1.34,ease(u)),mix(-7,3,u)),mode=0)
   r.backdrop('cosmos_bg',t)
   r.draw('sigil',w=1110,angle=s*22,op=.65)
   r.draw('eye',720,510,1150,z=-2,op=.4,angle=-5)
   r.draw('cookiya_portrait',720,820,870,angle=-3+6*u,deform=.65)
   r.draw('ribbon',720,1060,1150,z=2,angle=-5+s*7,op=smooth(s/.3))
   r.stars(t,48,2.2);self.orbit(t,6,670,540,95,-3)
   fx.update(zoomblur=.015*ease(u),chroma=.001*u)
  elif idx==1:
   r.begin(slot,t,cam=(720+45*h(s),520,1+.12*u,3-8*u),mode=0);r.backdrop('cosmos_bg',t)
   r.draw('sigil',w=1200,angle=-s*22,op=.55)
   self.orbit(t,9,770,540,150,-3)
   self.framed('cookiya_wink',720,560,720+100*ease(u),angle=5-10*u)
   r.draw('ribbon',720,900,820,z=2,angle=-7+6*h(s*2))
   r.draw('butterfly',mix(1350,30,u),90+60*h(s*3),135,z=4,tilt=(0,55*h(s*8)),angle=25-60*u)
   r.stars(t,44,1.1)
  elif idx==2:
   r.begin(slot,t,cam=(720+80*h(s*2),540,1.02,4*h(s*2)),mode=1)
   r.backdrop('theatre_bg',t,op=.30)
   for i,(x,key) in enumerate([(240,'cookiya_portrait'),(720,'cookiya_wink'),(1200,'cookiya_portrait')]):
    q=smooth((u-i*.10)/.48);ry=mix(83,0,q);a=[15,-8,-16][i]+h(s*2+i)*4
    r.pose_offset=(i-1)*.08
    self.framed(key,x,540+65*h(s*2+i),440+(i==1)*85,a,z=-1+(i==1),tilt=(8*h(s+i),ry),paper=True)
   r.pose_offset=0.
   r.draw('ribbon',720,1080,1700,z=3,angle=7+s*4)
   for j in range(6):r.draw('daisy',100+j*270,80 if j%2 else 1050,100,angle=t*20+j*35)
  elif idx==3:
   r.begin(slot,t,cam=(mix(860,700,ease(u)),mix(640,500,ease(u)),mix(.94,1.09,u),mix(-10,7,u)),mode=2)
   r.backdrop('dream_bg',t,op=.75)
   r.draw('sigil',720,570,1200,angle=s*38,op=.6)
   self.flowerburst(t,u,n=19)
   r.draw('cookiya_reach',720,530+40*h(s*2),mix(700,1100,ease(u)),z=mix(-2,1,u),angle=12-21*u,deform=1.1)
   r.draw('ribbon',-50+250*u,1000,900,z=5,angle=55)
   fx.update(zoomblur=.012*(1-u),bloom=.35)
  elif idx==4:
   r.begin(slot,t,cam=(720+65*h(s*1.7),540+30*co(s*2),1,-9+20*u),mode=4,energy=1.2)
   r.backdrop('cosmos_bg',t,op=.55)
   for j in range(8):
    phase=(j/8+u*.30)%1;z=-20+phase*32
    r.draw('frame',720,540,480,z=z,angle=(1-phase)*-45+s*15,tilt=(8*co(j),12*h(j+s)),op=min(1,(1-phase)*5))
   r.draw('cookiya_float',720+120*h(s*1.7),530,460+130*u,z=1,angle=-14+26*u,deform=1.3)
   r.flying(t,10,'chip0',8);r.stars(t,65,6)
   fx.update(zoomblur=.022,chroma=.0015)
  elif idx==5:
   r.begin(slot,t,cam=(720+120*h(s*1.5),560-45*u,1.1+u*.13,-4+7*u),mode=1)
   r.backdrop('theatre_bg',t)
   r.draw('cloud',370,240,760,z=-4,angle=5)
   r.draw('clock',1130,370,250,z=-1,angle=-s*28)
   r.draw('ribbon',740,630,1000,z=-1,angle=-22+15*u)
   r.draw('cookiya_float',660+160*u,570+95*h(s*2.6),470,z=1.2,angle=15*h(s*2),deform=1.3)
   r.draw('cloud',180,960,610,z=4,angle=-9)
   r.draw('cookie',1270-100*u,980,280,z=3,angle=s*24)
   r.flying(t,6,'butterfly',1.4)
  elif idx==6:
   r.begin(slot,t,cam=(720,540,1+u*.12,4*h(s*2)),mode=0)
   r.backdrop('dream_bg',t)
   r.draw('sigil',w=1200,angle=-s*38)
   r.draw('eye',550,505,1050,angle=6*h(s),stretch=1-.13*h(s*3))
   r.draw('cookiya_fall',1030-70*u,650,540,z=.2,angle=-4+8*u,deform=.8)
   r.draw('ribbon',720,920,1250,angle=s*14)
   r.flying(t,9,'daisy',3)
   fx.update(effect=5,amount=.3+.7*u,chroma=.001,bloom=.35)
  elif idx==7:
   r.begin(slot,t,cam=(720+100*h(s),500+110*u,1.10,-14+30*u),mode=3)
   r.backdrop('dream_bg',t)
   for i,(x,y,z,rr,aa,b) in enumerate(r.particles[:23]):
    r.draw('bubble',x*1800-180,(y*1700-s*190)%1700-280,30+rr*150,z=-5+z*10,angle=i*19)
   for j in range(3,0,-1):r.draw('cookiya_fall',720-j*70,450+u*250-j*90,650,z=-j*.6,angle=-19+u*32-j*9,op=.10/j,tint=(.48,.75,1.))
   r.draw('cookiya_fall',720+55*h(s*2),450+u*250,650,z=0,angle=-19+u*32,deform=1.6)
   r.draw('daisy',130,960,450,z=4,angle=s*16);r.draw('butterfly',1270,200+180*u,250,z=3,tilt=(0,50*h(s*7)))
   fx.update(effect=1,amount=.7,bloom=.25)
  elif idx==8:
   r.begin(slot,t,cam=(720,540,.98+u*.07,s*18),mode=0);r.backdrop('cosmos_bg',t)
   for ring in range(2):
    for j in range(8):
     a=j*TAU/8+s*(.38 if ring else -.35);rad=330+ring*260
     r.draw('daisy' if ring else 'eye',720+co(a)*rad,540+h(a)*rad,240 if ring else 175,z=-1,angle=-a*180/math.pi+90,tilt=(0,15*h(s*3+j)))
   r.draw('sigil',w=550,angle=-s*60)
   # The mandala is refracted first; the character is added afterwards for a readable gesture.
   fx.update(effect=2,amount=1,chroma=.0012)
  elif idx==9:
   r.begin(slot,t,cam=(720+130*h(s*1.2),540,1,12-23*u),mode=4);r.backdrop('cosmos_bg',t,op=.65)
   for j in range(7):
    z=-10+j*1.5;yy=((j*240+s*(170+j*26))%1900)-400;xx=190+j*175+70*h(s*2+j)
    r.draw('cookiya_fall',xx,yy,210+j*45,z=z,angle=j*27-70+s*(15+j*3),op=.35+j*.08,deform=1.4)
   r.draw('cookiya_float',760-100*u,480+u*190,520,angle=-20+u*34,z=2,deform=1.4)
   r.flying(t,13,'butterfly',5);r.stars(t,65,5)
   fx.update(chroma=.0013,zoomblur=.012)
  elif idx==10:
   r.begin(slot,t,cam=(720+35*h(s*18),490,1.14,2*h(s*15)),mode=2)
   r.backdrop('cosmos_bg',t,op=.6)
   r.draw('sigil',w=1150,angle=s*60,op=.5)
   # Close crop deliberately extends the cutout boundaries outside the picture.
   r.draw('cookiya_wink',760,860,1240,z=0,angle=-4+h(s*5)*3,mono=1-smooth(u*2))
   r.draw('sweet',720,140,1150,op=.8,screen=True)
   r.draw('ribbon',140,880,800,z=3,angle=70)
   r.draw('cookie',1300,900,250,z=2,angle=s*80)
   fx.update(effect=4,amount=.65+.3*h(s*28),chroma=.008*(1-u)+.001,bloom=.25)
  elif idx==11:
   r.begin(slot,t,cam=(720,540,1.02,-7+14*u),mode=1);r.backdrop('theatre_bg',t,op=.4)
   r.draw('sigil',w=1240,angle=s*18,tint=(.52,.29,.21),op=.75)
   r.draw('ribbon',720,800,1250,angle=20-30*u)
   ry=70*(1-ease(u*1.8))
   r.draw('cookiya_reach',720,530,1080,z=0,angle=7-14*u,tilt=(10*h(s),ry),mask=2,reveal=.1+.95*ease(u*2),deform=1.1)
   self.flowerburst(t,u,n=14)
   r.draw('cloud',110,1030,650,z=4);r.draw('cloud',1350,70,700,z=3,angle=180)
   fx.update(bloom=.20)
  elif idx==12:
   r.begin(slot,t,cam=(720+60*h(s*2),500+70*u,1.03,-6+10*u),mode=4,energy=2)
   r.backdrop('cosmos_bg',t,op=.60)
   r.draw('sigil',w=1500,angle=s*40,op=.35)
   r.flying(t,20,'cookie',11)
   r.draw('cookiya_float',620+200*u,500+40*h(s*3),890+100*u,z=1,angle=12-24*u,deform=1.3)
   r.draw('ribbon',720,1120,1300,z=1,angle=-s*15)
   r.stars(t,85,12)
   fx.update(zoomblur=.012,chroma=.0020,bloom=.35)
  elif idx==13:
   # Beat-spaced matched silhouette; environments and camera direction jump every 0.469s.
   k=int(max(0,s)/.469)%5;q=(max(0,s)/.469)%1
   cams=[-8,12,-14,9,0];r.begin(slot,t,cam=(720,540,1+q*.07,cams[k]),mode=[1,0,3,2,4][k])
   if k in (0,3):r.backdrop('theatre_bg',t,op=.8)
   elif k in (1,4):r.backdrop('cosmos_bg',t)
   else:r.backdrop('dream_bg',t)
   r.draw('sigil',w=1000,angle=s*45,op=.8)
   self.orbit(t+k,10,660,540,160,-1)
   r.draw('cookiya_fall',720,540+q*50,660,z=0,angle=-13+s*10,deform=1.5)
   r.draw('ribbon',720,1080,1300,z=3,angle=12)
   fx.update(effect=4,amount=.8*(1-smooth(q/.13)),zoomblur=.018,chroma=.004*(1-q))
  elif idx==14:
   r.begin(slot,t,cam=(720,540,1.02,-6+12*u),mode=0);r.backdrop('cosmos_bg',t)
   # Repeated nested frames are independent depth planes, not one flat zoomed image.
   for j in range(7):
    ww=1260*(.70**j)*(1+u*.3);a=(-1)**j*(8+j*3)+s*12
    r.draw('frame',720,540,ww,z=0,angle=a,op=1)
   # The main portrait sits on top of the recursive frame tunnel in post_scene.
   r.flying(t,8,'butterfly',3)
   fx.update(effect=3,amount=.14+.24*smooth(u),zoomblur=.009,chroma=.001)
  elif idx==15:
   r.begin(slot,t,cam=(mix(680,760,u),540,mix(.99,1.12,ease(u)),-6+12*u),mode=2)
   r.backdrop('dream_bg',t,op=.80)
   r.draw('sigil',w=1300,angle=-s*25,op=.8)
   self.flowerburst(t,u,n=20)
   for j in range(3,0,-1):r.draw('cookiya_reach',720-j*25,555+j*15,940-j*70,z=-j*.4,angle=-7+j*3,op=.12/j,tint=(1,.57,.64))
   r.draw('cookiya_reach',720,530-25*h(s*2),1000+130*ease(u),angle=-7+11*u,deform=1.15)
   r.draw('daisy',100,1080,420,z=4,angle=s*30);r.draw('ribbon',1350,250,800,z=4,angle=80)
   fx.update(bloom=.45,chroma=.0013)
  elif idx==16:
   r.begin(slot,t,cam=(720,540,1,0),mode=0);r.backdrop('theatre_bg',t,op=.6)
   for j in [0,1,3,4,2]:
    x=(j-2)*350+720;rot=60*(1-ease((u-j*.035)/.30))+4*h(s*2+j)
    r.pose_offset=(j-2)*.055
    self.framed('cookiya_wink' if j%2==0 else 'cookiya_portrait',x,540+45*h(s*4+j),500 if j==2 else 350,angle=-8+4*j,z=.5 if j==2 else -1,tilt=(0,rot),paper=True)
   r.pose_offset=0.
   r.draw('sweet',720,155,1100,screen=True)
   r.draw('reverie',720,960,1180,screen=True)
   r.flying(t,11,'chip2',5)
   fx.update(chroma=.002)
  elif idx==17:
   r.begin(slot,t,cam=(720,540,mix(1.23,.94,ease(u)),-12+18*u),mode=0);r.backdrop('cosmos_bg',t)
   r.draw('sigil',w=1290,angle=s*25)
   self.orbit(t,12,640,540,135,-1)
   r.draw('ribbon',720,540,1280,z=-1,angle=-s*13)
   r.draw('cookiya_float',720,515+22*h(s*3),460+70*u,z=1,angle=-8+16*u,deform=1)
   r.stars(t,80,2.5)
   r.draw('daisy',130,1020,400,z=3,angle=-s*17)
   r.draw('butterfly',1310,170,300,z=3,tilt=(0,35*h(s*6)))
   fx.update(bloom=.35)
  else:
   r.begin(slot,t,cam=(720,540,1+.03*u,2-2*u),mode=0);r.backdrop('cosmos_bg',t)
   r.draw('sigil',720,460,1170,angle=t*8,op=.6)
   r.draw('ribbon',720,480,1120,angle=-3+3*u)
   self.framed('cookiya_wink',720,400,440+15*u,angle=-3+3*u)
   r.draw('cookie',220,500,170,angle=t*11);r.draw('clock',1200,500,170,angle=-t*11)
   r.draw('title',720,825,1060,screen=True)
   r.draw('subtitle',720,925,440,screen=True)
   r.stars(t,45,.5)
   fx.update(bloom=.3)
  return fx
 def post_scene(self,idx,t,src,dst,fx):
  r=self.r;r.effectpass(src,dst,t,**fx)
  if idx in (8,14):
   r.fb[dst].use();r.ctx.enable(moderngl.BLEND);r.ctx.blend_func=(moderngl.SRC_ALPHA,moderngl.ONE_MINUS_SRC_ALPHA)
   s=t-CUTS[idx]
   self.framed('cookiya_portrait',720,540,490 if idx==8 else 500,angle=-s*18 if idx==8 else -s*10)
 def frame(self,t):
  r=self.r;idx=min(len(CUTS)-2,max(0,bisect.bisect_right(CUTS,t)-1));transition=None
  for j,(name,duration) in enumerate(TRANS):
   boundary=CUTS[j+1]
   if boundary-duration/2<=t<boundary+duration/2:transition=(j,name,(t-boundary+duration/2)/duration);break
  if transition:
   j,name,p=transition
   a=self.scene(j,t,0);self.post_scene(j,t,0,2,a)
   b=self.scene(j+1,t,1);self.post_scene(j+1,t,1,3,b)
   r.transition(name,p);src=4
  else:
   a=self.scene(idx,t,0);self.post_scene(idx,t,0,2,a);src=2
  # Continuous film finish. No full-white strobe; only small beat-locked breathing in the highlights.
  pulse=math.exp(-((t%(.469))/.047)**2)
  fade=smooth(t/.14)*(1-smooth((t-29.38)/.62))
  r.effectpass(src,5,t,bloom=.10,chroma=.0003,exposure=1.0+pulse*.012,fade=fade)
  return r

def samples(film):
 ts=[(a+b)/2 for a,b in zip(CUTS[:-1],CUTS[1:])]
 thumbs=[]
 for i,t in enumerate(ts):
  im=film.frame(t).image();im.save(OUT/f'shot_{i:02d}.jpg',quality=94);im.thumbnail((360,270));thumbs.append((t,im))
 sheet=Image.new('RGB',(360*4,300*5),(18,20,27));d=ImageDraw.Draw(sheet)
 for i,(t,im) in enumerate(thumbs):
  x=i%4*360;y=i//4*300;sheet.paste(im,(x,y));d.text((x+8,y+276),f'{i+1:02d}  {t:.2f}s  {NAMES[i]}',fill=(240,225,208))
 sheet.save(OUT/'storyboard_v3.jpg',quality=94)
 # Three successive frames around six different transition types.
 checks=[0,1,3,5,9,15];sheet=Image.new('RGB',(360*3,294*len(checks)),(18,20,27));d=ImageDraw.Draw(sheet)
 for row,j in enumerate(checks):
  name,duration=TRANS[j]
  for col,p in enumerate([.2,.5,.8]):
   t=CUTS[j+1]+(p-.5)*duration;im=film.frame(t).image();im.thumbnail((360,270));sheet.paste(im,(col*360,row*294));d.text((col*360+8,row*294+275),f'{name} {p:.1f}',fill='white')
 sheet.save(OUT/'transitions_v3.jpg',quality=93)
 film.frame(29.35).image().save(OUT/'Cookiya_Sweet_Reverie_Cover_v3.jpg',quality=95)
 print('SAMPLES_READY',flush=True)

def render(film,fps,width,output):
 h=width*3//4;music=ROOT.parent/'assets'/'music.m4a';n=round(30*fps)
 cmd=['ffmpeg','-y','-hide_banner','-loglevel','warning','-f','rawvideo','-pix_fmt','rgb24','-s',f'{width}x{h}','-r',str(fps),'-i','-','-i',str(music),'-map','0:v','-map','1:a','-vf','vflip','-c:v','libx264','-preset','medium','-crf','18' if width>=1440 else '20','-pix_fmt','yuv420p','-c:a','aac','-b:a','256k','-t','30','-movflags','+faststart','-metadata','title=Cookiya — Sweet Reverie / 38 Keyframes Edition',str(output)]
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE);start=time.monotonic()
 try:
  for k in range(n):
   film.frame(k/fps);p.stdin.write(film.r.read())
   if k%60==0:print(f'{k}/{n} frames, {time.monotonic()-start:.1f}s',flush=True)
  p.stdin.close();code=p.wait()
  if code:raise RuntimeError(f'ffmpeg returned {code}')
 except BaseException:p.kill();raise
 audit={'expected_count':38,'used_count':len(film.r.used_keys),'used_keyframes':sorted(film.r.used_keys)}
 (OUT/'render_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
 assert len(film.r.used_keys)==38, audit
 print('RENDERED',output,round(time.monotonic()-start,1),'38/38 keyframes used',flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--width',type=int,default=1440);p.add_argument('--fps',type=int,default=30);p.add_argument('--samples',action='store_true');p.add_argument('--output');args=p.parse_args()
 f=Film(args.width)
 if args.samples:samples(f)
 else:render(f,args.fps,args.width,Path(args.output) if args.output else OUT/'Cookiya_Sweet_Reverie_30s_v3.mp4')
