"""Draft independent SPACE QA adapter. No network calls in audit or tests.
Not a verified reproduction of the upstream loader. See docs/UPSTREAM.md.
"""
import argparse
import base64
import concurrent.futures
import csv
import hashlib
import json
import mimetypes
import os
import platform
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENDPOINT = 'https://api.openai.com/v1/responses'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()

def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(path)

def image_path(marker, root):
    prefix = 'IMAGE:data/SPACE_data_release/'
    if not marker.startswith(prefix):
        raise ValueError('Unsupported image marker; inspect upstream format')
    p = (root / marker[len(prefix):]).resolve()
    if root.resolve() not in p.parents or not p.is_file():
        raise ValueError('Image missing or outside dataset root: ' + marker)
    return p

def load_pool(root, categories):
    """Split model inputs and scoring keys immediately at the loader boundary."""
    inputs, keys, files = [], {}, []
    for cat in categories:
        path = root / cat / 'qas.json'
        raw = path.read_bytes()
        records = json.loads(raw)
        files.append({'category': cat, 'records': len(records), 'qas_sha256': digest(raw)})
        for i, record in enumerate(records):
            q, answer = record['question'], record['answer']
            if not isinstance(q, list) or not all(isinstance(s, str) for s in q):
                raise ValueError('Unsupported question schema')
            if type(answer) is not int or answer not in (1, 2, 3, 4):
                raise ValueError('Unsupported answer')
            item_id = f'{cat}-{i:05d}'
            # Never pass the original record, its answer, or its task field to the request builder.
            inputs.append({'item_id': item_id, 'category': cat, 'question': list(q)})
            keys[item_id] = answer
    return inputs, keys, files

def content_for(question, root, detail):
    content = []
    for part in question:
        if part.startswith('IMAGE:'):
            p = image_path(part, root)
            mime = mimetypes.guess_type(p.name)[0]
            if mime not in ('image/png', 'image/jpeg', 'image/webp', 'image/gif'):
                raise ValueError('Unsupported image type')
            url = f'data:{mime};base64,' + base64.b64encode(p.read_bytes()).decode('ascii')
            content.append({'type': 'input_image', 'image_url': url, 'detail': detail})
        else:
            content.append({'type': 'input_text', 'text': part})
    return content

def build_body(question, root, config):
    # Allowlist: the question alone crosses this interface. No gold-answer argument exists.
    body = {'model': config['model_snapshot'],
            'input': [{'role': 'user', 'content': content_for(question, root, config['image_detail'])}],
            'store': False}
    if config['reasoning_effort'] is not None:
        body['reasoning'] = {'effort': config['reasoning_effort']}
    if config['max_output_tokens'] is not None:
        body['max_output_tokens'] = config['max_output_tokens']
    return body

def parse_answer(text):
    """Allow surrounding reasoning/fences; reject conflicting/malformed answer objects."""
    decoder = json.JSONDecoder()
    candidates = []
    for match in re.finditer(r'\{', text):
        try:
            obj, _ = decoder.raw_decode(text[match.start():])
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and 'answer' in obj:
            candidates.append(obj['answer'])
    if not candidates:
        return None, 'no_json_answer'
    if any(type(v) is not int or v not in (1, 2, 3, 4) for v in candidates):
        return None, 'invalid_answer_value'
    if len(set(candidates)) != 1:
        return None, 'conflicting_answers'
    return candidates[0], 'valid'

def output_text(response):
    return '\n'.join(part.get('text', '') for item in response.get('output', [])
                     if item.get('type') == 'message'
                     for part in item.get('content', []) if part.get('type') == 'output_text')

