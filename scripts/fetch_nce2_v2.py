#!/usr/bin/env python3
"""NCE2 全量抓取 - 一次性抓完 2-001 到 2-096"""
import json, os, re, sys, time, urllib.request
from pathlib import Path

_HOST_IP = os.popen("ip route show | grep default | awk '{print $3}'").read().strip()
if _HOST_IP:
    os.environ['http_proxy'] = f'http://{_HOST_IP}:10808'
    os.environ['https_proxy'] = f'http://{_HOST_IP}:10808'

BASE_URL = "https://newconceptenglish.com/index.php?id="
OUTPUT = Path(__file__).parent.parent / "src" / "data" / "new-concept-2.json"

def fetch_page(lesson_id):
    url = f"{BASE_URL}{lesson_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")

def extract_content(html):
    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)
    english_parts, chinese_parts = [], []
    title = question = ""
    for p in paragraphs:
        text = re.sub(r'<[^>]+>', '', p).strip()
        if len(text) < 15: continue
        if 'copyright' in text.lower() or 'NewConceptEnglish.com' in text: continue
        if re.match(r'^版权', text): continue
        if re.match(r'^(英|美)\s*(n\.|v\.|adj\.|adv\.)', text): continue
        if re.match(r'地址：\s*\d', text): continue
        has_cn = bool(re.search(r'[\u4e00-\u9fa5]', text))
        has_en = bool(re.search(r'[a-zA-Z]{5,}', text))
        if has_en and not has_cn and len(text) < 40 and not english_parts:
            title = text; continue
        if has_en and has_cn and '?' in text and len(text) < 200:
            question = text; continue
        if has_en and not has_cn and len(text) > 30:
            english_parts.append(text); continue
        if english_parts and has_cn and not has_en and len(text) > 15:
            chinese_parts.append(text)
    return {"title": title, "question": question,
            "english_paragraph": " ".join(english_parts),
            "chinese_paragraph": "".join(chinese_parts)}

def split_en(text):
    text = re.sub(r'([.!?])\s+([A-Z\'\"\u201c])', r'\1\n\2', text)
    return [s.strip() for s in text.split('\n') if s.strip() and len(s.strip()) > 8 and re.search(r'[a-zA-Z]', s.strip())]

def split_cn(text):
    text = re.sub(r'地址：.*$', '', text).strip()
    parts = re.split(r'([。！？])', text)
    sents = []
    for i in range(0, len(parts)-1, 2):
        s = (parts[i]+parts[i+1]).strip()
        if len(s) > 3: sents.append(s)
    if len(parts) % 2 == 1 and parts[-1].strip() and len(parts[-1].strip()) > 3:
        sents.append(parts[-1].strip())
    return sents

def main():
    existing = {}
    if OUTPUT.exists():
        with open(OUTPUT) as f:
            data = json.load(f)
        for lesson in data.get("articles", []):
            lid = lesson.get("lesson_id", "")
            sents = lesson.get("sentences", [])
            cn_count = sum(1 for s in sents if s.get("translation",""))
            if sents and cn_count == len(sents):
                existing[lid] = lesson
        print(f"📂 已有完整课程: {len(existing)}")

    stats = {"ok": 0, "warn": 0, "fail": 0, "skip": 0}

    for i in range(1, 97):
        lesson_id = f"2-{i:03d}"
        if lesson_id in existing:
            print(f"📖 {lesson_id}... ⏭️")
            stats["skip"] += 1
            continue

        print(f"📖 {lesson_id}... ", end="", flush=True)
        try:
            html = fetch_page(lesson_id)
        except Exception as e:
            print(f"❌ {e}")
            stats["fail"] += 1
            continue

        content = extract_content(html)
        if not content["english_paragraph"]:
            print("❌ 无英文")
            stats["fail"] += 1
            continue

        en_sents = split_en(content["english_paragraph"])
        if not en_sents:
            print("❌ 无句子")
            stats["fail"] += 1
            continue

        cn_sents = split_cn(content["chinese_paragraph"])
        sentences = [{"text": en, "translation": cn_sents[i] if i < len(cn_sents) else ""}
                     for i, en in enumerate(en_sents)]

        cn_ok = sum(1 for s in sentences if s["translation"])
        if cn_ok == len(sentences):
            print(f"{len(en_sents)}句 ✅")
            stats["ok"] += 1
        else:
            print(f"{len(en_sents)}句 ⚠️{cn_ok}/{len(en_sents)}")
            stats["warn"] += 1

        existing[lesson_id] = {
            "lesson_id": lesson_id,
            "title": content["title"],
            "question": content["question"],
            "sentences": sentences,
        }

        all_lessons = sorted(existing.values(), key=lambda x: x.get("lesson_id", ""))
        with open(OUTPUT, "w", encoding="utf-8") as f:
            json.dump({"articles": all_lessons}, f, ensure_ascii=False, indent=2)

        time.sleep(1.2)

    print(f"\n📊 完成! ✅{stats['ok']} ⚠️{stats['warn']} ❌{stats['fail']} ⏭️{stats['skip']}")

if __name__ == "__main__":
    main()
