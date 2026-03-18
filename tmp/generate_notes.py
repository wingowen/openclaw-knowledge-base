#!/usr/bin/env python3
"""Generate structured vocabulary notes from subtitle files.
Extracts English words and their Chinese definitions from teaching content.
"""

import re
import os
import sys

SUB_DIR = '/root/.openclaw/workspace/tmp/subtitles'
OUT_DIR = '/root/.openclaw/workspace/knowledge-base/06-english-learning/雅思词汇真经'

CHAPTERS = [
    ("10上", "第10章", "物品材料", "上", "BV1ZBzkYsEtV"),
    ("10下", "第10章", "物品材料", "下", "BV19uCqYCEHy"),
    ("11上", "第11章", "时尚潮流", "上", "BV1VMr1Y8ECZ"),
    ("11下", "第11章", "时尚潮流", "下", "BV1TDcQe9Eom"),
    ("12上", "第12章", "饮食健康", "上", "BV1bnwaeiEyu"),
    ("12下", "第12章", "饮食健康", "下", "BV1niFQegEXP"),
    ("13上", "第13章", "建筑场所", "上", "BV1LJNieeEbd"),
    ("13下", "第13章", "建筑场所", "下", "BV1cnADeVEEH"),
    ("14上", "第14章", "交通旅行", "上", "BV1f4XRYtEkF"),
    ("14下", "第14章", "交通旅行", "下", "BV1GnRpYcEGD"),
    ("15上", "第15章", "国家政府", "上", "BV1yJoSYaEEn"),
    ("15下", "第15章", "国家政府", "下", "BV1XnfKYfErp"),
    ("16上", "第16章", "社会经济", "上", "BV1RYowY7EvL"),
    ("16下", "第16章", "社会经济", "下", "BV17SGkzAE8W"),
    ("17上", "第17章", "法律法规", "上", "BV1Q2EEzBEBj"),
    ("17下", "第17章", "法律法规", "下", "BV1HKJAzyE7k"),
    ("18上", "第18章", "沙场争锋", "上", "BV1ebMAzzEXG"),
    ("18中", "第18章", "沙场争锋", "中", "BV1guK6zcEpd"),
    ("18下", "第18章", "沙场争锋", "下", "BV19z3qz6EMW"),
]


def get_teaching_lines(text):
    """Extract teaching content lines (skip English lyrics at beginning)."""
    lines = text.split('\n')
    result = []
    started = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        has_cn = bool(re.search(r'[\u4e00-\u9fff]', line))
        
        if not started:
            # Look for teaching start indicators
            if has_cn and any(kw in line for kw in [
                '大家好', '同学', '频道', '我们来', '一起看', '单词', 
                '下面', '首先', '第', '章', '进入', '开始'
            ]):
                started = True
        
        if started:
            result.append(line)
    
    return result


def extract_vocab_entries(lines):
    """Extract vocabulary entries from teaching lines.
    Returns list of dicts: {word, definition, example, mastery}
    """
    entries = []
    current_word = None
    current_def = []
    current_examples = []
    current_mastery = '认识'
    
    # Patterns to detect new word introduction
    word_intro_patterns = [
        r'(?:单词|词汇?|短语)\s*(?:是|叫|呢\s*是)?\s*([A-Za-z][A-Za-z\s\-\'\.]+)',
        r'([A-Za-z][A-Za-z\-\'\.]+)\s*(?:这个单词|这个词汇|指的是|表示|意思是|做名词|做动词)',
        r'(?:首先|下面|接下来|然后|接着|下面呢)\s*(?:是|来看|说)?\s*(?:[一两三四五六七八九十]+个)?\s*(?:单词)?\s*([A-Za-z][A-Za-z\-\'\.]+)',
        r'^([A-Z][a-z]+(?:\s+[a-z]+)*)\s*$',  # Word alone on a line
    ]
    
    # Patterns for definitions
    def_patterns = [
        r'指的是(.+)',
        r'表示(.+)',
        r'意思是(.+)',
        r'意思是说(.+)',
        r'做名词\s*指的是?(.+)',
        r'做动词\s*指的是?(.+)',
        r'做形容词\s*指的是?(.+)',
        r'呢\s*指的是?(.+)',
        r'就是(.+)',
    ]
    
    # Mastery patterns
    mastery_patterns = {
        '背会': r'背会|背下来|记住|必须记住|一定要记住|牢牢记住',
        '认识': r'认识|了解|知道|看看|看一下|简单',
        '了解': r'了解|不需要背|只需要知道|看看就行',
    }
    
    in_word_section = False
    raw_text = '\n'.join(lines)
    
    # Simple approach: find all English words mentioned with their context
    for i, line in enumerate(lines):
        # Check for mastery requirements
        for mastery, pattern in mastery_patterns.items():
            if re.search(pattern, line):
                current_mastery = mastery
        
        # Find English words in the line
        eng_words = re.findall(r'\b([A-Z][a-z]+(?:\s+[a-z]+)*)\b', line)
        if not eng_words:
            eng_words = re.findall(r'\b([a-z]{3,}(?:\s+[a-z]+)*)\b', line)
    
    # Better approach: parse line by line to find word-definition pairs
    return parse_teaching_content(lines)


