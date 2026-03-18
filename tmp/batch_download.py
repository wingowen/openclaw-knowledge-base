import os
import sys
import json
import re
import requests

COOKIE_FILE = os.path.expanduser('~/.openclaw/workspace/bilibili_cookie.txt')
OUT_DIR = '/root/.openclaw/workspace/tmp/subtitles'
os.makedirs(OUT_DIR, exist_ok=True)

CHAPTERS = [
    ("10上", "BV1ZBzkYsEtV", 0, "第10章", "物品材料", "上"),
    ("10下", "BV19uCqYCEHy", 0, "第10章", "物品材料", "下"),
    ("11上", "BV1VMr1Y8ECZ", 0, "第11章", "时尚潮流", "上"),
    ("11下", "BV1TDcQe9Eom", 0, "第11章", "时尚潮流", "下"),
    ("12上", "BV1bnwaeiEyu", 0, "第12章", "饮食健康", "上"),
    ("12下", "BV1niFQegEXP", 0, "第12章", "饮食健康", "下"),
    ("13上", "BV1LJNieeEbd", 0, "第13章", "建筑场所", "上"),
    ("13下", "BV1cnADeVEEH", 0, "第13章", "建筑场所", "下"),
    ("14上", "BV1f4XRYtEkF", 0, "第14章", "交通旅行", "上"),
    ("14下", "BV1GnRpYcEGD", 0, "第14章", "交通旅行", "下"),
    ("15上", "BV1yJoSYaEEn", 0, "第15章", "国家政府", "上"),
    ("15下", "BV1XnfKYfErp", 0, "第15章", "国家政府", "下"),
    ("16上", "BV1RYowY7EvL", 0, "第16章", "社会经济", "上"),
    ("16下", "BV17SGkzAE8W", 0, "第16章", "社会经济", "下"),
    ("17上", "BV1Q2EEzBEBj", 0, "第17章", "法律法规", "上"),
    ("17下", "BV1HKJAzyE7k", 0, "第17章", "法律法规", "下"),
    ("18上", "BV1ebMAzzEXG", 0, "第18章", "沙场争锋", "上"),
    ("18中", "BV1guK6zcEpd", 0, "第18章", "沙场争锋", "中"),
    ("18下", "BV19z3qz6EMW", 0, "第18章", "沙场争锋", "下"),
]

def get_saved_cookie():
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, 'r') as f:
            return f.read().strip()
    return ""

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    'Referer': 'https://www.bilibili.com/',
}

def get_video_info(bv_id, cookie):
    url = "https://api.bilibili.com/x/web-interface/view"
    params = {'bvid': bv_id}
    headers = {**HEADERS, 'Cookie': cookie}
    resp = requests.get(url, params=params, headers=headers)
    data = resp.json()
    if data['code'] != 0:
        return None, data.get('message', 'unknown error')
    return data['data'], None

def fetch_subtitle_content(bv_id, cid, cookie):
    subtitle_api = 'https://api.bilibili.com/x/player/v2'
    headers = {**HEADERS, 'Cookie': cookie, 'origin': 'https://www.bilibili.com', 'authority': 'api.bilibili.com'}
    params = {'bvid': bv_id, 'cid': cid}
    resp = requests.get(subtitle_api, headers=headers, params=params)
    data = resp.json()
    
    if data.get('code') != 0:
        return None
    
    subtitles = data.get('data', {}).get('subtitle', {}).get('subtitles', [])
    if not subtitles:
        return None

    target_url = ""
    for s in subtitles:
        if 'zh' in s.get('lan', ''):
            target_url = s['subtitle_url']
            break
    if not target_url and subtitles:
        target_url = subtitles[0].get('subtitle_url', "")
    if not target_url:
        return None

    if target_url.startswith('//'):
        target_url = 'https:' + target_url
    
    resp = requests.get(target_url)
    body = resp.json().get('body', [])
    full_text = "\n".join([b.get('content', '') for b in body])
    return full_text

def main():
    cookie = get_saved_cookie()
    if not cookie:
        print("No cookie found!")
        sys.exit(1)
    
    results = []
    for label, bv_id, p_num, ch, theme, part in CHAPTERS:
        try:
            info, err = get_video_info(bv_id, cookie)
            if not info:
                results.append({"label": label, "status": f"ERROR: {err}"})
                print(f"❌ {label}: {err}")
                continue
            
            pages = info.get('pages', [])
            if p_num >= len(pages):
                results.append({"label": label, "status": f"ERROR: invalid p_num"})
                print(f"❌ {label}: invalid p_num")
                continue
            
            cid = pages[p_num]['cid']
            title = info.get('title', bv_id)
            full_text = fetch_subtitle_content(bv_id, cid, cookie)
            
            if not full_text:
                results.append({"label": label, "status": "NO_SUBTITLE", "title": title})
                print(f"⚠️ {label}: no subtitle found")
                # Save empty file
                with open(os.path.join(OUT_DIR, f"{label}.txt"), 'w', encoding='utf-8') as f:
                    f.write("")
                continue
            
            out_path = os.path.join(OUT_DIR, f"{label}.txt")
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(full_text)
            
            results.append({"label": label, "bvid": bv_id, "title": title, "chars": len(full_text), "status": "OK"})
            print(f"✅ {label} ({bv_id}): {len(full_text)} chars - {title}")
        except Exception as e:
            results.append({"label": label, "status": f"ERROR: {e}"})
            print(f"❌ {label}: {e}")
    
    with open(os.path.join(OUT_DIR, "_meta.json"), 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\nDone! Meta saved to _meta.json")

if __name__ == "__main__":
    main()
