"""Conservative weekly public-source refresh. No estimated prices or inferred specs."""
import concurrent.futures, datetime, html, io, json, pathlib, re, subprocess, threading
from html.parser import HTMLParser
from urllib.parse import urlparse
ROOT = pathlib.Path(__file__).resolve().parents[1]
TODAY = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
BLOCKED = ('fi.revalsys.com', 'fnfsale.in')
FEEDS = [
 ('Seiko', 'https://seikowatches.co.in', '/products.json'),
 ('Timex', 'https://shop.timexindia.com', '/products.json'),
 ('Titan', 'https://gangaramwatchgallery.com', '/products.json'),
 ('Fossil', 'https://zimsonwatches.com', '/collections/fossil/products.json'),
 ('Omega', 'https://zimsonwatches.com', '/collections/omega/products.json'),
]
locks = {}; lock = threading.Lock()
def key(s): return re.sub('[^a-z0-9]', '', str(s).lower())
def fetch(url):
 if any(x in urlparse(url).netloc for x in BLOCKED): raise ValueError('Untrusted source')
 with lock: sem = locks.setdefault(urlparse(url).netloc, threading.Semaphore(2))
 with sem:
  p = subprocess.run(['curl','-4','-L','--fail','--silent','--show-error','--connect-timeout','8','--max-time','25','--retry','1','--retry-max-time','30','--max-filesize','12000000',url],capture_output=True,timeout=60)
 if p.returncode: raise ValueError('Source unavailable (curl %s)' % p.returncode)
 return p.stdout.decode('utf-8')
