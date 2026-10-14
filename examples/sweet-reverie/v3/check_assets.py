"""Inspect pose deliverables and produce paired art / motion contact sheets."""
from pathlib import Path
import argparse,json,hashlib
from PIL import Image,ImageDraw,ImageFont,ImageChops
ROOT=Path(__file__).resolve().parent

def inspect(require_complete=False):
 plan=json.loads((ROOT/'shot_plan.json').read_text());report=[];present=[]
 for shot in plan:
  for variant in ['A','B']:
   p=ROOT/'assets'/f"shot_{shot['shot']:02d}_{variant}.png"
   if not p.exists():
    report.append({'file':p.name,'status':'missing'});continue
   im=Image.open(p);im.load();alpha=im.getchannel('A') if im.mode=='RGBA' else None
   extrema=alpha.getextrema() if alpha else None
   rec={'file':p.name,'status':'ok' if extrema and extrema[0]==0 and extrema[1]>250 else 'bad_alpha','size':im.size,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'alpha_extrema':extrema,'bounds':alpha.getbbox() if alpha else None}
   report.append(rec);present.append((shot,variant,p))
 hashes=[r['sha256'] for r in report if 'sha256' in r]
 result={'expected':38,'present':len(present),'unique':len(set(hashes)),'complete':len(present)==38 and len(set(hashes))==38 and all(r['status']=='ok' for r in report),'assets':report}
 (ROOT/'output'/'asset_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 if require_complete:assert result['complete'],result
 print(json.dumps({k:v for k,v in result.items() if k!='assets'},ensure_ascii=False),flush=True)
 # One pair per tile, four pairs per row; no missing asset is represented as finished.
 cw,ch=650,510;sheet=Image.new('RGB',(cw*4,ch*5),(18,23,32));d=ImageDraw.Draw(sheet)
 fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';font=ImageFont.truetype(fontpath,24);small=ImageFont.truetype(fontpath,18)
 for index,shot in enumerate(plan):
  x=index%4*cw;y=index//4*ch
  d.rounded_rectangle((x+8,y+8,x+cw-8,y+ch-8),radius=18,fill=(27,34,44),outline=(61,71,86),width=2)
  d.text((x+22,y+20),f"{shot['shot']:02d}   A  →  B",font=font,fill=(244,221,190))
  for col,v in enumerate(['A','B']):
   p=ROOT/'assets'/f"shot_{shot['shot']:02d}_{v}.png"
   if not p.exists():continue
   im=Image.open(p).convert('RGBA');im=im.crop(im.getchannel('A').getbbox());im.thumbnail((290,398),Image.Resampling.LANCZOS)
   xx=x+20+col*315+(290-im.width)//2;yy=y+76+(398-im.height)//2;sheet.paste(im,(xx,yy),im)
 sheet.save(ROOT/'output'/'Cookiya_38_Keyframes_Overview.jpg',quality=95)
 return result

def motion(only_ready=False,width=720):
 from render_v3 import Film,CUTS
 film=Film(width,allow_partial=only_ready);cw,ch=720,564;sheet=Image.new('RGB',(cw*2,ch*10),(18,23,32));d=ImageDraw.Draw(sheet)
 for idx,(a,b) in enumerate(zip(CUTS[:-1],CUTS[1:])):
  if not all((ROOT/'assets'/f'shot_{idx+1:02d}_{v}.png').exists() for v in ['A','B']):continue
  x=idx%2*cw;y=idx//2*ch
  for j,f in enumerate([.27,.73]):
   t=a+(b-a)*f;fx=film.scene(idx,t,0);film.post_scene(idx,t,0,2,fx);film.r.effectpass(2,5,t,exposure=1)
   im=film.r.image();im.thumbnail((360,270));sheet.paste(im,(x+j*360,y))
   d.text((x+j*360+10,y+276),f'{idx+1:02d} / {"A" if j==0 else "B"} / {t:.2f}s',fill='white')
  # Extra row samples near the switch to review alignment rather than only static poses.
  for j,f in enumerate([.46,.54]):
   t=a+(b-a)*f;fx=film.scene(idx,t,0);film.post_scene(idx,t,0,2,fx);film.r.effectpass(2,5,t,exposure=1)
   im=film.r.image();im.thumbnail((360,270));sheet.paste(im,(x+j*360,y+294))
 sheet.save(ROOT/'output'/'all_pairs_motion_check.jpg',quality=93)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--complete',action='store_true');p.add_argument('--motion',action='store_true');a=p.parse_args();inspect(a.complete)
 if a.motion:motion(only_ready=not a.complete)