def parse_teaching_content(lines):
    """Parse teaching content into vocabulary entries."""
    entries = []
    all_text = '\n'.join(lines)
    
    # Find all vocabulary teaching blocks
    # Pattern: English word followed by Chinese definition
    vocab_pattern = re.compile(
        r'(?:^|\n)\s*(?:首先|下面|接下来|然后|接着|下面呢|好的)?\s*'
        r'(?:[一二三四五六七八九十]+[个是]?\s*)?'
        r'(?:单词|词汇|短语)?\s*'
        r'([A-Za-z][A-Za-z\-\'\.\s]{1,40}?)\s*'
        r'(?:这个(?:单词|词汇)|指的是|表示|意思是|做(?:名词|动词|形容词)|呢\s*(?:是|指)|就是)',
        re.MULTILINE
    )
    
    # More targeted: find word-definition pairs
    # Split by potential new word markers
    blocks = re.split(
        r'(?:首先|下面|接下来|然后|接着|好的|好的那么|呢那我们|那么|好)\s*'
        r'(?:[一二三四五六七八九十]+个)?\s*(?:单词|词汇|短语|看看|说说)?\s*'
        r'(?:是|呢\s*是|呢\s*看)?',
        all_text
    )
    
    # Actually, let's just use a simpler line-by-line approach
    return extract_from_lines(lines)


def extract_from_lines(lines):
    """Line-by-line extraction of vocabulary."""
    entries = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Look for English word patterns
        # Pattern 1: "单词X" or "X这个单词"
        m = re.search(r'(?:单词|短语)\s*(?:是|叫|呢\s*是)?\s*([A-Za-z][A-Za-z\-\']+)', line)
        if not m:
            m = re.search(r'([A-Za-z][A-Za-z\-\']+)\s*(?:这个单词|这个短语|这个词汇)', line)
        if not m:
            m = re.search(r'([A-Za-z][A-Za-z\-\']+)\s*指的是', line)
        if not m:
            m = re.search(r'([A-Za-z][A-Za-z\-\']+)\s*表示', line)
        if not m:
            m = re.search(r'([A-Za-z][A-Za-z\-\']+)\s*意思是', line)
        if not m:
            m = re.search(r'([A-Za-z][A-Za-z\-\']+)\s*做(?:名词|动词|形容词)', line)
        
        if m:
            word = m.group(1).strip()
            # Skip very short or very long matches
            if 2 <= len(word) <= 40:
                # Collect definition from this and following lines
                context_lines = lines[max(0, i-1):min(len(lines), i+5)]
                context = ' '.join(context_lines)
                definition = extract_definition(context, word)
                example = extract_example(context, word)
                mastery = extract_mastery(context)
                
                entries.append({
                    'word': word,
                    'definition': definition,
                    'example': example,
                    'mastery': mastery,
                })
        
        i += 1
    
    return entries


def extract_definition(context, word):
    """Extract Chinese definition for a word from context."""
    # Remove the word itself from context for cleaner extraction
    patterns = [
        rf'{re.escape(word)}\s*(?:这个单词)?\s*(?:指的是?|表示|意思是?|就是)(.+?)(?:[。！？\n]|$)',
        rf'{re.escape(word)}\s*做(?:名词|动词|形容词)\s*(?:指的是?|表示)?(.+?)(?:[。！？\n]|$)',
        rf'(?:指的是?|表示|意思是?|就是)\s*(.+?)(?:{re.escape(word)}|[。！？\n]|$)',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, context)
        if m:
            defn = m.group(1).strip()
            # Clean up
            defn = re.sub(r'[嗯啊哈呢吧嘛了哦]', '', defn).strip()
            defn = re.sub(r'^\s*和\s*', '', defn).strip()
            if len(defn) > 2 and len(defn) < 50:
                return defn
    
    # Fallback: look for Chinese text near the word
    m = re.search(rf'{re.escape(word)}[^。！？\n]*?([\u4e00-\u9fff]{{2,20}})', context)
    if m:
        return m.group(1).strip()
    
    return ''


