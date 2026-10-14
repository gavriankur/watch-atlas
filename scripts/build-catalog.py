"""Compile sourced reference records; preserve missing values and per-field provenance."""
import json,pathlib,re,collections
from urllib.parse import urlparse
root=pathlib.Path(__file__).resolve().parents[1]
old=json.loads((root/'data/catalog-seed-v2.json').read_text())
records={};aliases={}
def refkey(brand,ref):return brand.lower()+'-'+re.sub('[^a-z0-9]','',str(ref).lower())
def valnum(v):
 if isinstance(v,(int,float)):return float(v)
 m=re.search(r'\d+(?:\.\d+)?',str(v or ''));return float(m.group()) if m else None
mapping={'calibre':'Caliber','caliber number':'Caliber','caliber no':'Caliber','case':'Case material','material':'Case material','size case':'Case diameter (retailer listing)','case diameter':'Case diameter','diameter':'Case diameter','case width':'Case width','case material':'Case material','glass':'Crystal','glass material':'Crystal','crystal lens':'Crystal','case back':'Caseback','case thickness':'Thickness','case height':'Thickness','dial color':'Dial colour','dial colour':'Dial colour','dial':'Dial','strap material':'Strap material','band material':'Strap material','band':'Strap material','bracelet':'Bracelet','strap color':'Strap colour','strap colour':'Strap colour','band color':'Strap colour','band colour':'Strap colour','power reserve':'Power reserve','duration':'Power reserve','water resistance':'Water resistance','water resistance (m)':'Water resistance','water resistance (bar)':'Water resistance','water resistancy':'Water resistance','water resistant':'Water resistance','warranty period':'Warranty','warranty':'Warranty','buckle':'Clasp','buckle type':'Clasp','strap closure':'Clasp','band buckle':'Clasp','buckle clasp':'Clasp','lug to lug':'Lug-to-lug','lug-to-lug':'Lug-to-lug','lug width':'Lug width','band / lug width':'Lug width','band width':'Lug width','strap width':'Lug width','case shape':'Case shape','gender':'Gender','gander':'Gender','country of origin':'Country of manufacture','country of manufacture':'Country of manufacture','country':'Country of manufacture','case size (mm)':'Case diameter','case size':'Case dimensions','weight (gms)':'Weight','watch weight':'Weight','warranty years':'Warranty','strap lug width':'Lug width','watch functions':'Functions','watch movement':'Movement','band/ strap type':'Strap material','movement':'Movement','movement type':'Movement','function':'Functions','functions':'Functions','bezel colour':'Bezel colour','bezel color':'Bezel colour','case color':'Case colour','case colour':'Case colour'}
known={'Tissot','Hamilton','Rado','Fossil','Seiko','Citizen','Titan','Timex','Casio','Longines','Swatch','Rolex','Omega'}
rejected=[]
def normalize(w):
 w=dict(w);brand=w['brand'];ref=w.get('ref') or w.get('reference');id=refkey(brand,ref)
 source=w.get('source') or w.get('sourceUrl');img=w.get('image') or w.get('imageUrl');price=w.get('price',w.get('priceInr'))
 specs={}
 for k,v in w.get('specs',{}).items():
  if v is None or v=='':continue
  k=' '.join(k.split());v=' '.join(str(v).split())
  if len(k)>75 or k in ['Brand','Collection','Reference','Model No','SKU','MRP (INR)','Manufacturer description','Manufacturer technical notes','Package Includes','Net Quantity','Net quantity','Model']:continue
  key=mapping.get(k.lower(),k)
  if k=='Case' and re.search(r'\d.*mm',v,re.I):key='Case description'
  if key=='Case diameter' and k.lower()=='case size (mm)' and not re.search('[a-zA-Z]',v):v+=' mm'
  if key=='Weight' and k.lower()=='weight (gms)' and not re.search('[a-zA-Z]',v):v+=' g'
  if key=='Water resistance' and k.lower()=='water resistance (m)' and not re.search('[a-zA-Z]',v):v+=' m'
  if key not in specs or len(v)>len(specs[key]):specs[key]=v
 # Split explicitly supplied combined case dimensions rather than infer measurements.
 text=specs.get('Case Size') or specs.get('Case size') or ''
 for label,pattern in [('Case diameter',r'(?:Case\s*)?Diameter\s*:?\s*(\d+(?:\.\d+)?)\s*mm'),('Thickness',r'(?:Thickness|Height)\s*:?\s*(\d+(?:\.\d+)?)\s*mm'),('Lug-to-lug',r'Lug[ -]to[ -]lug\s*:?\s*(\d+(?:\.\d+)?)\s*mm')]:
  m=re.search(pattern,text,re.I)
  if m and label not in specs:specs[label]=m.group(1)+' mm'
 size=valnum(w.get('size')) or valnum(specs.get('Case diameter')) or valnum(specs.get('Case diameter (retailer listing)'))
 move=str(w.get('movement') or specs.get('Movement') or '').lower()
 if 'self-winding' in move or 'self winding' in move or 'self-w' in move or 'automatic' in move:movement='Automatic'
 elif 'solar' in move or 'eco-drive' in move or 'light powered' in move:movement='Solar quartz'
 elif 'kinetic' in move:movement='Kinetic'
 elif 'spring drive' in move:movement='Spring Drive'
 elif 'manual' in move or 'hand-w' in move or ('mechanical' in move and 'self' not in move):movement='Manual'
 elif 'digital' in move:movement='Digital quartz'
 elif 'quartz' in move or move in ['chronograph','multifunction','three-hand','three hand']:movement='Quartz'
 else:
  title=(str(w.get('name',''))+' '+specs.get('Movement','')).lower()
  movement='Automatic' if 'automatic' in title else 'Solar quartz' if any(x in title for x in ['solar','eco-drive']) else 'Quartz' if 'quartz' in title else 'Manual' if 'manual winding' in title or 'hand-wound' in title else 'Not stated'
 if brand=='Casio' and 'digital' in specs.get('Display','').lower() and 'analog' not in specs.get('Display','').lower() and movement!='Solar quartz':movement='Digital quartz'
 collection=str(w.get('collection') or brand).strip()
 # Collection is a family; special editions stay in the individual name.
 if brand=='Tissot':
  for family in ['Chemin Des Tourelles','Chemin des Tourelles','Classic Dream','Le Locle','Seastar','Supersport','Gentleman','PR 100','PR100','PRX','T-Race','T-Touch','Lovely','Ballade','Desir','Désir','SRV','Chrono L','Everytime','Carson','Bellissima','Couturier','Flamingo','Tradition']:
   if family.lower() in collection.lower():collection=family;break
 collectionAliases={'Bioceramic Moonswatch':'Bioceramic MoonSwatch','BIOCERAMIC MOONSWATCH':'Bioceramic MoonSwatch','Hydroconquest':'HydroConquest','The Longines Master Collection':'Master Collection','Chemin des Tourelles':'Chemin Des Tourelles','Désir':'Desir'}
 collection=collectionAliases.get(collection,collection)
 name=str(w['name']).strip();name=re.sub(r'^'+re.escape(brand)+r'\s+','',name,flags=re.I)
 if ref:name=' '.join(re.sub(r'(?<![a-zA-Z0-9])'+re.escape(str(ref))+r'(?![a-zA-Z0-9])','',name,flags=re.I).split()).strip(' -–·')
 if brand in ['Seiko','Timex','Citizen'] and ref and name.lower().endswith(str(ref).lower()):name=re.sub(r'\s*[-–·]?\s*'+re.escape(str(ref))+r'$','',name,flags=re.I).strip()
 style=w.get('style','')
 if style not in ['Dive','Dress','Sport','Everyday']:
  s=(name+' '+collection).lower();style='Dive' if any(k in s for k in ['diver','submariner','sea-dweller','deepsea','seamaster','hydroconquest','captain cook','ocean star']) else 'Sport' if any(k in s for k in ['chronograph','speedmaster','daytona','g-shock','gshock','khaki','pro trek','protrek','explorer','5 sports']) else 'Dress' if any(k in s for k in ['datejust','day-date','1908','cocktail','presage','centrix','master collection','dolcevita','classic']) else 'Everyday'
 notes=w.get('notes',[]);notes=[notes] if isinstance(notes,str) else notes
 notes=[n for n in notes if n]
 if brand=='Timex' and 'swiss-made' in source and specs.get('Country of manufacture','').lower() not in ['','switzerland','swiss']:
  specs.pop('Country of manufacture',None);notes.append('The product title says Swiss made, but a structured origin field conflicts with it. The origin field is omitted here.')
 if w.get('priceNote') and w['priceNote'] not in notes:notes.append(w['priceNote'])
 sources=w.get('sources') or [{'label':brand+' official product page','url':source}]
 if isinstance(sources,dict):sources=[sources]
 official={'Rolex':['rolex.com'],'Omega':['omegawatches.com'],'Rado':['rado.com'],'Fossil':['fossil.com','fi.revalsys.com'],'Seiko':['seikowatches.com','seikowatches.co.in'],'Casio':['casio.com','casioindiashop.com'],'Tissot':['tissotwatches.com'],'Citizen':['citizenwatches.co.in','citizenwatch.com'],'Titan':['titan.co.in'],'Timex':['timexindia.com'],'Hamilton':['hamiltonwatch.com'],'Longines':['longines.com'],'Swatch':['swatch.com']}
 host=urlparse(source).hostname or ''
 sourceType='manufacturer' if any(host==h or host.endswith('.'+h) for h in official.get(brand,[])) else 'retailer'
 record={'id':id,'brand':brand,'collection':collection,'name':name,'ref':str(ref),'price':float(price) if price is not None else None,'priceType':w.get('priceType') or 'Listed INR price','source':source,'priceSource':w.get('priceSource') or source,'image':img,'images':list(dict.fromkeys(w.get('images') or [img]))[:6],'size':size,'movement':movement,'style':style,'specs':specs,'verifiedAt':w.get('verifiedAt','2026-10-13'),'priceCheckedAt':w.get('priceCheckedAt') or ('2026-10-13' if brand=='Rado' and w.get('technicalVerifiedAt') else w.get('verifiedAt','2026-10-13')),'specCheckedAt':w.get('technicalVerifiedAt') or w.get('verifiedAt','2026-10-13'),'notes':notes,'sources':sources,'sourceType':sourceType}
 if brand not in known or not ref or not source or not img or len(specs)<6:
  rejected.append({'brand':brand,'ref':ref,'reason':'Missing provenance/photo/reference or fewer than 6 documented fields'});return None
 if size is not None and (size<12 or size>80):rejected.append({'brand':brand,'ref':ref,'reason':'Implausible case measurement'});return None
 return record
