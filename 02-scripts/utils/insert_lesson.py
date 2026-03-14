#!/usr/bin/env python3
"""
将课程句子录入 Supabase 数据库
"""
import json
import subprocess
import os
import sys

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

def insert_sentence(env, article_id, content, translation, sequence_order):
    """插入单个句子到数据库"""
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

def main():
    lesson_file = sys.argv[1] if len(sys.argv) > 1 else 'lesson_3-001.json'
    article_id = sys.argv[2] if len(sys.argv) > 2 else '7'
    
    # 加载环境变量
    env = load_env()
    
    # 加载课程数据
    with open(f'/root/.openclaw/workspace/scripts/{lesson_file}', 'r', encoding='utf-8') as f:
        lesson = json.load(f)
    
    print(f"开始录入: {lesson['lesson_id']} - {lesson['title']}")
    print(f"Article ID: {article_id}")
    print(f"句子数: {len(lesson['english_sentences'])}")
    print()
    
    # 录入每个句子
    success_count = 0
    for i, (en, zh) in enumerate(zip(lesson['english_sentences'], lesson['chinese_sentences']), 1):
        print(f"[{i}/{len(lesson['english_sentences'])}] 录入中...")
        result = insert_sentence(env, int(article_id), en, zh, i)
        
        try:
            response = json.loads(result)
            if isinstance(response, list) and len(response) > 0:
                success_count += 1
                print(f"  ✓ ID: {response[0]['id']}")
            else:
                print(f"  ✗ 错误: {result[:100]}")
        except json.JSONDecodeError:
            print(f"  ✗ 解析错误: {result[:100]}")
    
    print(f"\n完成！成功: {success_count}/{len(lesson['english_sentences'])}")

if __name__ == '__main__':
    main()
