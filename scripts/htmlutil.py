from html.parser import HTMLParser

class Element:
 def __init__(self,tag='root',attrs=None):self.tag=tag;self.attrs=dict(attrs or []);self.children=[]
 def text(self):return ' '.join(' '.join(c.text() if isinstance(c,Element) else c for c in self.children).split())
 def all(self,pred):
  r=[self] if pred(self) else []
  for c in self.children:
   if isinstance(c,Element):r+=c.all(pred)
  return r
class DOM(HTMLParser):
 def __init__(self,s):
  super().__init__(convert_charrefs=True);self.root=Element();self.stack=[self.root];self.feed(s)
 def handle_starttag(self,tag,attrs):
  e=Element(tag,attrs);self.stack[-1].children.append(e)
  if tag not in ['area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr']:self.stack.append(e)
 def handle_endtag(self,tag):
  for i in range(len(self.stack)-1,0,-1):
   if self.stack[i].tag==tag:self.stack=self.stack[:i];break
 def handle_data(self,s):self.stack[-1].children.append(s)
