"""Package only the final 38 keyframes, runtime and referenced backgrounds."""
from pathlib import Path
import zipfile,json
from check_assets import inspect
from render_v3 import CUTS,NAMES,TRANS
ROOT=Path(__file__).resolve().parent;PROJECT=ROOT.parent;OUT=ROOT/'output'

def package():
 audit=inspect(require_complete=True)
 rendered=json.loads((OUT/'render_audit.json').read_text());assert rendered['used_count']==38
 meta_source=ROOT/'production_v3.json' if (ROOT/'production_v3.json').exists() else PROJECT/'production.json'
 m=json.loads(meta_source.read_text())
 m.update(version=3,title='Cookiya — Sweet Reverie / 38 Keyframes Edition',unique_character_keyframes=38,character_keyframes_per_shot=2,render_command='python v3/render_v3.py --width 1440 --fps 30',animation='Nineteen shot-specific A/B pose pairs (38 separately generated transparent illustrations), ~90 ms pose changes, mesh hair motion, 3D paper planes, 18 GLSL transitions, eye melt, background kaleidoscope, foreground parallax and nested frames. Two-keyframe cutout animation, not frame-by-frame animation.',shots=[{'start':a,'end':b,'scene':n,'keyframes':[f'shot_{i+1:02d}_A.png',f'shot_{i+1:02d}_B.png'],'pose_change_time':(a+b)/2} for i,(a,b,n) in enumerate(zip(CUTS[:-1],CUTS[1:],NAMES))],transitions=[{'center':CUTS[i+1],'type':n,'duration':d} for i,(n,d) in enumerate(TRANS)],dependencies=['Python 3','ModernGL','glcontext','Pillow','NumPy','SciPy','FFmpeg with libx264','OpenGL 3.3+ EGL'],generated_art='Built-in GPT Image; each shot has its own newly generated A and B pose. See v3/assets/prompts_*.json for exact calls.',shader_source='https://github.com/gl-transitions/gl-transitions (MIT)')
 (ROOT/'production_v3.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
 dest=OUT/'Cookiya_38_Keyframes_Project_v3.zip'
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
  prefix='Cookiya_38_Keyframes/'
  z.write(ROOT/'README.md',prefix+'README.md')
  for p in sorted((ROOT/'assets').glob('shot_*.png')):z.write(p,prefix+'v3/assets/'+p.name)
  for p in sorted((ROOT/'assets').glob('prompts_*.json')):z.write(p,prefix+'v3/assets/'+p.name)
  for p in ROOT.rglob('*'):
   if not p.is_file() or 'assets' in p.relative_to(ROOT).parts or 'output' in p.relative_to(ROOT).parts or '__pycache__' in p.parts:continue
   if p.suffix in ['.py','.vert','.frag','.glsl','.json','.txt','.md'] or p.name=='LICENSE':z.write(p,prefix+'v3/'+str(p.relative_to(ROOT)))
  for n in ['cosmos_bg.png','dream_bg.png','theatre_bg.png','props_atlas.png','props_atlas_v2.png','music.m4a','prompts_backgrounds.json','prompts_props.json','prompts_theatre.json','prompts_props_v2.json']:
   p=PROJECT/'assets'/n;z.write(p,prefix+'assets/'+n)
  for n in ['cover.jpg','fullbody.jpg','outfit.jpg']:
   p=PROJECT/'references'/n
   if p.exists():z.write(p,prefix+'references/'+n)
  for n in ['asset_audit.json','render_audit.json','Cookiya_38_Keyframes_Overview.jpg']:
   p=OUT/n;z.write(p,prefix+'v3/output/'+n)
 print(dest,dest.stat().st_size,flush=True)

if __name__=='__main__':package()
