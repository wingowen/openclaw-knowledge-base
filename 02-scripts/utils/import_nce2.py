#!/usr/bin/env python3
"""
批量导入新概念英语第二册到 Supabase
"""
import os
import sys
import json
import subprocess
import time
import requests

# Supabase 配置
SUPABASE_URL = None
SUPABASE_SERVICE_ROLE_KEY = None
SUPABASE_ANON_KEY = None

def load_env():
    global SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_ANON_KEY
    # 使用工作区根目录的 .env.supabase
    env_file = '/root/.openclaw/workspace/.env.supabase'
    env_vars = {}
    with open(env_file) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                env_vars[key] = value
    SUPABASE_URL = env_vars['SUPABASE_URL']
    SUPABASE_SERVICE_ROLE_KEY = env_vars['SUPABASE_SERVICE_ROLE_KEY']
    SUPABASE_ANON_KEY = env_vars['SUPABASE_ANON_KEY']
    return env_vars

def fetch_lesson(lesson_id):
    """调用 fetch_nce3_lesson.py 抓取课程"""
    script = os.path.join(os.path.dirname(__file__), 'fetch_nce3_lesson.py')
    result = subprocess.run(
        ['python3', script, lesson_id],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(script)
    )
    if result.returncode != 0:
        raise Exception(f"Fetch failed: {result.stderr}")
    json_file = os.path.join(os.path.dirname(script), f'lesson_{lesson_id}.json')
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def supabase_headers(use_service_role=True):
    if use_service_role:
        return {
            'apikey': SUPABASE_SERVICE_ROLE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
    else:
        return {
            'apikey': SUPABASE_ANON_KEY,
            'Content-Type': 'application/json'
        }

def get_tag_id(tag_name):
    """获取或创建标签"""
    url = f"{SUPABASE_URL}/rest/v1/tags"
    params = f"name=eq.{tag_name}"
    resp = requests.get(url, headers=supabase_headers(use_service_role=True), params=params)
    resp.raise_for_status()
    tags = resp.json()
    if tags:
        return tags[0]['id']
    else:
        # Create tag
        color = '#DC2626' if tag_name == '新概念英语第二册' else '#000000'
        resp = requests.post(url, headers=supabase_headers(use_service_role=True),
                             json={'name': tag_name, 'color': color})
        resp.raise_for_status()
        return resp.json()[0]['id']

def article_exists(title):
    """检查文章是否已存在"""
    url = f"{SUPABASE_URL}/rest/v1/articles"
    params = f"title=eq.{title}"
    resp = requests.get(url, headers=supabase_headers(use_service_role=True), params=params)
    resp.raise_for_status()
    return len(resp.json()) > 0

def create_article(title, source_url, total_sentences):
    """创建文章"""
    url = f"{SUPABASE_URL}/rest/v1/articles"
    data = {
        'title': title,
        'source_url': source_url,
        'total_sentences': total_sentences
    }
    resp = requests.post(url, headers=supabase_headers(use_service_role=True), json=data)
    resp.raise_for_status()
    return resp.json()[0]['id']

def insert_sentences_batch(article_id, english_sentences, chinese_paragraphs):
    """批量插入句子。
    英文句子列表和中文段落列表可能长度不同，我们将英文句子分组映射到中文段落。
    """
    url = f"{SUPABASE_URL}/rest/v1/sentences"
    
    # 简单的分段策略：将英文句子大致等分为 len(chinese_paragraphs) 组
    # 每组对应一个中文段落
    n_zh = len(chinese_paragraphs)
    n_en = len(english_sentences)
    if n_zh == 0:
        print("  Warning: no Chinese paragraphs, skipping sentences.")
        return 0
    if n_zh >= n_en:
        # 中文段落不少于英文句子，可以一对一（或部分段落对应一句）
        en_groups = [[en] for en in english_sentences]
        zh_groups = chinese_paragraphs[:len(en_groups)]
        # 如果中文段落更多，多余的丢弃
    else:
        # 中文段落少于英文句子，需要将英文句子分组
        # 计算每组的大小（尽可能均匀）
        base = n_en // n_zh
        extra = n_en % n_zh
        en_groups = []
        idx = 0
        for i in range(n_zh):
            size = base + (1 if i < extra else 0)
            group = english_sentences[idx:idx+size]
            en_groups.append(group)
            idx += size
        zh_groups = chinese_paragraphs
    
    assert len(en_groups) == len(zh_groups) == n_zh
    
    batch = []
    for grp_idx, (en_grp, zh_text) in enumerate(zip(en_groups, zh_groups), 1):
        # 每组内多个英文句子合并为一个翻译？
        # 不，我们仍然为每个英文句子创建独立记录，但翻译字段使用同一个段落翻译
        for en_sentence in en_grp:
            batch.append({
                'article_id': article_id,
                'content': en_sentence,
                'sequence_order': len(batch) + 1,
                'is_active': True,
                'extensions': {'translation': zh_text}
            })
    
    resp = requests.post(url, headers=supabase_headers(use_service_role=True), json=batch)
    resp.raise_for_status()
    return len(resp.json())

def link_article_tag(article_id, tag_id):
    """关联文章和标签"""
    url = f"{SUPABASE_URL}/rest/v1/article_tags"
    data = {'article_id': article_id, 'tag_id': tag_id}
    resp = requests.post(url, headers=supabase_headers(use_service_role=True), json=data)
    if resp.status_code not in (200, 201):
        # Might already exist, ignore
        return False
    return True

def main():
    load_env()
    tag_name = '新概念英语第二册'
    tag_id = get_tag_id(tag_name)
    print(f"Tag '{tag_name}' id: {tag_id}")

    total_lessons = 96
    start_lesson = 1
    end_lesson = 96

    for i in range(start_lesson, end_lesson + 1):
        lesson_id = f"2-{i:03d}"
        try:
            # 检查是否已存在
            title_guess = f"{lesson_id}"  # 我们不知道确切标题，先抓取
            data = fetch_lesson(lesson_id)
            eng_title = data.get('title', '') or ''
            # 优先使用英文标题（从页面上抓取的）
            article_title = f"{lesson_id} {eng_title}" if eng_title else lesson_id
            # 如果按标题检查已存在，跳过
            if article_exists(article_title):
                print(f"[{i}/{total_lessons}] {lesson_id} already exists, skipping.")
                continue

            # 创建文章
            source_url = f"https://newconceptenglish.com/index.php?id={lesson_id}"
            article_id = create_article(article_title, source_url, len(data['english_sentences']))
            print(f"[{i}/{total_lessons}] Created article {article_id}: {article_title}")

            # 插入句子（支持分段映射）
            inserted = insert_sentences_batch(article_id, data['english_sentences'], data['chinese_sentences'])
            print(f"  Inserted {inserted} sentences (English {len(data['english_sentences'])} × Chinese {len(data['chinese_sentences'])} paragraphs).")

            # 关联标签
            link_article_tag(article_id, tag_id)
            print(f"  Linked to tag {tag_name}")

            # 每5课（或最后一课）发送一次通知（这里仅打印，实际通知由调用者处理）
            if i % 5 == 0 or i == end_lesson:
                print(f"PROGRESS: {i}/{total_lessons} lessons imported.")

            time.sleep(0.5)  # 礼貌延迟

        except Exception as e:
            print(f"ERROR: Lesson {lesson_id} failed: {e}")
            continue

    print("All done!")

if __name__ == '__main__':
    main()
