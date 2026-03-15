#!/usr/bin/env python3
"""同步本地 JSON 新概念二数据到 Supabase（更新句子+翻译）"""
import json
import os
import sys
import time
import urllib.request

SUPABASE_URL = "https://gtcnjqeloworstrimcsr.supabase.co"
KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
if not KEY:
    # Try loading from .env
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env.supabase")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("SUPABASE_SERVICE_ROLE_KEY="):
                    KEY = line.split("=", 1)[1].strip()
                    break

if not KEY:
    print("❌ 未找到 SUPABASE_SERVICE_ROLE_KEY")
    sys.exit(1)

HEADERS = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

JSON_PATH = os.path.join(os.path.dirname(__file__), "..", "src", "data", "new-concept-2.json")
TAG_ID = 7  # 新概念英语第二册


def api(method, path, data=None):
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=HEADERS, method=method)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def get_existing_articles():
    """Get existing NCE2 articles from Supabase"""
    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/articles?select=id,title&title=like.2-*",
        headers={"apikey": KEY, "Authorization": f"Bearer {KEY}"}
    )
    with urllib.request.urlopen(req) as r:
        return {a["title"][:5]: a["id"] for a in json.loads(r.read())}


def count_sentences(article_id):
    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/sentences?select=id&article_id=eq.{article_id}",
        headers={"apikey": KEY, "Authorization": f"Bearer {KEY}", "Prefer": "count=exact"}
    )
    with urllib.request.urlopen(req) as r:
        rh = r.headers.get('content-range', '0-0/0')
        return int(rh.split('/')[-1])


def delete_sentences(article_id):
    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/sentences?article_id=eq.{article_id}",
        headers={"apikey": KEY, "Authorization": f"Bearer {KEY}"},
        method="DELETE"
    )
    with urllib.request.urlopen(req) as r:
        pass


def insert_sentences(article_id, sentences):
    """Insert sentences in batches"""
    for i in range(0, len(sentences), 20):
        batch = sentences[i:i+20]
        payload = [
            {
                "article_id": article_id,
                "content": s["text"],
                "sequence_order": j + 1,
                "is_active": True,
                "extensions": {"translation": s.get("translation", "")}
            }
            for j, s in enumerate(batch, start=i)
        ]
        try:
            api("POST", "sentences", payload)
        except Exception as e:
            print(f"  ❌ 插入句子批次 {i}-{i+len(batch)}: {e}")
            return False
    return True


def main():
    with open(JSON_PATH) as f:
        data = json.load(f)
    
    articles = data["articles"]
    print(f"📂 本地 JSON: {len(articles)} 课")
    
    existing = get_existing_articles()
    print(f"📂 Supabase: {len(existing)} 篇文章")
    
    stats = {"created": 0, "updated": 0, "skipped": 0, "failed": 0}
    
    for i, article in enumerate(articles):
        lid = article["lesson_id"]
        title = article.get("title", "")
        sentences = article.get("sentences", [])
        en_count = len(sentences)
        cn_count = sum(1 for s in sentences if s.get("translation", ""))
        
        display_title = f"{lid} {title}" if title else lid
        
        if lid in existing:
            aid = existing[lid]
            existing_sents = count_sentences(aid)
            
            # Check if update needed
            if existing_sents == en_count and existing_sents > 0:
                print(f"⏭️ {display_title} ({existing_sents}句)")
                stats["skipped"] += 1
                continue
            
            # Need to re-import sentences
            print(f"🔄 {display_title}: {existing_sents}句 → {en_count}句", end=" ", flush=True)
            try:
                delete_sentences(aid)
                time.sleep(0.2)
                if insert_sentences(aid, sentences):
                    print("✅")
                    stats["updated"] += 1
                else:
                    stats["failed"] += 1
            except Exception as e:
                print(f"❌ {e}")
                stats["failed"] += 1
        else:
            # Create new article
            print(f"➕ {display_title}", end=" ", flush=True)
            try:
                result = api("POST", "articles", {
                    "title": display_title,
                    "description": f"新概念英语第二册 {lid}",
                    "source_url": f"https://newconceptenglish.com/index.php?id={lid}",
                    "total_sentences": en_count
                })
                aid = result[0]["id"]
                time.sleep(0.2)
                
                if insert_sentences(aid, sentences):
                    # Associate tag
                    try:
                        api("POST", "article_tags", {"article_id": aid, "tag_id": TAG_ID})
                    except:
                        pass
                    print("✅")
                    stats["created"] += 1
                else:
                    stats["failed"] += 1
            except Exception as e:
                print(f"❌ {e}")
                stats["failed"] += 1
        
        time.sleep(0.3)
    
    print(f"\n📊 完成! ➕{stats['created']} 🔄{stats['updated']} ⏭️{stats['skipped']} ❌{stats['failed']}")


if __name__ == "__main__":
    main()
