#!/usr/bin/env python3
"""
新概念英语第二册全量抓取脚本
从网站提取英文+中文，按句切分对齐
"""
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

# Proxy for WSL2
_HOST_IP = os.popen("ip route show | grep default | awk '{print $3}'").read().strip()
if _HOST_IP:
    os.environ['http_proxy'] = f'http://{_HOST_IP}:10808'
    os.environ['https_proxy'] = f'http://{_HOST_IP}:10808'

BASE_URL = "https://newconceptenglish.com/index.php?id="
OUTPUT = Path(__file__).parent.parent / "src" / "data" / "new-concept-2.json"


def fetch_page(lesson_id: str) -> str:
    url = f"{BASE_URL}{lesson_id}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


def extract_content(html: str) -> dict:
    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)
    english_parts = []
    chinese_parts = []
    title = ""
    question = ""

    for p in paragraphs:
        text = re.sub(r'<[^>]+>', '', p).strip()
        if len(text) < 15:
            continue
        if 'copyright' in text.lower() or 'NewConceptEnglish.com' in text:
            continue
        if re.match(r'^版权', text):
            continue
        if re.match(r'^(英|美)\s*(n\.|v\.|adj\.|adv\.)', text):
            continue
        # Skip IP address lines
        if re.match(r'^地址：\s*\d', text):
            continue

        has_cn = bool(re.search(r'[\u4e00-\u9fa5]', text))
        has_en = bool(re.search(r'[a-zA-Z]{5,}', text))

        if has_en and not has_cn and len(text) < 40 and not english_parts:
            title = text
            continue
        if has_en and has_cn and '?' in text and len(text) < 200:
            question = text
            continue
        if has_en and not has_cn and len(text) > 30:
            english_parts.append(text)
            continue
        if english_parts and has_cn and not has_en and len(text) > 15:
            chinese_parts.append(text)

    return {
        "title": title,
        "question": question,
        "english_paragraph": " ".join(english_parts),
        "chinese_paragraph": "".join(chinese_parts),
    }


def split_english_sentences(text: str) -> list[str]:
    # Handle abbreviations
    text = re.sub(r'([.!?])\s+([A-Z\'\"\u201c])', r'\1\n\2', text)
    sentences = [s.strip() for s in text.split('\n') if s.strip()]
    return [s for s in sentences if len(s) > 8 and re.search(r'[a-zA-Z]', s)]


def split_chinese_sentences(text: str) -> list[str]:
    # Split on Chinese sentence-ending punctuation
    # Remove trailing junk (like "地址：xxx")
    text = re.sub(r'地址：.*$', '', text).strip()
    # Split on 。！？ but keep the punctuation
    parts = re.split(r'([。！？])', text)
    sentences = []
    for i in range(0, len(parts) - 1, 2):
        s = (parts[i] + parts[i+1]).strip()
        if len(s) > 3:
            sentences.append(s)
    # Handle last part without punctuation
    if len(parts) % 2 == 1 and parts[-1].strip() and len(parts[-1].strip()) > 3:
        sentences.append(parts[-1].strip())
    return sentences


def process_lesson(lesson_id: str) -> dict | None:
    try:
        html = fetch_page(lesson_id)
    except Exception as e:
        print(f"❌ {e}")
        return None

    content = extract_content(html)
    if not content["english_paragraph"]:
        print("❌ 无英文")
        return None

    en_sents = split_english_sentences(content["english_paragraph"])
    if not en_sents:
        print("❌ 无句子")
        return None

    cn_sents = split_chinese_sentences(content["chinese_paragraph"])

    # Build sentence pairs
    sentences = []
    for i, en in enumerate(en_sents):
        cn = cn_sents[i] if i < len(cn_sents) else ""
        sentences.append({"text": en, "translation": cn})

    cn_status = f"{len(cn_sents)}中" if cn_sents else "无中文"
    print(f"{len(en_sents)}英 {cn_status}", end="")

    # Check alignment
    if len(cn_sents) != len(en_sents):
        print(f" ⚠️中英不齐({len(en_sents)}vs{len(cn_sents)})", end="")

    return {
        "lesson_id": lesson_id,
        "title": content["title"],
        "question": content["question"],
        "sentences": sentences,
    }


def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 96

    # Load existing
    existing = {}
    if OUTPUT.exists():
        with open(OUTPUT) as f:
            data = json.load(f)
            for lesson in data.get("articles", []):
                lid = lesson.get("lesson_id", "")
                existing[lid] = lesson
        print(f"📂 已有 {len(existing)} 课")

    stats = {"ok": 0, "warn": 0, "fail": 0, "skip": 0}

    for i in range(start, end + 1):
        lesson_id = f"2-{i:03d}"
        if lesson_id in existing:
            ex = existing[lesson_id]
            ex_sents = ex.get("sentences", [])
            ex_cn = sum(1 for s in ex_sents if s.get("translation", ""))
            if ex_sents and ex_cn == len(ex_sents):
                print(f"📖 {lesson_id}... ⏭️")
                stats["skip"] += 1
                continue
            else:
                print(f"📖 {lesson_id}... 🔄 重取({ex_cn}/{len(ex_sents)})", end="  ", flush=True)

        print(f"📖 {lesson_id}... ", end="", flush=True)
        result = process_lesson(lesson_id)
        if result:
            existing[lesson_id] = result
            has_cn = all(s["translation"] for s in result["sentences"])
            en_count = len(result["sentences"])
            cn_count = sum(1 for s in result["sentences"] if s["translation"])
            if cn_count == en_count:
                print(" ✅")
                stats["ok"] += 1
            else:
                print()
                stats["warn"] += 1

            # Save incrementally
            all_lessons = sorted(existing.values(), key=lambda x: x.get("lesson_id", ""))
            with open(OUTPUT, "w", encoding="utf-8") as f:
                json.dump({"articles": all_lessons}, f, ensure_ascii=False, indent=2)
        else:
            stats["fail"] += 1

        time.sleep(1.2)  # Rate limit

    print(f"\n📊 完成! ✅{stats['ok']} ⚠️{stats['warn']} ❌{stats['fail']} ⏭️{stats['skip']}")
    print(f"📁 {OUTPUT}")


if __name__ == "__main__":
    main()