def extract_example(context, word):
    """Extract example or collocation."""
    patterns = [
        r'(?:例如|比如|比如说|像)(.+?)(?:[。！？\n]|$)',
        rf'{re.escape(word)}\s+(?:in|on|at|for|with|to|from|by)\s+([A-Za-z]+)',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, context)
        if m:
            return m.group(1).strip()[:80]
    return ''


def extract_mastery(context):
    """Extract mastery requirement from context."""
    if re.search(r'背会|背下来|记住|必须记住|一定要记住|牢牢记住', context):
        return '背会'
    if re.search(r'了解|不需要背|只需要知道|看看就行|看看就可以', context):
        return '了解'
    return '认识'


def extract_phrases(lines):
    """Extract important phrases."""
    phrases = []
    all_text = '\n'.join(lines)
    
    # Look for phrase patterns
    phrase_patterns = [
        r'短语\s*(?:是|叫|呢\s*是)?\s*([A-Za-z][A-Za-z\s\-\'\.]+(?:in|on|at|for|with|to|from|by|up|out|off|down)\s+[A-Za-z]+)',
        r'([A-Za-z]+\s+(?:in|on|at|for|with|to|from|by|up|out|off|down)\s+[A-Za-z]+)\s*指的是',
        r'([A-Za-z]+\s+(?:in|on|at|for|with|to|from|by|up|out|off|down)\s+[A-Za-z]+)\s*表示',
    ]
    
    for pattern in phrase_patterns:
        for m in re.finditer(pattern, all_text):
            phrase = m.group(1).strip()
            # Find definition
            ctx_start = max(0, m.start() - 50)
            ctx_end = min(len(all_text), m.end() + 200)
            ctx = all_text[ctx_start:ctx_end]
            definition = extract_definition(ctx, phrase)
            if phrase and len(phrase) > 5:
                phrases.append({'phrase': phrase, 'definition': definition})
    
    return phrases


def generate_markdown(label, ch, theme, part, bvid, entries, phrases):
    """Generate markdown output."""
    lines = []
    lines.append(f"# 雅思词汇真经｜{ch}｜{theme}（{part}）")
    lines.append("")
    lines.append(f"**视频**: https://www.bilibili.com/video/{bvid}/")
    lines.append(f"**章节**: {ch} | {theme} | {part}")
    lines.append("")
    lines.append("## 📚 词汇笔记")
    lines.append("")
    
    if entries:
        lines.append("| 单词 | 释义 | 例句/搭配 | 掌握要求 |")
        lines.append("|------|------|-----------|----------|")
        for e in entries:
            word = e['word']
            defn = e['definition'] or '-'
            example = e['example'] or '-'
            mastery = e['mastery']
            # Escape pipes in content
            word = word.replace('|', '\\|')
            defn = defn.replace('|', '\\|')
            example = example.replace('|', '\\|')
            lines.append(f"| {word} | {defn} | {example} | {mastery} |")
    else:
        lines.append("*（字幕内容不足，未能提取到有效词汇）*")
    
    if phrases:
        lines.append("")
        lines.append("### 重点短语")
        lines.append("")
        lines.append("| 短语 | 含义 |")
        lines.append("|------|------|")
        for p in phrases:
            phrase = p['phrase'].replace('|', '\\|')
            defn = p['definition'].replace('|', '\\|') or '-'
            lines.append(f"| {phrase} | {defn} |")
    
    lines.append("")
    return '\n'.join(lines)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    
    for label, ch, theme, part, bvid in CHAPTERS:
        sub_path = os.path.join(SUB_DIR, f"{label}.txt")
        if not os.path.exists(sub_path) or os.path.getsize(sub_path) == 0:
            print(f"⚠️ {label}: no subtitle file")
            continue
        
        with open(sub_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Extract teaching lines
        teaching_lines = get_teaching_lines(text)
        
        if len(teaching_lines) < 5:
            print(f"⚠️ {label}: too few teaching lines ({len(teaching_lines)})")
            continue
        
        # Extract vocabulary
        entries = extract_from_lines(teaching_lines)
        phrases = extract_phrases(teaching_lines)
        
        # Generate markdown
        md = generate_markdown(label, ch, theme, part, bvid, entries, phrases)
        
        # Write output
        filename = f"{ch}-{theme}-{part}.md"
        out_path = os.path.join(OUT_DIR, filename)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(md)
        
        print(f"✅ {label} → {filename}: {len(entries)} words, {len(phrases)} phrases")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