def audit(root, cfg):
    inputs, _, files = load_pool(root, cfg['categories'])
    rows, seen, dup = [], {}, 0
    for item in inputs:
        img_hashes = [digest(image_path(x, root).read_bytes()) for x in item['question'] if x.startswith('IMAGE:')]
        signature = digest(canonical({'question': item['question'], 'images': img_hashes}))
        duplicate_of = seen.get(signature, '')
        dup += bool(duplicate_of)
        seen.setdefault(signature, item['item_id'])
        rows.append({'item_id': item['item_id'], 'category': item['category'],
                     'question_sha256': digest(canonical(item['question'])),
                     'image_sha256': ';'.join(img_hashes), 'exact_duplicate_of': duplicate_of})
    out = HERE / 'manifests' / 'items.csv'
    with out.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    write_json(HERE / 'manifests' / 'inventory.json', {'source_files': files, 'total_records': len(rows),
               'exact_duplicate_records': dup, 'note': 'All source records retained. Hash checks do not identify option permutations or all shared-layout families.'})
    # Local-only request preview, not an uploadable benchmark or a public prompt dump.
    preview = build_body(inputs[0]['question'], root, cfg)
    for part in preview['input'][0]['content']:
        if part['type'] == 'input_image':
            part['image_url'] = '[image bytes omitted from preview]'
    write_json(HERE / 'local' / 'request_preview.json', preview)
    print(json.dumps({'records': len(rows), 'exact_duplicate_records': dup, 'network_requests': 0}))

def git_commit():
    p = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=HERE, capture_output=True, text=True)
    if p.returncode:
        raise ValueError('Commit this repository before a live run.')
    status = subprocess.run(['git', 'status', '--porcelain'], cwd=HERE, capture_output=True, text=True, check=True)
    if status.stdout.strip():
        raise ValueError('Working tree has uncommitted changes; commit first.')
    return p.stdout.strip()

def validate_live(cfg):
    if not cfg['model_settings_verified'] or not cfg['upstream_implementation_checked']:
        raise ValueError('Draft blocked: verify model settings and upstream implementation first.')
    if not cfg['upstream_commit'] or not re.fullmatch(r'[0-9a-f]{40}', cfg['upstream_commit']):
        raise ValueError('Record the actual 40-character upstream commit.')
    if not cfg['model_snapshot'] or not re.search(r'\d{4}-\d{2}-\d{2}', cfg['model_snapshot']):
        raise ValueError('A verified dated model snapshot is required; do not invent an ID.')
    if type(cfg['max_output_tokens']) is not int or cfg['max_output_tokens'] <= 0:
        raise ValueError('Verify and specify an adequate output-token limit.')
    if cfg['status'] != 'ready':
        raise ValueError('Config status must be ready after review.')
    if not os.environ.get('OPENAI_API_KEY'):
        raise ValueError('Set OPENAI_API_KEY locally; never place it in config.json.')

def call_one(item, root, cfg, out):
    dest = out / 'raw' / (item['item_id'] + '.json')
    if dest.exists():
        return 'already_logged' # Failures are also preserved; no silent retries.
    if (out / 'requests' / (item['item_id'] + '.json')).exists():
        return 'unresolved_prior_attempt_not_resubmitted'
    body = build_body(item['question'], root, cfg)
    request_hash = digest(canonical(body))
    # Immutable per-item request archived locally, without headers or credentials.
    write_json(out / 'requests' / (item['item_id'] + '.json'), body)
    record = {'item_id': item['item_id'], 'category': item['category'], 'request_sha256': request_hash,
              'started_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    req = urllib.request.Request(ENDPOINT, data=canonical(body), method='POST',
          headers={'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY'], 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=cfg['timeout_seconds']) as result:
            raw = result.read().decode('utf-8')
            record.update(http_status=result.status, response_text=raw, request_id=result.headers.get('x-request-id'))
    except urllib.error.HTTPError as err:
        record.update(http_status=err.code, response_text=err.read().decode('utf-8', errors='replace'))
    except (urllib.error.URLError, TimeoutError) as err:
        record.update(http_status=None, transport_error=type(err).__name__)
    write_json(dest, record)
    return 'logged'

