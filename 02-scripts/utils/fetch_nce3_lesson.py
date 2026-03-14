#!/usr/bin/env python3
"""
抓取新概念英语第三册课程内容并切分句子
"""
import re
import subprocess
import json
import sys

def fetch_lesson(lesson_id):
    """抓取课程页面内容"""
    url = f"https://newconceptenglish.com/index.php?id={lesson_id}"
    result = subprocess.run(
        ['curl', '-4', '-s', url],
        capture_output=True,
        text=True
    )
    return result.stdout

def extract_content(html):
    """提取英文课文和中文翻译"""
    # 提取英文课文
    en_match = re.search(
        r'<div class="nce nce-lessons">.*?<h3[^>]*>.*?</h3>(.*?)</div>',
        html, re.DOTALL
    )
    english_text = ""
    if en_match:
        english_text = en_match.group(1)
        # 移除 HTML 标签
        english_text = re.sub(r'<span class="drop-cap-classic">([A-Z])</span>', r'\1', english_text)
        english_text = re.sub(r'<[^>]+>', '', english_text)
        english_text = re.sub(r'\s+', ' ', english_text).strip()
    
    # 提取中文翻译：稳健地提取整个 nce-fanyi 块（可能包含嵌套 div）
    def extract_div_block(html, start_class):
        """提取以 start_class 开头的 <div> 块，处理嵌套 div"""
        start_tag = f'<div class="{start_class}">'
        start_idx = html.find(start_tag)
        if start_idx == -1:
            return None
        start_idx += len(start_tag)
        
        # 从 start_idx 开始，查找匹配的闭合 </div>
        depth = 1
        i = start_idx
        while i < len(html) and depth > 0:
            if html[i:i+5] == '<div ':
                # 可能是一个嵌套 div 开始，需跳过标签直到 '>'
                depth += 1
                # 跳过直到 '>'
                while i < len(html) and html[i] != '>':
                    i += 1
                if i < len(html):
                    i += 1
            elif html[i:i+6] == '</div>':
                depth -= 1
                i += 6
            else:
                i += 1
        if depth == 0:
            end_idx = i
            return html[start_idx:end_idx-6]  # 不包含最后的 </div>
        else:
            return None
    
    fanyi_content = extract_div_block(html, 'nce nce-fanyi')
    chinese_text = ""
    title = ""
    if fanyi_content:
        # 提取中文标题（course-title-cn）
        title_match = re.search(
            r'<div class="course-title-cn[^>]*>.*?<p[^>]*>(.*?)</p>.*?</div>',
            fanyi_content, re.DOTALL
        )
        if title_match:
            title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
        
        # 移除 h3 标题（新概念英语－翻译）
        fanyi_content = re.sub(r'<h3[^>]*>.*?</h3>', '', fanyi_content, flags=re.DOTALL)
        # 移除 course-title-cn 块（避免混入内容）
        fanyi_content = re.sub(r'<div class="course-title-cn[^>]*>.*?</div>', '', fanyi_content, flags=re.DOTALL)
        
        # 清理剩余 HTML 标签，并规范化空白
        chinese_text = re.sub(r'<[^>]+>', '', fanyi_content)
        chinese_text = re.sub(r'\s+', ' ', chinese_text).strip()
    
    # 备用标题提取
    if not title:
        title_match = re.search(
            r'<div id="coursetitle">.*?<p[^>]*>(.*?)</p>',
            html, re.DOTALL
        )
        if title_match:
            title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
    
    return {
        'title': title,
        'english': english_text,
        'chinese': chinese_text
    }

