#!/usr/bin/env python3
"""
新概念英语课文抓取 + 逐句翻译脚本
从 newconceptenglish.com 抓取英文课文，用 MyMemory API 翻译为中文逐句对照
"""
import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path

# Use proxy for external API calls (required in WSL2 for external APIs)
_HOST_IP = os.popen("ip route show | grep default | awk '{print $3}'").read().strip()
if _HOST_IP:
    os.environ['http_proxy'] = f'http://{_HOST_IP}:10808'
    os.environ['https_proxy'] = f'http://{_HOST_IP}:10808'

BASE_URL = "https://newconceptenglish.com/index.php?id="
BOOK_MAP = {
    2: {"prefix": "2", "total": 96, "output": "new-concept-2.json"},
    3: {"prefix": "3", "total": 60, "output": "new-concept-3-full.json"},
}

# Rate limiting state
_rate_limit_count = 0
_last_request_time = 0


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
    text = re.sub(r'([.!?])\s+([A-Z\'"])', r'\1\n\2', text)
    sentences = [s.strip() for s in text.split('\n') if s.strip()]
    return [s for s in sentences if len(s) > 10 and re.search(r'[a-zA-Z]', s)]


def translate_batch(sentences: list[str], retries: int = 3) -> list[str]:
    """Translate sentences using MyMemory API with batching (500 char limit per request)"""
    global _last_request_time

    if not sentences:
        return []

    result = [""] * len(sentences)

    # Split into batches that fit within 500 char limit
    batches = []  # [(start_idx, [sentences])]
    current_batch = []
    current_len = 0
    start_idx = 0

    for i, sent in enumerate(sentences):
        marker_len = len(f"[{i}]") + len(sent) + 1  # +1 for newline
        if current_len + marker_len > 450 and current_batch:
            batches.append((start_idx, current_batch))
            current_batch = [sent]
            current_len = len(sent)
            start_idx = i
        else:
            current_batch.append(sent)
            current_len += marker_len
    if current_batch:
        batches.append((start_idx, current_batch))

    for batch_idx, (start, batch_sents) in enumerate(batches):
        joined = "\n".join(f"[{start+i}]{s}" for i, s in enumerate(batch_sents))

        url = "https://api.mymemory.translated.net/get?" + urllib.parse.urlencode({
            "q": joined,
            "langpair": "en|zh-CN",
        })

        for attempt in range(retries + 1):
            now = time.time()
            if now - _last_request_time < 5:
                time.sleep(5 - (now - _last_request_time))
            _last_request_time = time.time()

            try:
                req = urllib.request.Request(url, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; NCE-Bot/1.0)"
                })
                with urllib.request.urlopen(req, timeout=20) as resp:
                    data = json.loads(resp.read().decode())

                if data.get("responseStatus") == 200:
                    translated = data["responseData"]["translatedText"]
                    # Check for error messages
                    if "QUERY LENGTH LIMIT" in translated or "LIMIT EXCEEDED" in translated:
                        raise Exception("query_too_long")
                    parts = re.split(r'\[(\d+)\]', translated)
                    for j in range(1, len(parts)-1, 2):
                        idx = int(parts[j])
                        text = parts[j+1].strip()
                        if 0 <= idx < len(result):
                            result[idx] = text
                    break  # success, move to next batch
                elif data.get("responseStatus") == 429:
                    wait = [10, 30, 60][min(attempt, 2)]
                    print(f"⏳{wait}s", end=" ", flush=True)
                    time.sleep(wait)
                else:
                    raise Exception(f"status_{data.get('responseStatus')}")
            except Exception as e:
                if attempt < retries:
                    wait = [8, 20, 45][min(attempt, 2)]
                    print(f"⏳{wait}s", end=" ", flush=True)
                    time.sleep(wait)
                else:
                    print(f"⚠️", end="", flush=True)

    return result


def review_translations(en_sents, api_trans, orig_cn):
    issues = []
    for i, (en, api_cn) in enumerate(zip(en_sents, api_trans)):
        if not api_cn:
            issues.append({"sentence": i+1, "type": "missing", "en": en[:50]})
            continue
        api_chars = set(api_cn)
        orig_chars = set(orig_cn)
        overlap = len(api_chars & orig_chars) / max(len(api_chars), 1)
        if overlap < 0.3 and len(api_cn) > 5:
            issues.append({
                "sentence": i+1, "type": "divergent",
                "en": en[:50], "api_cn": api_cn[:30],
            })
    return issues


def process_lesson(lesson_id: str, book: int) -> dict | None:
    print(f"📖 {lesson_id}...", end=" ", flush=True)
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

    print(f"{len(en_sents)}句", end=" ", flush=True)

    # Batch translate all sentences in one API call
    translations = translate_batch(en_sents)

    issues = review_translations(en_sents, translations, content["chinese_paragraph"])
    if issues:
        print(f"⚠️{len(issues)}问", end=" ")
    else:
        print("✅", end=" ")
    print()

    sentences = [{"text": en, "translation": cn} for en, cn in zip(en_sents, translations)]

    return {
        "lesson_id": lesson_id,
        "title": content["title"],
        "question": content["question"],
        "sentences": sentences,
        "original_chinese": content["chinese_paragraph"],
        "review_issues": issues,
    }


def main():
    if len(sys.argv) < 3:
        print("用法: python fetch_nce_lessons.py <book> <start> [end]")
        print("示例: python fetch_nce_lessons.py 2 1 5")
        print("示例: python fetch_nce_lessons.py 3 11 60")
        sys.exit(1)

    book = int(sys.argv[1])
    start = int(sys.argv[2])
    end = int(sys.argv[3]) if len(sys.argv) > 3 else start

    if book not in BOOK_MAP:
        print(f"❌ 不支持第{book}册")
        sys.exit(1)

    cfg = BOOK_MAP[book]
    prefix = cfg["prefix"]
    output_dir = Path(__file__).parent.parent / "src" / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / cfg["output"]

    existing = {}
    if output_file.exists():
        with open(output_file) as f:
            data = json.load(f)
            for lesson in data.get("articles", data if isinstance(data, list) else []):
                lid = lesson.get("lesson_id", "")
                existing[lid] = lesson

    review_report = []

    for i in range(start, end + 1):
        lesson_id = f"{prefix}-{i:03d}"
        if lesson_id in existing:
            print(f"📖 {lesson_id}... ⏭️ 已存在")
            continue

        result = process_lesson(lesson_id, book)
        if result:
            existing[lesson_id] = result
            if result["review_issues"]:
                review_report.append({"lesson": lesson_id, "issues": result["review_issues"]})

            # Save incrementally after each lesson
            all_lessons = sorted(existing.values(), key=lambda x: x.get("lesson_id", ""))
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump({"articles": all_lessons}, f, ensure_ascii=False, indent=2)

    all_lessons = sorted(existing.values(), key=lambda x: x.get("lesson_id", ""))
    print(f"\n📁 共 {len(all_lessons)} 课 → {output_file}")

    if review_report:
        report_file = output_file.with_suffix(".review.json")
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(review_report, f, ensure_ascii=False, indent=2)
        total_issues = sum(len(r['issues']) for r in review_report)
        print(f"📋 审核: {len(review_report)}课有问题，共{total_issues}处需确认")


if __name__ == "__main__":
    main()
