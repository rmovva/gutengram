#!/usr/bin/env python
"""
Download English books via Gutendex and store both .txt and metadata.
Run:  python 01_download_gutenberg.py [--delay SECONDS]
"""
import argparse
import json
import os
import re
import requests
import time
import concurrent.futures
from html.parser import HTMLParser
from pathlib import Path

from tqdm import tqdm

parser = argparse.ArgumentParser(
    description="Download English books via Gutendex and store both .txt and metadata."
)
parser.add_argument(
    '--delay', type=float, default=1.0,
    help='seconds to sleep between page requests (default: 1.0)'
)
parser.add_argument(
    '--workers', type=int, default=10,
    help='number of workers to download texts concurrently (default: 10)'
)
parser.add_argument(
    '--max-books', type=int, default=10_000,
    help='maximum number of books to download (default: 10_000)'
)
parser.add_argument(
    '--timeout', type=int, default=100,
    help='timeout in seconds for each request (default: 100)'
)
args = parser.parse_args()

# use a requests session for connection pooling
session = requests.Session()

BASE = Path(__file__).resolve().parents[1]  # project root
RAW   = BASE/'data'/'raw'
META  = BASE/'data'/'meta'
RAW.mkdir(parents=True, exist_ok=True); META.mkdir(parents=True, exist_ok=True)

# Track books that already have metadata so we don't write duplicates on reruns
meta_path = META / 'metadata_raw.jsonl'
existing_ids: set[int] = set()
if meta_path.exists():
    with open(meta_path, 'r', encoding='utf8') as f:
        for line in f:
            try:
                existing_ids.add(json.loads(line)['id'])
            except json.JSONDecodeError:
                # ignore malformed lines
                pass

API = "https://gutendex.com/books/"
MAX_BOOKS = 10_000  # limit to first 10k most popular books
params = {"languages": "en", "author_year_start": 1800, "mime_type": "text/plain", "sort": "popular"}
next_url = API
with open(META/'metadata_raw.jsonl', 'a', encoding='utf8') as meta_f:
    pbar = None  # global progress bar

    while next_url:
        try:
            resp = session.get(next_url, params=params, timeout=args.timeout)
            resp.raise_for_status()
            r = resp.json()
            # Clear params after the first request to avoid duplicating query args when using the "next" URL returned by the API
            params = None
        except (requests.exceptions.RequestException, requests.exceptions.JSONDecodeError) as e:
            # Skip this page if we hit an HTTP error or the body isn't valid JSON
            print(f"[warning] metadata fetch failed for {next_url}: {e}")
            time.sleep(args.delay)
            continue

        # Initialize overall progress bar on first iteration
        if pbar is None:
            total_api = r.get('count', 0)
            total = min(total_api, MAX_BOOKS)
            pbar = tqdm(total=total, desc='books', unit='book')
            pbar.update(len(existing_ids))  # start progress at already-processed count

        books = r.get('results', [])

        # write raw metadata
        # collect only new books (metadata not yet recorded)
        new_books = []
        for book in books:
            book_id = book['id']
            if book_id in existing_ids:
                continue  # metadata already stored
            meta_f.write(json.dumps(book, ensure_ascii=False) + '\n')
            existing_ids.add(book_id)
            new_books.append(book)

        # helper to download one book
        def download_book(book):
            book_id = book['id']
            title = book.get('title', 'Unknown')
            outpath = RAW / f"{book_id}.txt"
            if outpath.exists():
                return  # already downloaded

            fmt = book.get('formats', {})
            # look for a text/plain format (any charset)
            url = next((v for k, v in fmt.items() if k.startswith('text/plain')), None)
            if not url:
                print(f"[warning] no text/plain format for book {book_id} '{title}', skipping download")
                return

            try:
                resp = session.get(url, timeout=100)
                resp.raise_for_status()
                outpath.write_text(resp.text, encoding='utf8')
            except Exception as e:
                print(f"[error] failed download for book {book_id} '{title}' from {url}: {e}")

        # download concurrently and update global progress bar
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
            for _ in executor.map(download_book, new_books):
                pbar.update(1)

        # move to next page unless we hit the cap
        next_url = r.get('next')  # Gutendex gives full URL for next page
        # if we've reached or exceeded the cap, stop fetching more pages
        if pbar.n >= MAX_BOOKS:
            next_url = None

        time.sleep(args.delay)  # be polite

    if pbar:
        pbar.close()
