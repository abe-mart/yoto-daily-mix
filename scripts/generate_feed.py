#!/usr/bin/env python3
"""
generate_feed.py

Usage:
  python scripts/generate_feed.py --mp3-dir mp3 --out public --num 10 --site-url "https://owner.github.io/repo" --mode rotate

Modes:
 - rotate  : deterministic rotation by day (no state file needed)
 - random  : random sample each run
"""
import argparse
import os
import shutil
import time
import random
from datetime import date, datetime, timezone
from email.utils import formatdate

def rfc2822_now():
    return formatdate(timeval=None, localtime=False, usegmt=True)

def sanitize_title(fn):
    name = os.path.splitext(fn)[0]
    # replace underscores & dashes with spaces, strip numbers at start
    name = name.replace('_', ' ').replace('-', ' ').strip()
    return name

def build_feed(items, channel_title, channel_link, channel_description, out_file):
    now = rfc2822_now()
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<rss version="2.0">\n')
        f.write('  <channel>\n')
        f.write(f'    <title>{channel_title}</title>\n')
        f.write(f'    <link>{channel_link}</link>\n')
        f.write(f'    <description>{channel_description}</description>\n')
        f.write(f'    <lastBuildDate>{now}</lastBuildDate>\n')
        for it in items:
            pubdate = rfc2822_now()
            guid = f"{it['url']}#{it['filename']}"
            f.write('    <item>\n')
            f.write(f'      <title>{it["title"]}</title>\n')
            f.write(f'      <pubDate>{pubdate}</pubDate>\n')
            f.write(f'      <guid isPermaLink="false">{guid}</guid>\n')
            f.write(f'      <enclosure url="{it["url"]}" length="{it["length"]}" type="audio/mpeg" />\n')
            f.write('    </item>\n')
        f.write('  </channel>\n')
        f.write('</rss>\n')

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--mp3-dir', default='mp3', help='Directory with source MP3s')
    p.add_argument('--out', default='public', help='Output directory (will be deployed)')
    p.add_argument('--num', type=int, default=10, help='How many files to include in the feed')
    p.add_argument('--site-url', required=True, help='Base URL where files will be hosted, e.g. https://owner.github.io/repo')
    p.add_argument('--mode', choices=['rotate','random'], default='rotate', help='Selection mode')
    p.add_argument('--channel-title', default='Daily Yoto Mix', help='RSS channel title')
    p.add_argument('--channel-desc', default='Rotating daily subset of my MP3s for Yoto', help='RSS channel description')
    args = p.parse_args()

    mp3_dir = args.mp3_dir
    out_dir = args.out
    num = args.num
    site_url = args.site_url.rstrip('/')
    mode = args.mode

    if not os.path.isdir(mp3_dir):
        raise SystemExit(f"mp3 dir not found: {mp3_dir}")

    # make output dir clean
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    all_files = [f for f in sorted(os.listdir(mp3_dir)) if f.lower().endswith('.mp3')]
    if not all_files:
        raise SystemExit("No mp3 files found in mp3_dir")

    n = len(all_files)
    take = min(num, n)

    if mode == 'random':
        chosen = random.sample(all_files, take)
    else:  # rotate mode: deterministic selection based on date (so it rotates daily without state)
        epoch = date(2020,1,1).toordinal()  # arbitrary epoch
        today_index = date.today().toordinal() - epoch
        start = (today_index * take) % n
        chosen = []
        for i in range(take):
            chosen.append(all_files[(start + i) % n])

    items = []
    for fn in chosen:
        src = os.path.join(mp3_dir, fn)
        dst = os.path.join(out_dir, fn)
        shutil.copy2(src, dst)
        length = os.path.getsize(dst)
        url = f"{site_url}/{fn}"
        items.append({
            'filename': fn,
            'title': sanitize_title(fn),
            'length': str(length),
            'url': url
        })

    feed_file = os.path.join(out_dir, 'feed.xml')
    build_feed(items, args.channel_title, args.site_url, args.channel_desc, feed_file)
    print(f"Wrote {len(items)} items to {feed_file}")

if __name__ == '__main__':
    main()
