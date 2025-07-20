#!/usr/bin/env python
"""
Fetch first 500 chars of Wikipedia for each distinct author.
"""
import json, csv, time, wikipedia, sys
from pathlib import Path
from tqdm import tqdm

BASE = Path(__file__).resolve().parents[1]
META = BASE/'data'/'meta'
authors = set()

# 1) read metadata_raw.jsonl
for line in open(META/'metadata_raw.jsonl', encoding='utf8'):
    for a in json.loads(line)['authors']:
        if a['name']: authors.add(a['name'])

out_path = META/'author_wiki.jsonl'
done = {json.loads(l)['author'] for l in open(out_path, 'r', encoding='utf8')} if out_path.exists() else set()

with open(out_path,'a',encoding='utf8') as f:
    for name in tqdm(sorted(authors), desc='wiki'):
        if name in done: continue
        try:
            page = wikipedia.page(name, auto_suggest=False)
            snippet = page.summary[:500]
        except Exception as e:
            snippet = f"LOOKUP_ERROR: {e}"
        f.write(json.dumps({"author":name,"wiki":snippet})+'\n')
        time.sleep(0.1)  # throttle