def clean(s): return ' '.join(html.unescape(re.sub('<[^>]+>', ' ', str(s))).split())
def json_blocks(page):
 for s in re.findall(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',page,re.S|re.I):
  try: yield json.loads(s)
  except (ValueError,TypeError): continue
def objects(obj):
 if isinstance(obj,list):
  for x in obj: yield from objects(x)
 elif isinstance(obj,dict):
  yield obj
  for k in ('@graph','mainEntity','itemListElement','item'): yield from objects(obj.get(k))
def price_for(page, ref):
 """Only exact-reference Product offers in INR; ignore unrelated recommendations."""
 for block in json_blocks(page):
  for p in objects(block):
   typ=p.get('@type',[]);typ=[typ] if isinstance(typ,str) else typ
   if 'Product' not in typ: continue
   identity=[p.get(x,'') for x in ('sku','mpn','model','productID')]
   if key(ref) not in [key(x) for x in identity]: continue
   offers=p.get('offers',[]);offers=[offers] if isinstance(offers,dict) else offers
   values=set()
   for o in offers:
    if o.get('priceCurrency')!='INR': continue
    try:
     value=float(str(o.get('price','')).replace(',',''))
     if value>0: values.add(value)
    except ValueError: pass
   if len(values)==1: return values.pop()
 return None
def rado_price(page,ref):
 title=re.search(r'<title[^>]*>(.*?)</title>',page,re.S|re.I)
 if not title or not re.search(r'(?<![A-Za-z0-9])'+re.escape(ref)+r'(?![A-Za-z0-9])',clean(title.group(1)),re.I): return None
 currencies=re.findall(r'<meta[^>]*itemprop="priceCurrency"\s+content="([^"]+)"',page,re.I)
 values=re.findall(r'<meta[^>]*itemprop="price"\s+content="([^"]+)"',page,re.I)
 if currencies==['INR'] and len(values)==1:
  try:return float(values[0])
  except ValueError:pass
 return None
def safe_price(old,new):
 return isinstance(new,(int,float)) and 100 <= new <= 100000000 and (not old or .5 <= new/old <= 1.5)
def read_catalog(): return json.loads((ROOT/'dist/catalog.js').read_text().removeprefix('const watches = ').rstrip(';'))
def specs_from_html(body):
 specs={}
 # Source-provided two-column specification tables / Zimson definition rows.
 pairs=re.findall(r'<tr\b[^>]*>\s*<t[dh][^>]*>(.*?)</t[dh]>\s*<td[^>]*>(.*?)</td>',body,re.S|re.I)
 pairs+=re.findall(r'<li class="table_header_z[^"]*">(.*?)</li>\s*<li class="table_para_z">(.*?)</li>',body,re.S)
 pairs+=re.findall(r'<dt\b[^>]*>(.*?)</dt>\s*<dd\b[^>]*>(.*?)</dd>',body,re.S|re.I)
 for k,v in pairs:
  k,v=clean(k).strip(' :'),clean(v)
  if 1<len(k)<65 and 0<len(v)<400 and k.lower() not in ('brand','model','model no','sku','collection','reference'): specs[k]=v
 for block in json_blocks(body):
  for product in objects(block):
   if product.get('@type')!='Product': continue
   for prop in product.get('additionalProperty',[]):
    if isinstance(prop,dict) and prop.get('name') and prop.get('value'):
     k,v=clean(prop['name']),clean(prop['value'])
     if len(k)<65 and len(v)<400: specs[k]=v
 return specs
def cache_photo(id,url):
 from PIL import Image, ImageOps
 if not url.startswith('https://') or any(x in url for x in BLOCKED): raise ValueError('Invalid photograph source')
 p=subprocess.run(['curl','-4','-L','--fail','--silent','--connect-timeout','8','--max-time','25','--max-filesize','15000000',url],capture_output=True,timeout=30)
 if p.returncode: raise ValueError('Photograph unavailable')
 im=ImageOps.exif_transpose(Image.open(io.BytesIO(p.stdout)));im.thumbnail((650,650))
 if im.mode not in ('RGB','RGBA'): im=im.convert('RGB')
 path='photos-v3/'+id+'.webp';im.save(ROOT/'dist'/path,'WEBP',quality=83)
 return {'path':path,'source':url,'width':im.width,'height':im.height}
def discover_official(brand,known,photos):
 from htmlutil import DOM,Element
 host='https://www.'+('tissotwatches.com' if brand=='Tissot' else 'hamiltonwatch.com')
 paths=['/en-in/collection.html'] if brand=='Tissot' else ['/en-in/collection/'+x+'.html' for x in ('khaki-field','jazzmaster','khaki-navy','ventura','american-classic','khaki-aviation')]
 urls=[]
 for path in paths:
  page=fetch(host+path)
  pattern=r'data-product-tile-link="[^"]+" href="([^"]+)"' if brand=='Tissot' else r'href="(/en-in/h\d+[^"?#]+\.html)"'
  urls.extend(host+x if x.startswith('/') else x for x in re.findall(pattern,page,re.I))
 new=[];attempts=0
 for url in dict.fromkeys(urls):
  if len(new)>=12 or attempts>=30: break
  urlref=url.rsplit('/',1)[-1].split('.')[0].split('-')[0]
  if (brand,key(urlref)) in known: continue
  attempts+=1
  try:
   page=fetch(url);products=[p for b in json_blocks(page) for p in objects(b) if p.get('@type')=='Product']
   if len(products)!=1: continue
   product=products[0];ref=str(product.get('sku') or '')
   if not ref or (brand,key(ref)) in known: continue
   if key(ref)!=key(urlref): continue
   if re.search(r'Pocket|Savonnette|Lepine|Pendant|Strap',product['name'],re.I): continue
   price=price_for(page,ref)
   if not safe_price(None,price): continue
   dom=DOM(page).root;specs={}
   if brand=='Tissot':
    for e in dom.all(lambda e:'ti-pdp-details-content' in e.attrs.get('class','')):
     children=[c for c in e.children if isinstance(c,Element)]
     if len(children)>=2:
      k,v=children[0].text(),children[1].text()
      if k and v and len(k)<65 and len(v)<400 and not any(x in k.lower() for x in ('manufacturer','importer','packer')):
       specs[k]=v+(' mm' if '(mm)' in k else ' g' if k=='Weight (g)' else ' hours' if k=='Power reserve (hours)' else '')
   else:
    for e in dom.all(lambda e:e.tag=='li'):
     labels=e.all(lambda e:'attribute-label' in e.attrs.get('class',''))
     values=e.all(lambda e:'attribute-value' in e.attrs.get('class',''))
     if len(labels)==len(values)==1: specs[labels[0].text()]=values[0].text()
   specs={({'Case Width (mm)':'Case diameter','CaseThickness (mm)':'Thickness','Case Water resistance':'Water resistance'}.get(k,k)):v for k,v in specs.items() if v and k.lower() not in ('reference','sku','collection','strap reference','status')}
   if len(specs)<8: continue
   images=product.get('image',[]);images=[images] if isinstance(images,str) else images
   if not images and brand=='Tissot':images=[e.attrs['src'] for e in dom.all(lambda e:e.tag=='img' and 'product-pictures' in e.attrs.get('src',''))]
   images=[i.get('url') if isinstance(i,dict) else i for i in images]
   if not images:continue
   id=brand.lower()+'-'+key(ref);photos[id]=cache_photo(id,images[0])
   new.append({'brand':brand,'name':product['name'],'ref':ref,'collection':specs.get('Collection',brand),'price':price,'priceType':'Official India listed INR price','source':url,'priceSource':url,'image':images[0],'images':images[:6],'specs':specs,'verifiedAt':TODAY})
  except Exception: continue
 return new
def main():
 from PIL import Image
 catalog=read_catalog();byref={(w['brand'],key(w['ref'])):w for w in catalog}
 overrides_path=ROOT/'data/refresh-overrides.json'
 overrides=json.loads(overrides_path.read_text()) if overrides_path.exists() else {}
 discovered_path=ROOT/'data/imports/zz-discovered.json'
 discovered=json.loads(discovered_path.read_text()) if discovered_path.exists() else []
 photos=json.loads((ROOT/'data/photo-map.json').read_text())
 report={'checkedAt':TODAY,'schedule':'Sundays 06:00 Asia/Kolkata','checked':0,'changed':0,'added':0,'sources':[],'unavailable':[],'quarantined':[]}
 observed={};new=[]
 for brand,host,path in FEEDS:
  count=0; attempted=0
  print('Checking feed:',brand,flush=True)
  try:
   products=[]
   for page in range(1,21):
    batch=json.loads(fetch(host+path+'?limit=250&page='+str(page)))['products']
    products.extend(batch)
    if len(batch)<250: break
   else: raise ValueError('Feed pagination limit exceeded; snapshot discarded')
   for p in products:
    if brand.lower() not in p.get('vendor','').lower(): continue
    for v in p.get('variants',[]):
     ref=str(v.get('sku') or '').strip()
     if not ref: continue
     try: price=float(v['price'])
     except (ValueError,TypeError,KeyError): continue
     source=host+'/products/'+p['handle'];existing=byref.get((brand,key(ref)))
     # These India-only stores publish variant prices in rupees.
     if existing:
      # Do not silently substitute a different retailer for the recorded price source.
      if urlparse(existing['priceSource']).netloc==urlparse(host).netloc:
       observed[existing['id']]=(price,source);count+=1
      continue
     # New records require variant-specific fields and a verified primary photo.
     # Multi-variant pages can mix size/dial specs, so omit those from discovery.
     if len(p['variants'])!=1 or brand=='Omega': continue
     if len([x for x in new if x['brand']==brand])>=12 or attempted>=30: continue
     if re.search(r'\b(strap|bracelet only|replacement band|clock)\b',p['title'],re.I): continue
     attempted+=1
     specs=specs_from_html(p.get('body_html',''))
     if len(specs)<8:
      try: specs.update(specs_from_html(fetch(source)))
      except Exception: continue
     if len(specs)<8 or not safe_price(None,price): continue
     image=(p.get('images') or [{}])[0].get('src')
     if not image: continue
     id=brand.lower()+'-'+key(ref)
     try: photos[id]=cache_photo(id,image)
     except Exception: continue
     new.append({'id':id,'brand':brand,'ref':ref,'name':p['title'],'collection':p.get('product_type') or brand,'source':source,'priceSource':source,'price':price,'priceType':'Listed INR price','image':image,'images':[image],'specs':specs,'verifiedAt':TODAY,'notes':['Discovered from the exact-reference India product listing.']})
   report['sources'].append({'brand':brand,'feed':host+path,'products':len(products),'pricesMatched':count})
  except Exception as e: report['sources'].append({'brand':brand,'error':str(e)})
 for brand in ('Tissot','Hamilton'):
  print('Checking new official models:',brand,flush=True)
  try:
   additions=discover_official(brand,byref,photos);new.extend(additions)
   report['sources'].append({'brand':brand,'newModels':len(additions)})
  except Exception as e:report['sources'].append({'brand':brand,'error':str(e)})
 # All remaining references are checked against their recorded price source.
 def check(w):
  try:
   page=fetch(w['priceSource']);price=price_for(page,w['ref'])
   if price is None and urlparse(w['priceSource']).hostname in ('www.rado.com','rado.com'):
    price=rado_price(page,w['ref'])
   if price is None: raise ValueError('No exact-reference INR offer in supported markup')
   return w['id'],price,None
  except Exception as e: return w['id'],None,str(e)
 pending=[w for w in catalog if w['id'] not in observed]
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  for index,(id,price,error) in enumerate(pool.map(check,pending)):
   if index%100==0: print('Product pages checked:',index,'/',len(pending),flush=True)
   if error: report['unavailable'].append({'id':id,'reason':error})
   else: observed[id]=(price,next(w['priceSource'] for w in catalog if w['id']==id))
 history=[]
 for w in catalog:
  if w['id'] not in observed: continue
  price,source=observed[w['id']]
  if not safe_price(w['price'],price):
   report['quarantined'].append({'id':w['id'],'previous':w['price'],'observed':price});continue
  report['checked']+=1
  overrides[w['id']]={'price':price,'priceSource':source,'priceCheckedAt':TODAY}
  if w['price']!=price:
   report['changed']+=1;history.append({'id':w['id'],'date':TODAY,'previous':w['price'],'price':price,'source':source})
 report['added']=len(new)
 # A broken source layout must not silently publish an almost-unchecked snapshot.
 report['success']=report['checked']>=max(1,len(catalog)//4)
 (ROOT/'data/refresh-report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k not in ('unavailable','quarantined','sources')},indent=2))
 if not report['success']: raise SystemExit('Fewer than 25% of references checked. Keeping the published catalog unchanged.')
 overrides_path.write_text(json.dumps(overrides,indent=2)+'\n')
 discovered_path.write_text(json.dumps(discovered+new,indent=2)+'\n')
 (ROOT/'data/photo-map.json').write_text(json.dumps(photos,indent=2)+'\n')
 if history:
  with (ROOT/'data/price-history.jsonl').open('a') as f:
   for row in history: f.write(json.dumps(row)+'\n')
 (ROOT/'dist/update-status.json').write_text(json.dumps({k:v for k,v in report.items() if k not in ('unavailable','quarantined')},indent=2)+'\n')
if __name__=='__main__': main()
