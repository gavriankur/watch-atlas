"""Stop deployment if the compiled catalog loses records, sources, or primary photos."""
import datetime,json,pathlib
from PIL import Image
r=pathlib.Path(__file__).resolve().parents[1]
items=json.loads((r/'dist/catalog.js').read_text().removeprefix('const watches = ').rstrip(';'))
assert not json.loads((r/'data/import-report.json').read_text())['rejected'],'Compiler rejected source records'
assert len(items)>=1244,'Catalog unexpectedly shrank'
assert len({w['id'] for w in items})==len(items),'Duplicate model IDs'
for w in items:
 assert w['ref'] and len(w['specs'])>=6,w['id']
 assert w['price'] is None or 100<=w['price']<=100000000,w['id']
 for field in ('source','priceSource'):
  assert w[field].startswith('https://') and not any(x in w[field] for x in ('fi.revalsys.com','fnfsale.in')),w['id']
 for field in ('priceCheckedAt','specCheckedAt'):datetime.date.fromisoformat(w[field])
 path=(r/'dist'/w['image']).resolve()
 assert path.is_relative_to((r/'dist/photos-v3').resolve()) and path.is_file(),w['id']
 with Image.open(path) as im:im.verify()
print('Validated',len(items),'references and primary photographs')
