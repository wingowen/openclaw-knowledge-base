import asyncio
import json
import os
import urllib.request
import sys

# bilibili-api-python
from bilibili_api import video

CHAPTERS = [
    ("10上", "BV1ZBzkYsEtV", "第10章", "物品材料", "上"),
    ("10下", "BV19uCqYCEHy", "第10章", "物品材料", "下"),
    ("11上", "BV1VMr1Y8ECZ", "第11章", "时尚潮流", "上"),
    ("11下", "BV1TDcQe9Eom", "第11章", "时尚潮流", "下"),
    ("12上", "BV1bnwaeiEyu", "第12章", "饮食健康", "上"),
    ("12下", "BV1niFQegEXP", "第12章", "饮食健康", "下"),
    ("13上", "BV1LJNieeEbd", "第13章", "建筑场所", "上"),
    ("13下", "BV1cnADeVEEH", "第13章", "建筑场所", "下"),
    ("14上", "BV1f4XRYtEkF", "第14章", "交通旅行", "上"),
    ("14下", "BV1GnRpYcEGD", "第14章", "交通旅行", "下"),
    ("15上", "BV1yJoSYaEEn", "第15章", "国家政府", "上"),
    ("15下", "BV1XnfKYfErp", "第15章", "国家政府", "下"),
    ("16上", "BV1RYowY7EvL", "第16章", "社会经济", "上"),
    ("16下", "BV17SGkzAE8W", "第16章", "社会经济", "下"),
    ("17上", "BV1Q2EEzBEBj", "第17章", "法律法规", "上"),
    ("17下", "BV1HKJAzyE7k", "第17章", "法律法规", "下"),
    ("18上", "BV1ebMAzzEXG", "第18章", "沙场争锋", "上"),
    ("18中", "BV1guK6zcEpd", "第18章", "沙场争锋", "中"),
    ("18下", "BV19z3qz6EMW", "第18章", "沙场争锋", "下"),
]

OUT_DIR = "/root/.openclaw/workspace/tmp/subtitles"
os.makedirs(OUT_DIR, exist_ok=True)

async def get_subtitle(bvid):
    v = video.Video(bvid=bvid)
    info = await v.get_info()
    cid = info['cid']
    subtitle_info = await v.get_subtitle(cid)
    subtitles = subtitle_info.get('subtitles', [])
    if subtitles:
        subtitle_url = 'https:' + subtitles[0]['subtitle_url']
        req = urllib.request.Request(subtitle_url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        return data.get('body', [])
    return []

async def main():
    results = []
    for label, bvid, ch, theme, part in CHAPTERS:
        try:
            subs = await get_subtitle(bvid)
            text = '\n'.join([s['content'] for s in subs])
            out_path = os.path.join(OUT_DIR, f"{label}.txt")
            with open(out_path, 'w') as f:
                f.write(text)
            results.append((label, bvid, ch, theme, part, len(subs), "OK"))
            print(f"✅ {label} ({bvid}): {len(subs)} lines")
        except Exception as e:
            results.append((label, bvid, ch, theme, part, 0, f"ERROR: {e}"))
            print(f"❌ {label} ({bvid}): {e}")
        # Small delay to avoid rate limiting
        await asyncio.sleep(1)
    
    # Save metadata
    with open(os.path.join(OUT_DIR, "_meta.json"), 'w') as f:
        json.dump([{"label": r[0], "bvid": r[1], "ch": r[2], "theme": r[3], "part": r[4], "lines": r[5], "status": r[6]} for r in results], f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
