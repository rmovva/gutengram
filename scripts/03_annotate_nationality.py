#!/usr/bin/env python
"""
Ask GPT‑4o to label author nationality (American|British|Canadian|Other|Unknown).
Requires $OAI_GENERAL.
"""
import json, os, time, openai, re
from pathlib import Path
from tqdm import tqdm

openai.api_key = os.getenv("OAI_GENERAL")
BASE = Path(__file__).resolve().parents[1]
WIKI = BASE/'data'/'meta'/'author_wiki.jsonl'
OUT  = BASE/'data'/'meta'/'author_nationality.csv'

done = {}
if OUT.exists():
    for line in open(OUT,encoding='utf8'):
        name, nat = line.strip().split(',',1)
        done[name]=nat

with open(OUT,'a',encoding='utf8') as f_out, open(WIKI,encoding='utf8') as f_in:
    for row in tqdm(f_in, desc='LLM'):
        d = json.loads(row)
        name = d['author']
        if name in done: continue
        wiki = d['wiki'][:500]
        prompt = (
          "You are a librarian. "
          "Return exactly one of {American,British,Canadian,Other,Unknown}. "
          f"Author: {name}\nData: {wiki}\nAnswer:"
        )
        try:
            rsp = openai.ChatCompletion.create(model="gpt-4o-mini",
                    messages=[{"role":"user","content":prompt}],
                    temperature=0)
            nat = rsp['choices'][0]['message']['content'].strip().split()[0]
        except Exception as e:
            nat = "Unknown"
        f_out.write(f"{name},{nat}\n")
        time.sleep(0.25)  # stay well under rate‑limit

