"""Offline parity check against inspected local source; never imports API clients."""
import ast,base64,contextlib,hashlib,io,json,re,sys
from pathlib import Path
from typing import Any,Optional,Union
from types import SimpleNamespace
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import benchmark as b

def extract(path,names,namespace):
 nodes=[n for n in ast.parse(path.read_text()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
 for n in nodes:n.decorator_list=[]
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),namespace)

def main(source,data):
 # Substitute only original file decoder dependency; original encode_image executes unchanged.
 # This validates RGB PNG decoding via Pillow, not imageio package/runtime equivalence.
 def imread(path,pilmode):
  p=Path(path)
  if not p.is_absolute():p=data/str(p).split('data/SPACE_data_release/',1)[1]
  with Image.open(p) as im:return np.array(im.convert(pilmode))
 ns={'np':np,'Image':Image,'BytesIO':io.BytesIO,'base64':base64,'Optional':Optional,
     'imageio':SimpleNamespace(imread=imread)}
 extract(source/'space/utils/common.py',{'encode_image','get_image_as_message'},ns)
 captured=[]
 class Agent:
  model_name='gpt-compat';image_detail='low'
  def reset(self):pass
  def get_prediction(self,content,answer):captured.append(content);return None
  def get_eval_cost(self):return {}
 env={'Any':Any,'get_agent':lambda *a:Agent(),'get_image_as_message':ns['get_image_as_message']}
 extract(source/'space/evaluate_qas.py',{'evaluate_on_qa'},env)
 cfg=json.loads((ROOT/'config.json').read_text());n=0;imgn=0
 modes=set()
 for cat in cfg['categories']:
  for qa in json.loads((data/cat/'qas.json').read_text()):
   env['evaluate_on_qa']('QA_Agent',{},qa)
   official=captured.pop()
   adapted=b.content_for(qa['question'],data,cfg['image_detail'])
   mapped=[{'type':'input_text','text':x} if isinstance(x,str) else
           {'type':'input_image','image_url':x['image_url']['url'],'detail':x['image_url']['detail']} for x in official]
   assert mapped==adapted,(cat,n)
   for q in qa['question']:
    if q.startswith('IMAGE:'):
     with Image.open(b.image_path(q,data)) as im:modes.add(im.mode)
     imgn+=1
   n+=1
 pns={'Any':Any,'Union':Union,'json':json,'re':re}
 extract(source/'space/agents/qa_agent.py',{'is_int','QA_Agent'},pns)
 parser=object.__new__(pns['QA_Agent'])
 examples=['2','{"answer":2}','{"answer":"2"}','{"choice":2}','{"answer":1} {"answer":2}',
           '{"answer":true}','{"answer":null}','{"answer":[]}','{"answer":2.9}','{"answer":5}',
           '{bad}','{"answer":{"x":2}}','```json\n{"answer": 3}\n```','{}','{"a":1,"b":2}']
 for text in examples:
  with contextlib.redirect_stdout(io.StringIO()):
   try:expected=(parser.parse_answer_from_response(text),None)
   except Exception as e:expected=(None,type(e).__name__)
  assert expected==b.upstream_prediction(text),(text,expected,b.upstream_prediction(text))
 report={'date':'2026-11-19','records_compared':n,'image_occurrences_compared':imgn,'image_modes':sorted(modes),
         'text_order_and_jpeg_payload_parity':True,'parser_cases_compared':len(examples),'real_api_calls':0,
         'limits':'Original evaluate/encode/parser source executed. Original imageio RGB decoding substituted by Pillow RGB decoding. No live API/SDK test or original imageio environment reproduction.',
         'source_hashes':{str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [source/'space/evaluate_qas.py',source/'space/agents/qa_agent.py',source/'space/utils/common.py']}}
 (ROOT/'audit/parity_results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main(Path(sys.argv[1]),Path(sys.argv[2]))
