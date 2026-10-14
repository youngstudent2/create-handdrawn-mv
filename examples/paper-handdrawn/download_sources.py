import urllib.request,gzip,json,pathlib,concurrent.futures,subprocess
ROOT=pathlib.Path(__file__).parent/'references'
def get(u):
 r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.bilibili.com/'}),timeout=60)
 b=r.read();return gzip.decompress(b) if b[:2]==b'\x1f\x8b' else b
def run(name):
 d=json.loads((ROOT/(name+'___INITIAL_STATE__.json')).read_text())['videoData'];bv=d['bvid'];cid=d['cid']
 p=json.loads(get(f'https://api.bilibili.com/x/player/playurl?bvid={bv}&cid={cid}&qn=64&fnval=1&fourk=0'))
 (ROOT/(name+'_play.json')).write_text(json.dumps(p));print(name,'playurl',p.get('code'),list(p.get('data',{})),flush=True)
 if p.get('data',{}).get('durl'):
  u=p['data']['durl'][0]['url'];b=get(u);(ROOT/(name+'.mp4')).write_bytes(b);print(name,'downloaded',len(b),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:list(ex.map(run,['model','reference']))