def split_sentences(text, is_chinese=False):
    """按标点切分句子"""
    if is_chinese:
        # 中文处理：需要处理引号、书名号等成对符号，避免拆散引号内的内容
        
        # 1. 保护成对符号：引号“”、括号（）、[]、{}、书名号《》
        # 使用占位符，格式为 <<<SYM0>>> 等
        protected = text
        pairs = [
            ('“', '”'),  # 中文双引号
            ('‘', '’'),  # 中文单引号
            ('（', '）'),  # 中文括号
            ('【', '】'),  # 中文方括号/标注括号
            ('《', '》'),  # 书名号
        ]
        pair_map = {}
        counter = 0
        for open_sym, close_sym in pairs:
            # 查找配对的成对符号，用占位符替换整个配对区间
            pattern = re.escape(open_sym) + r'.*?' + re.escape(close_sym)
            for match in re.finditer(pattern, protected):
                placeholder = f'<<<SYM{counter}>>>'
                pair_map[placeholder] = match.group(0)
                protected = protected.replace(match.group(0), placeholder)
                counter += 1
        
        # 2. 按句子结束标点切分：。 ？ ！ （注意保留分隔符）
        # 使用正向后视断言，在结束标点后切分
        raw_sentences = re.split(r'(?<=[。？！])\s*', protected)
        
        # 3. 还原占位符
        sentences = []
        for s in raw_sentences:
            for placeholder, original in pair_map.items():
                s = s.replace(placeholder, original)
            if s.strip():
                sentences.append(s.strip())
        
        return sentences
    else:
        # 英文切分：
        # 1. 先保护常见的缩写（把整个缩写替换成占位符，保留原始形式）
        protected = text
        abbreviations = ['B.C.', 'A.D.', 'B.C.E.', 'C.E.', 'Mr.', 'Mrs.', 'Ms.', 'Dr.', 'Prof.', 'Sr.', 'Jr.', 'vs.', 'etc.', 'i.e.', 'e.g.', 'U.S.', 'U.K.']
        abbr_map = {}
        for i, abbr in enumerate(abbreviations):
            placeholder = f'<<<ABBR{i}>>>'
            abbr_map[placeholder] = abbr
            protected = protected.replace(abbr, placeholder)
        
        # 2. 规范化空格（确保句号/问号/感叹号后有空格）
        protected = re.sub(r'([.!?])(?=[A-Z])', r'\1 ', protected)
        
        # 3. 确保占位符后有空格（如果没有）
        protected = re.sub(r'(<<<ABBR\d+>>>)(?=\S)', r'\1 ', protected)
        
        # 4. 在占位符后面添加临时标记，用于区分句子边界
        # 如果占位符后面是大写字母开头的新句子，标记为可切分
        protected = re.sub(r'(<<<ABBR\d+>>>)\s+(?=[A-Z][a-z])', r'\1<<<SENTENCE_END>>> ', protected)
        
        # 5. 按 . ? ! 或 <<<SENTENCE_END>>> 切分
        protected = protected.replace('<<<SENTENCE_END>>>', '|||END|||')
        sentences = re.split(r'(?<=[.!?])\s+|\s*\|\|\|END\|\|\|\s*', protected)
        
        # 6. 还原缩写
        for placeholder, abbr in abbr_map.items():
            sentences = [s.replace(placeholder, abbr) for s in sentences]
        sentences = [s.strip() for s in sentences]
    # 过滤空句子
    sentences = [s for s in sentences if s.strip()]
    return sentences

def main():
    lesson_id = sys.argv[1] if len(sys.argv) > 1 else "3-001"
    
    print(f"抓取课程: {lesson_id}")
    html = fetch_lesson(lesson_id)
    
    content = extract_content(html)
    print(f"\n=== 标题: {content['title']} ===\n")
    
    # 切分英文句子
    en_sentences = split_sentences(content['english'], is_chinese=False)
    print(f"英文句子数: {len(en_sentences)}\n")
    
    # 切分中文句子
    zh_sentences = split_sentences(content['chinese'], is_chinese=True)
    print(f"中文句子数: {len(zh_sentences)}\n")
    
    # 输出 JSON 供后续处理
    output = {
        'lesson_id': lesson_id,
        'title': content['title'],
        'english_sentences': en_sentences,
        'chinese_sentences': zh_sentences,
        'english_raw': content['english'],
        'chinese_raw': content['chinese']
    }
    
    print("=== 英文句子 ===")
    for i, s in enumerate(en_sentences, 1):
        print(f"{i}. {s}")
    
    print("\n=== 中文句子 ===")
    for i, s in enumerate(zh_sentences, 1):
        print(f"{i}. {s}")
    
    # 保存到文件
    with open(f'/root/.openclaw/workspace/scripts/lesson_{lesson_id}.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n已保存到: scripts/lesson_{lesson_id}.json")

if __name__ == '__main__':
    main()