for w in old:
 n=normalize(w)
 if n:records[n['id']]=n
for f in sorted((root/'data/imports').glob('*.json')):
 for w in json.loads(f.read_text()):
  n=normalize(w)
  if n:records[n['id']]=n
# Merge global Seiko family names that are explicitly the same reference in the India catalog.
for id,w in list(records.items()):
 if w['brand']=='Seiko' and len(w['ref'])==6:
  matches=[x for x in records.values() if x['brand']=='Seiko' and x['ref'].startswith(w['ref']) and x['ref'][6:] in ['K1','J1','P1']]
  if len(matches)==1:
   matches[0].setdefault('legacyIds',[]).append(id);del records[id]
# Keep primary photos already optimized locally across reproducible builds.
assets=json.loads((root/'data/photo-map.json').read_text()) if (root/'data/photo-map.json').exists() else {}
for id,w in records.items():
 if id in assets and (root/'dist'/assets[id]['path']).exists():w['image']=assets[id]['path'];w['images'][0]=w['image']
# Round-robin brands to make the first screen useful, rather than dominated by the largest feed.
order=['Rolex','Omega','Rado','Fossil','Seiko','Casio','Tissot','Citizen','Titan','Timex','Hamilton','Longines','Swatch'];groups={b:[] for b in order}
for w in records.values():groups[w['brand']].append(w)
result=[]
for i in range(max(map(len,groups.values()))):
 for brand in order:
  if i<len(groups[brand]):result.append(groups[brand][i])
(root/'dist/catalog.js').write_text('const watches = '+json.dumps(result,ensure_ascii=False,separators=(',',':'))+';')
summary={'checkedAt':max(w['verifiedAt'] for w in result),'references':len(result),'brands':{b:len(ws) for b,ws in groups.items()},'priced':sum(w['price'] is not None for w in result),'manufacturerSourced':sum(w['sourceType']=='manufacturer' for w in result),'minimumSpecFields':min(len(w['specs']) for w in result),'rejected':rejected}
(root/'data/import-report.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