def run(root, cfg, args):
    validate_live(cfg)
    commit = git_commit()
    inputs, _, files = load_pool(root, cfg['categories'])
    if args.phase == 'technical':
        inputs = [x for cat in cfg['categories'] for x in [y for y in inputs if y['category'] == cat][:2]]
    elif args.phase == 'repeat':
        if not args.candidate_ids or args.repeat_number not in (2,3,4,5):
            raise ValueError('Repeat phase requires frozen candidate IDs and repeat number 2–5.')
        ids = json.loads(Path(args.candidate_ids).read_text())
        if not isinstance(ids, list) or len(ids) != len(set(ids)) or not set(ids) <= {x['item_id'] for x in inputs}:
            raise ValueError('Invalid candidate IDs')
        inputs = [x for x in inputs if x['item_id'] in set(ids)]
    out = HERE / 'runs' / args.run_id
    meta = {'phase': args.phase, 'repeat_number': args.repeat_number, 'config': cfg, 'git_commit': commit,
            'python': platform.python_version(), 'platform': platform.platform(), 'source_files': files,
            'item_ids': [x['item_id'] for x in inputs],
            'input_content_sha256': digest(canonical([(x['item_id'], digest(canonical(build_body(x['question'],root,cfg)))) for x in inputs]))}
    path = out / 'metadata.json'
    if path.exists():
        if json.loads(path.read_text()) != meta:
            raise ValueError('Run identity changed. Do not resume with changed config, code or dataset.')
    else:
        write_json(path, meta)
    with concurrent.futures.ThreadPoolExecutor(max_workers=cfg['concurrency']) as pool:
        futures = [pool.submit(call_one, x, root, cfg, out) for x in inputs]
        for i, f in enumerate(concurrent.futures.as_completed(futures), 1):
            print(i, len(inputs), f.result(), flush=True)

def score(root, cfg, run_id):
    out = HERE / 'runs' / run_id
    meta = json.loads((out/'metadata.json').read_text())
    _, keys, files = load_pool(root, meta['config']['categories'])
    if files != meta['source_files']:
        raise ValueError('Source files changed since run')
    rows=[]
    for item_id in meta['item_ids']:
        path=out/'raw'/(item_id+'.json'); answer=None; status='missing'
        if path.exists():
            r=json.loads(path.read_text());status='request_error'
            if r.get('http_status') == 200:
                try:
                    response=json.loads(r['response_text'])
                    status='incomplete_response'
                    if response.get('status') == 'completed':
                        answer,status=parse_answer(output_text(response))
                except (json.JSONDecodeError,TypeError):
                    status='malformed_response'
        rows.append({'item_id':item_id,'category':item_id.rsplit('-',1)[0], 'parsed_answer':answer,
                     'gold_answer':keys[item_id],'status':status,
                     'correct':int(answer==keys[item_id]) if status=='valid' else ''})
    with (out/'scores.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    summary={}
    for cat in meta['config']['categories']:
        rr=[r for r in rows if r['category']==cat]; valid=[r for r in rr if r['status']=='valid']
        ncorrect=sum(r['correct'] for r in valid)
        summary[cat]={'n_expected':len(rr),'n_valid':len(valid),'n_correct':ncorrect,
          'accuracy_valid_only': ncorrect/len(valid) if valid else None,
          'correct_over_all_expected': ncorrect/len(rr) if rr else None,
          'status_counts':{s:sum(r['status']==s for r in rr) for s in sorted(set(r['status'] for r in rr))}}
    write_json(out/'summary.json',summary)
    print('Scores saved. Check missing/error/invalid counts before claiming full-pool accuracy.')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('command',choices=['audit','run','score'])
    ap.add_argument('--data-root',type=Path,required=True)
    ap.add_argument('--config',type=Path,default=HERE/'config.json')
    ap.add_argument('--run-id',default='technical-001')
    ap.add_argument('--phase',choices=['technical','full','repeat'],default='technical')
    ap.add_argument('--candidate-ids');ap.add_argument('--repeat-number',type=int,default=1)
    args=ap.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9_-]+',args.run_id):
        ap.error('run-id must contain only letters, numbers, underscores or hyphens')
    cfg=json.loads(args.config.read_text())
    if args.command=='audit': audit(args.data_root,cfg)
    elif args.command=='run': run(args.data_root,cfg,args)
    else:score(args.data_root,cfg,args.run_id)
if __name__=='__main__':
    main()
