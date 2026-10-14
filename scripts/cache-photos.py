"""Fetch public product photographs and cache compressed, aspect-preserving WebP previews."""
import pathlib,json,concurrent.futures,subprocess,io,time,struct
from urllib.parse import quote
from PIL import Image,ImageOps
r=pathlib.Path(__file__).resolve().parents[1];items=json.loads((r/'dist/catalog.js').read_text().removeprefix('const watches = ').rstrip(';'));out=r/'dist/photos-v3';out.mkdir(exist_ok=True)
mapfile=r/'data/photo-map.json';mapping=json.loads(mapfile.read_text()) if mapfile.exists() else {};fail=[]
def photo(w):
 id=w['id'];dst=out/(id+'.webp');local='photos-v3/'+dst.name
 if id in mapping and (r/'dist'/mapping[id]['path']).exists():return id,mapping[id],None
 if dst.exists():return id,{'path':local,'source':w['image']},None
 source=w['image'];data=None;error='unknown'
 for url in list(dict.fromkeys([source]+w['images'][:2])):
  if url.startswith('photos'):
   p=r/'dist'/url
   if p.exists():data=p.read_bytes()
   else:continue
  else:
   # These public image transformations request smaller versions of the same photograph.
   url=url.replace('c_limit%2Cw_1920','c_limit%2Cw_650')
   if 'cdn.shopify.com' in url:url+=('&' if '?' in url else '?')+'width=700'
   if 'api.ecom.longines.com' in url:url=url.split('?')[0]+'?w=650'
   try:
    url=quote(url,safe=":/?&=%+,$;@!~*()")
    proc=subprocess.run(['curl','-4','-L','--fail','--silent','--show-error','--connect-timeout','8','--max-time','22','--max-filesize','20000000',url],capture_output=True,timeout=25)
    if proc.returncode:raise ValueError(proc.stderr.decode()[:180])
    data=proc.stdout
   except Exception as e:error=str(e);continue
  try:
   if data[:8]==b'\x89PNG\r\n\x1a\n':
    chunks=[data[:8]];pos=8
    while pos+12<=len(data):
     length=struct.unpack('>I',data[pos:pos+4])[0];kind=data[pos+4:pos+8];end=pos+12+length
     if end>len(data):break
     if kind not in [b'tEXt',b'zTXt',b'iTXt']:chunks.append(data[pos:end])
     pos=end
    data=b''.join(chunks)
   im=Image.open(io.BytesIO(data));im.load();im=ImageOps.exif_transpose(im);im.thumbnail((650,650),Image.Resampling.LANCZOS)
   if im.mode not in ['RGB','RGBA']:im=im.convert('RGBA' if 'transparency' in im.info else 'RGB')
   im.save(dst,'WEBP',quality=83,method=4)
   return id,{'path':local,'source':source,'width':im.width,'height':im.height},None
  except Exception as e:error=str(e)
 return id,None,error
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
 for i,(id,entry,error) in enumerate(pool.map(photo,items)):
  if entry:mapping[id]=entry
  else:fail.append({'id':id,'error':error})
  if (i+1)%50==0:
   mapfile.write_text(json.dumps(mapping,indent=2));print('Processed',i+1,'/',len(items),'cached',len(mapping),'failed',len(fail),flush=True)
mapfile.write_text(json.dumps(mapping,indent=2));(r/'data/photo-errors.json').write_text(json.dumps(fail,indent=2));print('COMPLETE',len(mapping),'cached;',len(fail),'primary download failures',flush=True)
