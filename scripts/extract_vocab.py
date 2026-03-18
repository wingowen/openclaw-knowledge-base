#!/usr/bin/env python3
"""
雅思词汇提取脚本 - 从B站字幕中提取结构化词汇笔记
用法: python3 extract_vocab.py <subtitle_file> <chapter_name> <bv_id> <output_file>
"""
import sys
import re
import os

def split_into_chunks(text, max_lines=80):
    """将字幕按行数分块"""
    lines = text.split('\n')
    chunks = []
    for i in range(0, len(lines), max_lines):
        chunks.append('\n'.join(lines[i:i+max_lines]))
    return chunks

def extract_words_from_chunk(chunk):
    """从一块字幕中提取单词和释义"""
    words = []
    lines = chunk.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 跳过歌词和非教学内容
        if line.startswith('♪') or line.startswith('['):
            i += 1
            continue
            
        # 匹配 "下面是XXX" 或 "好下面是XXX" 或 "下面是XXX这个单词" 
        m = re.match(r'^(?:好|嗯|那|然后)?(?:下面[是的是]*|首先来看[第]?[一个]*单词?)\s*([a-zA-Z]+(?:\s+[a-zA-Z]+)?)', line)
        if not m:
            # 也匹配 "XXX这个单词" 或 "XXX指的是" 或 "XXX作为动词"
            m = re.match(r'^([a-zA-Z]+)(?:这个单词|这个[呢]?(?:作为|做|指的是|表示|意思是))', line)
        if not m:
            # 匹配 "XXX指的是" at start
            m = re.match(r'^([a-zA-Z]{3,})\s*(?:指的是|意思是|可以表示|表示)', line)
        
        if m:
            word = m.group(1).strip().lower()
            # 清理单词（去掉末尾的 r a 等单独字母）
            word = re.sub(r'\s+[a-z]$', '', word).strip()
            # 过滤太短、太长、常见词和非英文
            stopwords = {'the', 'and', 'for', 'that', 'this', 'with', 'you', 'are', 'but', 'not', 'can', 'has', 'have', 'was', 'were', 'been', 'will', 'would', 'could', 'should', 'may', 'might', 'shall', 'must', 'need', 'dare', 'ought', 'used', 'able', 'like', 'just', 'don', 'get', 'got', 'let', 'say', 'said', 'also', 'very', 'much', 'more', 'some', 'about', 'into', 'over', 'such', 'than', 'them', 'then', 'only', 'other', 'here', 'there', 'what', 'when', 'where', 'which', 'while', 'who', 'how'}
            if 2 <= len(word) <= 20 and word not in stopwords and re.match(r'^[a-z]+$', word):
                # 找释义 - 在接下来的几行中找 "指的是/意思是"
                definition = ""
                for j in range(i, min(i+8, len(lines))):
                    dl = lines[j].strip()
                    dm = re.search(r'(?:指的是|意思是|表示|可以表示|也可以表示|也可以做)(.+?)(?:$|啊|嗯|哈|吧|啦|哦|呢)', dl)
                    if dm:
                        def_text = dm.group(1).strip()
                        # 清理字幕碎片和口水话
                        for junk in ['就记一个字儿', '就记', '大家把它记下来', '大家把它', '就可以了', '能明白吗', '大家去理解', '咱们说', '你看', '同学们', '背会', '就是', '其实就是', '这个', '我们说', '你', '咱们']:
                            def_text = def_text.replace(junk, '')
                        def_text = def_text.strip(' ，。,. ')
                        # 过滤无效释义
                        bad_defs = ['动词', '名词', '形容词', '副词', '介词', '下面', '好下面', '下面的是', '这个单词', '大家']
                        if def_text and not def_text.startswith('下面是') and def_text not in bad_defs and len(def_text) > 2 and len(def_text) < 50:
                            definition = def_text
                            break
                
                if definition:
                    words.append({
                        'word': word,
                        'definition': definition,
                        'raw_line': line
                    })
        i += 1
    
    return words

def deduplicate(words):
    """去重，保留释义最长的版本"""
    seen = {}
    for w in words:
        key = w['word'].lower()
        if key not in seen or len(w['definition']) > len(seen[key]['definition']):
            seen[key] = w
    return list(seen.values())

def generate_markdown(words, chapter_name, bv_id, chapter_num, theme, part):
    """生成Markdown格式的词汇笔记"""
    video_url = f"https://www.bilibili.com/video/{bv_id}/"
    
    md = f"""# 雅思词汇真经｜第{chapter_num}章｜{theme}（{part}）

**视频**: {video_url}
**章节**: 第{chapter_num}章 | {theme} | {part}

## 📚 词汇笔记

### 词汇列表

| 单词 | 释义 | 掌握要求 |
|------|------|----------|
"""
    for w in words:
        md += f"| {w['word']} | {w['definition']} | 📖 认识 |\n"
    
    return md

def main():
    if len(sys.argv) < 5:
        print("Usage: python3 extract_vocab.py <subtitle_file> <chapter_num> <theme> <part> <bv_id> <output_file>")
        print("Example: python3 extract_vocab.py tmp/subtitles/10上.txt 10 物品材料 上 BV1ZBzkYsEtV output.md")
        sys.exit(1)
    
    sub_file = sys.argv[1]
    chapter_num = sys.argv[2]
    theme = sys.argv[3]
    part = sys.argv[4]
    bv_id = sys.argv[5]
    output_file = sys.argv[6] if len(sys.argv) > 6 else None
    
    if not os.path.exists(sub_file):
        print(f"Error: {sub_file} not found")
        sys.exit(1)
    
    with open(sub_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"[*] Processing {sub_file} ({len(content)} chars)...", file=sys.stderr)
    
    # 分块处理
    chunks = split_into_chunks(content, max_lines=80)
    print(f"[*] Split into {len(chunks)} chunks", file=sys.stderr)
    
    all_words = []
    for idx, chunk in enumerate(chunks):
        words = extract_words_from_chunk(chunk)
        if words:
            print(f"  Chunk {idx+1}: found {len(words)} words", file=sys.stderr)
            all_words.extend(words)
    
    # 去重
    unique_words = deduplicate(all_words)
    print(f"[*] Total unique words: {len(unique_words)}", file=sys.stderr)
    
    if not unique_words:
        print("[!] No words extracted!", file=sys.stderr)
        sys.exit(1)
    
    # 生成 markdown
    md = generate_markdown(unique_words, "", bv_id, chapter_num, theme, part)
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md)
        print(f"[*] Written to {output_file}", file=sys.stderr)
    else:
        print(md)

if __name__ == '__main__':
    main()
