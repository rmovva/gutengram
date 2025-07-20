#!/usr/bin/env python
"""
Compute 1‑ and 2‑gram counts for American vs British books,
then write a parquet with stats + a jsonl with excerpt lists.
"""
import re, json, math, pandas as pd
from collections import Counter, defaultdict
from pathlib import Path
from tqdm import tqdm

BASE   = Path(__file__).resolve().parents[1]
PROC   = BASE/'data'/'processed'/'clean_texts'
INDEX  = pd.read_parquet(BASE/'data'/'meta'/'book_index.parquet')
STATS  = BASE/'data'/'processed'/'ngram_stats.parquet'
EXCERPTS = BASE/'data'/'processed'/'ngram_examples.jsonl'

tok_re = re.compile(r"[a-z']+")
AM, BR = 'American', 'British'
counters = {AM:Counter(), BR:Counter()}
examples = {AM:defaultdict(list), BR:defaultdict(list)}

def ngrams(tokens, n):
    return zip(*[tokens[i:] for i in range(n)])

for row in tqdm(INDEX.itertuples(), total=len(INDEX), desc='ngrams'):
    if row.nationality not in (AM, BR): continue
    txt = Path(row.path).read_text(encoding='utf8')
    toks = tok_re.findall(txt)
    for n in (1,2):
        for ng in ngrams(toks, n):
            key = ' '.join(ng)
            counters[row.nationality][key] += 1
    # save first 2 excerpts per n‑gram
    for m in re.finditer(tok_re, txt):
        word = m.group(0)
        s,e = m.start(), m.end()
        snippet = txt[max(0,s-150):min(len(txt),e+150)]
        key1 = word
        if len(examples[row.nationality][key1])<2:
            examples[row.nationality][key1].append(snippet)
    # (bigram excerpts optional – keep file small)

# merge stats
rows=[]
for ng in set(counters[AM])|set(counters[BR]):
    a,b = counters[AM][ng], counters[BR][ng]
    tot  = a+b
    if tot<200:        # frequency floor
        continue
    ratio = math.log2((a+0.5)/(b+0.5))  # add‑0.5 smoothing
    rows.append({"ngram":ng,"len":len(ng.split()),"american":a,
                 "british":b,"total":tot,"log_ratio":ratio})
pd.DataFrame(rows).to_parquet(STATS)

# write excerpts
with open(EXCERPTS,'w',encoding='utf8') as f:
    for nat in (AM,BR):
        for ng, lst in examples[nat].items():
            f.write(json.dumps({"ngram":ng,"nat":nat,"ex":lst})+'\n')

