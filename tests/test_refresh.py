import importlib.util,json,pathlib,unittest
spec=importlib.util.spec_from_file_location('refresh',pathlib.Path(__file__).parents[1]/'scripts/refresh-catalog.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class RefreshTests(unittest.TestCase):
 def page(self,p):return '<script type="application/ld+json">'+json.dumps(p)+'</script>'
 def product(self,**kw):return dict({'@type':'Product','sku':'ABC-123','offers':{'priceCurrency':'INR','price':'12995'}},**kw)
 def test_exact_reference(self):self.assertEqual(m.price_for(self.page(self.product()),'ABC123'),12995)
 def test_other_model_ignored(self):self.assertIsNone(m.price_for(self.page(self.product()),'ABC124'))
 def test_currency_not_assumed(self):self.assertIsNone(m.price_for(self.page(self.product(offers={'priceCurrency':'USD','price':200})),'ABC123'))
 def test_missing_currency(self):self.assertIsNone(m.price_for(self.page(self.product(offers={'price':200})),'ABC123'))
 def test_conflicting_offers(self):self.assertIsNone(m.price_for(self.page(self.product(offers=[{'priceCurrency':'INR','price':1000},{'priceCurrency':'INR','price':2000}])),'ABC123'))
 def test_invalid_prices(self):
  for price in (0,-1,99,float('nan'),float('inf')):self.assertFalse(m.safe_price(10000,price))
 def test_price_jump(self):
  self.assertFalse(m.safe_price(10000,20000));self.assertFalse(m.safe_price(10000,1000));self.assertTrue(m.safe_price(10000,11000))
 def test_specs(self):self.assertEqual(m.specs_from_html('<table><tr><td>Crystal</td><td>Sapphire</td></tr></table>'),{'Crystal':'Sapphire'})
 def test_rado_exact_title(self):
  page='<title>Watch R123 | Rado India</title><meta itemprop="price" content="10000"><meta itemprop="priceCurrency"\n content="INR">'
  self.assertEqual(m.rado_price(page,'R123'),10000)
  self.assertIsNone(m.rado_price(page,'R124'))
 def test_rado_ambiguous(self):
  page='<title>R123</title><meta itemprop="priceCurrency" content="INR"><meta itemprop="price" content="10000"><meta itemprop="price" content="20000">'
  self.assertIsNone(m.rado_price(page,'R123'))
if __name__=='__main__':unittest.main()
