import asyncio
import json
import os
import urllib.request
import urllib.error
import time

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

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.bilibili.com/',
}

def bv_to_aid(bvid):
    """Convert BV id to aid using the API"""
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    req = urllib.request.Request(url, headers=HEADERS)
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    if data['code'] == 0:
        return data['data']['aid'], data['data']['cid']
    raise Exception(f"Failed to get info: {data}")

def get_subtitle(bvid):
    """Get subtitle text for a video"""
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    req = urllib.request.Request(url, headers=HEADERS)
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    if data['code'] != 0:
        raise Exception(f"API error: {data}")
    
    cid = data['data']['cid']
    subtitle_info = data['data'].get('subtitle', {})
    subtitles = subtitle_info.get('subtitles', [])
    
    if not subtitles:
        # Try the player API
        aid = data['data']['aid']
        player_url = f"https://api.bilibili.com/x/player/v2?bvid={bvid}&cid={cid}"
        req2 = urllib.request.Request(player_url, headers=HEADERS)
        resp2 = urllib.request.urlopen(req2)
        player_data = json.loads(resp2.read())
        if player_data['code'] == 0:
            subtitles = player_data['data'].get('subtitle', {}).get('subtitles', [])
    
    if subtitles:
        subtitle_url = subtitles[0].get('subtitle_url', '')
        if subtitle_url.startswith('//'):
            subtitle_url = 'https:' + subtitle_url
        elif not subtitle_url.startswith('http'):
            subtitle_url = 'https://aisubtitle.hdslb.com' + subtitle_url
        
        req3 = urllib.request.Request(subtitle_url, headers=HEADERS)
        resp3 = urllib.request.urlopen(req3)
        sub_data = json.loads(resp3.read())
        return sub_data.get('body', [])
    
    return []

def main():
    results = []
    for label, bvid, ch, theme, part in CHAPTERS:
        try:
            subs = get_subtitle(bvid)
            text = '\n'.join([s['content'] for s in subs])
            out_path = os.path.join(OUT_DIR, f"{label}.txt")
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(text)
            results.append({"label": label, "bvid": bvid, "ch": ch, "theme": theme, "part": part, "lines": len(subs), "status": "OK", "chars": len(text)})
            print(f"✅ {label} ({bvid}): {len(subs)} lines, {len(text)} chars")
        except Exception as e:
            results.append({"label": label, "bvid": bvid, "ch": ch, "theme": theme, "part": part, "lines": 0, "status": f"ERROR: {e}"})
            print(f"❌ {label} ({bvid}): {e}")
        time.sleep(0.5)
    
    with open(os.path.join(OUT_DIR, "_meta.json"), 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
