import urllib.request,gzip,re,json,pathlib,concurrent.futures
ROOT=pathlib.Path(__file__).parent/'references'
def get(u):
 r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.bilibili.com/'}),timeout=50)
 b=r.read();return gzip.decompress(b) if b[:2]==b'\x1f\x8b' else b
def run(item):
 name,bv=item
 b=get('https://www.bilibili.com/video/'+bv+'/').decode();(ROOT/(name+'.html')).write_text(b)
 for key in ['__INITIAL_STATE__','__playinfo__']:
  m=re.search(r'window\.'+key+r'\s*=\s*',b)
  if m:
   d=json.JSONDecoder().raw_decode(b[m.end():])[0];(ROOT/(name+'_'+key+'.json')).write_text(json.dumps(d,ensure_ascii=False))
   if key=='__INITIAL_STATE__':print(name,'metadata',json.dumps({k:d.get('videoData',{}).get(k) for k in ['title','bvid','cid','duration','pic','desc']},ensure_ascii=False),flush=True)
   else: print(name,'playinfo',list(d.keys()),'quality',d.get('data',{}).get('quality'),'dash',bool(d.get('data',{}).get('dash')),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:list(ex.map(run,[('model','BV1JNZ6BsEo6'),('reference','BV1tcK861EyE')]))
