import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
import benchmark as b
class ReviewTests(unittest.TestCase):
 def test_official_primary_strict_secondary(self):
  for text,gold in [('{"answer":"2"}',2),('{"choice":3}',3),('{"answer":1} {"answer":4}',4),('{"answer":true}',1)]:
   self.assertEqual(b.upstream_prediction(text),(gold,None))
   self.assertIsNone(b.parse_answer(text)[0])
 def test_parser_exception_is_visible(self):
  self.assertEqual(b.upstream_prediction('{"answer": []}'),([],None))
 def test_interrupted_request_not_resent(self):
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp);b.write_json(out/'requests/x.json',{})
   with patch('urllib.request.urlopen') as network:
    self.assertEqual(b.call_one({'item_id':'x'},Path(tmp),{},out),'unresolved_prior_attempt_not_resubmitted')
    network.assert_not_called()
 def test_failed_request_not_resent(self):
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp);b.write_json(out/'raw/x.json',{'http_status':429})
   with patch('urllib.request.urlopen') as network:
    self.assertEqual(b.call_one({'item_id':'x'},Path(tmp),{},out),'already_logged');network.assert_not_called()
 def test_no_answer_key_in_actual_network_body(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);cfg=json.loads((b.HERE/'config.json').read_text());cfg['model_snapshot']='mock'
   class Reply:
    status=200;headers={}
    def __enter__(self):return self
    def __exit__(self,*a):pass
    def read(self):return b'{"status":"completed","output":[]}'
   with patch.dict('os.environ',{'OPENAI_API_KEY':'TEST_ONLY'}),patch('urllib.request.urlopen',return_value=Reply()) as network:
    b.call_one({'item_id':'q','category':'PTT_vision','question':['Question with four choices']},root,cfg,root/'out')
    req=network.call_args.args[0];payload=json.loads(req.data)
    self.assertEqual(payload['input'][0]['content'],[{'type':'input_text','text':'Question with four choices'}])
    self.assertNotIn('answer',payload);self.assertNotIn('TEST_ONLY',(root/'out/requests/q.json').read_text())
 def test_primary_denominator_includes_unparseable_completed(self):
  with tempfile.TemporaryDirectory() as tmp:
   home=Path(tmp);root=home/'data';(root/'PTT_vision').mkdir(parents=True)
   (root/'PTT_vision/qas.json').write_text(json.dumps([{'question':['q'],'answer':2}]*2))
   _,_,files=b.load_pool(root,['PTT_vision']);out=home/'runs/test'
   ids=['PTT_vision-00000','PTT_vision-00001']
   b.write_json(out/'metadata.json',{'source_files':files,'config':{'categories':['PTT_vision']},'item_ids':ids})
   for ident,text in zip(ids,['{"answer":"2"}','no answer']):
    response={'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':text}]}]}
    b.write_json(out/'raw'/f'{ident}.json',{'http_status':200,'response_text':json.dumps(response)})
   with patch.object(b,'HERE',home):b.score(root,{},'test')
   result=json.loads((out/'summary.json').read_text())['PTT_vision']
   self.assertEqual(result['upstream_accuracy_full_pool'],0.5)
   self.assertEqual(result['n_valid'],0)
