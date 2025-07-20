#!/usr/bin/env python
"""
Strip PG headers/footers, lower‑case, keep year + nationality in a parquet index.
"""
import json, re, pandas as pd
from pathlib import Path
from tqdm import tqdm

BASE = Path(__file__).resolve().parents[1]
RAW   = BASE/'data'/'raw'
PROC  = BASE/'data'/'processed'/'clean_texts'; PROC.mkdir(parents=True, exist_ok=True)
META  = BASE/'data'/'meta'
nat_map = dict(line.strip().split(',',1) for line in open(META/'author_nationality.csv',encoding='utf8'))

records = []
for j in tqdm(open(META/'metadata_raw.jsonl',encoding='utf8'), desc='clean'):
    book = json.loads(j)
    authors = [a['name'] for a in book['authors']]
    # Majority vote if multiple authors
    nat = next((nat_map.get(a) for a in authors if nat_map.get(a) in {'American','British','Canadian'}), None)
    if not nat: continue
    year = book['copyright_year'] or book.get('download_count')  # fallback
    book_id = book['id']
    raw_path = RAW/f"{book_id}.txt"
    if not raw_path.exists(): continue
    txt = raw_path.read_text(encoding='utf8', errors='ignore')
    # crude header/body split
    body = re.split(r'\*\*\* START OF THE PROJECT GUTENBERG EBOOK .*?\*\*\*', txt, flags=re.I|re.S)[-1]
    body = re.split(r'\*\*\* END OF THE PROJECT GUTENBERG EBOOK .*?', body, flags=re.I|re.S)[0]
    body = re.sub(r'\s+',' ', body).lower()
    clean_path = PROC/f"{book_id}.txt"
    clean_path.write_text(body,encoding='utf8')
    records.append({"book_id":book_id,"year":year,"nationality":nat,"path":str(clean_path)})

pd.DataFrame(records).to_parquet(BASE/'data'/'meta'/'book_index.parquet')

