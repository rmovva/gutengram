#!/usr/bin/env python
"""
Download English books via Gutendex and store both .txt and metadata.
Run:  python 01_download_gutenberg.py
"""
import json, os, re, requests, time
from pathlib import Path
from tqdm import tqdm

BASE = Path(__file__).resolve().parents[1]  # project root
RAW   = BASE/'data'/'raw'
META  = BASE/'data'/'meta'
RAW.mkdir(parents=True, exist_ok=True); META.mkdir(parents=True, exist_ok=True)

API = "https://gutendex.com/books/"
params = {"languages":"en"}
next_url = API
with open(META/'metadata_raw.jsonl', 'a', encoding='utf8') as meta_f:
    while next_url:
        r = requests.get(next_url, params=params, timeout=30).json()
        for book in tqdm(r['results'], desc='books page', leave=False):
            book_id = book["id"]
            path    = RAW/f"{book_id}.txt"
            if not path.exists():
                # Select a plaintext download URL, preferring utf-8
                txt_url = None
                try:
                    txt_url = next(v for v in book['formats'].values()
                                   if v.endswith('.txt') and 'utf-8' in v.lower())
                except StopIteration:
                    try:
                        txt_url = next(v for v in book['formats'].values()
                                       if v.endswith('.txt'))
                    except StopIteration:
                        print(f"[warning] no .txt format for book {book_id}, skipping download")
                if txt_url:
                    txt = requests.get(txt_url, timeout=60).text
                    path.write_text(txt, encoding='utf8')
            meta_f.write(json.dumps(book, ensure_ascii=False)+'\n')
        next_url = r['next']  # Gutendex gives full URL
        time.sleep(1)         # be polite

