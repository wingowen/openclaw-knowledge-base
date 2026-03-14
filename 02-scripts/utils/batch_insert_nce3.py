#!/usr/bin/env python3
"""
批量录入新概念英语第三册课程
"""
import json
import subprocess
import os
import sys
import time

def load_env():
    """加载环境变量"""
    env_file = '/root/.openclaw/workspace/.env.supabase'
    env_vars = {}
    with open(env_file) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                env_vars[key] = value
    return env_vars

def create_article(env, title, lesson_id):
    """创建文章"""
    url = f"{env['SUPABASE_URL']}/rest/v1/articles"
    headers = [
        '-H', f"apikey: {env['SUPABASE_SERVICE_ROLE_KEY']}",
        '-H', f"Authorization: Bearer {env['SUPABASE_SERVICE_ROLE_KEY']}",
        '-H', 'Content-Type: application/json',
        '-H', 'Prefer: return=representation'
    ]
    
    data = {
        'title': title,
        'description': f'新概念英语第三册 - {lesson_id}',
        'source_url': f'https://newconceptenglish.com/index.php?id={lesson_id}',
        'total_sentences': 0
    }
    
    result = subprocess.run(
        ['curl', '-4', '-s', '-X', 'POST', url] + headers +
        ['-d', json.dumps(data, ensure_ascii=False)],
        capture_output=True,
        text=True
    )
    return result.stdout

def link_article_tag(env, article_id, tag_id=6):
    """关联文章到标签"""
    url = f"{env['SUPABASE_URL']}/rest/v1/article_tags"
    headers = [
        '-H', f"apikey: {env['SUPABASE_SERVICE_ROLE_KEY']}",
        '-H', f"Authorization: Bearer {env['SUPABASE_SERVICE_ROLE_KEY']}",
        '-H', 'Content-Type: application/json',
        '-H', 'Prefer: return=representation'
    ]
    
    data = {
        'article_id': article_id,
        'tag_id': tag_id
    }
    
    result = subprocess.run(
        ['curl', '-4', '-s', '-X', 'POST', url] + headers +
        ['-d', json.dumps(data)],
        capture_output=True,
        text=True
    )
    return result.stdout

def insert_sentence(env, article_id, content, translation, sequence_order):
    """插入单个句子"""
    url = f"{env['SUPABASE_URL']}/rest/v1/sentences"
    headers = [
        '-H', f"apikey: {env['SUPABASE_SERVICE_ROLE_KEY']}",
        '-H', f"Authorization: Bearer {env['SUPABASE_SERVICE_ROLE_KEY']}",
        '-H', 'Content-Type: application/json',
        '-H', 'Prefer: return=representation'
    ]
    
    data = {
        'article_id': article_id,
        'content': content,
        'sequence_order': sequence_order,
        'is_active': True,
        'extensions': {
            'translation': translation
        }
    }
    
    result = subprocess.run(
        ['curl', '-4', '-s', '-X', 'POST', url] + headers +
        ['-d', json.dumps(data, ensure_ascii=False)],
        capture_output=True,
        text=True
    )
    return result.stdout

def update_article_sentence_count(env, article_id, count):
    """更新文章的句子总数"""
    url = f"{env['SUPABASE_URL']}/rest/v1/articles?id=eq.{article_id}"
    headers = [
        '-H', f"apikey: {env['SUPABASE_SERVICE_ROLE_KEY']}",
        '-H', f"Authorization: Bearer {env['SUPABASE_SERVICE_ROLE_KEY']}",
        '-H', 'Content-Type: application/json',
        '-H', 'Prefer: return=minimal'
    ]
    
    data = {'total_sentences': count}
    
    result = subprocess.run(
        ['curl', '-4', '-s', '-X', 'PATCH', url] + headers +
        ['-d', json.dumps(data)],
        capture_output=True,
        text=True
    )
    return result.stdout

def process_lesson(env, lesson_id):
    """处理单课：抓取 -> 创建文章 -> 录入句子"""
    print(f"\n{'='*60}")
    print(f"处理课程: {lesson_id}")
    print(f"{'='*60}")
    
    # 1. 抓取课程
    print("📥 抓取课程数据...")
    result = subprocess.run(
        ['python3', '/root/.openclaw/workspace/scripts/fetch_nce3_lesson.py', lesson_id],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ 抓取失败: {result.stderr}")
        return False
    
    # 2. 加载抓取的数据
    lesson_file = f'/root/.openclaw/workspace/scripts/lesson_{lesson_id}.json'
    with open(lesson_file, 'r', encoding='utf-8') as f:
        lesson = json.load(f)
    
    print(f"   标题: {lesson['title']}")
    print(f"   句子数: {len(lesson['english_sentences'])}")
    
    # 3. 创建文章
    print("📝 创建文章...")
    article_result = create_article(env, lesson['title'], lesson_id)
    try:
        article_data = json.loads(article_result)
        if isinstance(article_data, list) and len(article_data) > 0:
            article_id = article_data[0]['id']
            print(f"   ✓ Article ID: {article_id}")
        else:
            print(f"❌ 创建文章失败: {article_result[:200]}")
            return False
    except json.JSONDecodeError:
        print(f"❌ 解析文章响应失败: {article_result[:200]}")
        return False
    
    # 4. 关联标签
    print("🏷️  关联标签...")
    tag_result = link_article_tag(env, article_id)
    print(f"   ✓ 已关联到标签 id=6")
    
    # 5. 录入句子
    print(f"💾 录入 {len(lesson['english_sentences'])} 个句子...")
    success_count = 0
    for i, (en, zh) in enumerate(zip(lesson['english_sentences'], lesson['chinese_sentences']), 1):
        result = insert_sentence(env, article_id, en, zh, i)
        try:
            response = json.loads(result)
            if isinstance(response, list) and len(response) > 0:
                success_count += 1
            else:
                print(f"   ⚠️  句子 {i} 失败: {result[:100]}")
        except json.JSONDecodeError:
            print(f"   ⚠️  句子 {i} 解析错误: {result[:100]}")
    
    # 6. 更新句子总数
    update_article_sentence_count(env, article_id, success_count)
    
    print(f"✅ 完成 {lesson_id}: {success_count}/{len(lesson['english_sentences'])} 句")
    return True

def main():
    # 要录入的课程列表
    lessons = ['3-003', '3-004', '3-005', '3-006', '3-007', '3-008', '3-009', '3-010']
    
    # 加载环境变量
    env = load_env()
    
    print(f"开始批量录入 {len(lessons)} 课")
    
    completed = []
    failed = []
    
    for lesson_id in lessons:
        try:
            success = process_lesson(env, lesson_id)
            if success:
                completed.append(lesson_id)
            else:
                failed.append(lesson_id)
            # 避免请求过快
            time.sleep(1)
        except Exception as e:
            print(f"❌ {lesson_id} 异常: {e}")
            failed.append(lesson_id)
    
    print(f"\n{'='*60}")
    print("批量录入完成")
    print(f"✅ 成功: {len(completed)} 课 - {', '.join(completed)}")
    if failed:
        print(f"❌ 失败: {len(failed)} 课 - {', '.join(failed)}")

if __name__ == '__main__':
    main()
