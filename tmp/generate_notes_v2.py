#!/usr/bin/env python3
"""Improved vocabulary note generator from Bilibili subtitles.
Better word extraction, clean definitions, and mastery detection.
"""

import re
import os
import json

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

# Filler/stop words to ignore
STOP_WORDS = {
    'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had',
    'her', 'was', 'one', 'our', 'out', 'has', 'his', 'how', 'its', 'may',
    'new', 'now', 'old', 'see', 'way', 'who', 'did', 'get', 'let', 'say',
    'she', 'too', 'use', 'come', 'make', 'like', 'just', 'know', 'take',
    'into', 'year', 'your', 'good', 'some', 'could', 'them', 'than',
    'been', 'call', 'find', 'long', 'look', 'made', 'many', 'over',
    'such', 'that', 'this', 'what', 'when', 'with', 'have', 'from',
    'they', 'been', 'said', 'each', 'which', 'their', 'word', 'will',
    'about', 'other', 'many', 'then', 'them', 'these', 'would', 'write',
    'like', 'number', 'way', 'could', 'people', 'come', 'first', 'also',
    'after', 'back', 'only', 'very', 'well', 'even', 'want', 'because',
    'any', 'these', 'give', 'day', 'most', 'great', 'think', 'help',
    'through', 'much', 'before', 'line', 'right', 'mean', 'old', 'same',
    'tell', 'does', 'three', 'must', 'high', 'home', 'read', 'hand',
    'here', 'should', 'still', 'between', 'never', 'under', 'last',
    'might', 'while', 'place', 'again', 'where', 'little', 'world',
    'every', 'begin', 'life', 'always', 'those', 'both', 'often',
    'being', 'another', 'keep', 'play', 'turn', 'point', 'small',
    'follow', 'house', 'live', 'learn', 'next', 'hard', 'open',
    'example', 'begin', 'seem', 'need', 'large', 'group', 'change',
    'play', 'move', 'thing', 'kind', 'four', 'head', 'far', 'black',
    'long', 'white', 'children', 'important', 'until', 'side',
    'something', 'without', 'however', 'system', 'set', 'put',
    'end', 'why', 'try', 'against', 'asked', 'men', 'different',
    'called', 'going', 'looked', 'few', 'away', 'second', 'enough',
    'above', 'name', 'water', 'own', 'found', 'study', 'yet',
    'word', 'between', 'keep', 'start', 'might', 'city', 'tree',
    'cross', 'hard', 'start', 'story', 'saw', 'far', 'sea', 'left',
    'late', 'run', 'don', 'while', 'press', 'close', 'night',
    'real', 'almost', 'let', 'face', 'below', 'girl', 'gave',
    'later', 'since', 'become', 'turn', 'move', 'ship', 'answer',
    'need', 'sure', 'top', 'front', 'young', 'ask', 'miss', 'show',
    'became', 'road', 'several', 'during', 'best', 'once', 'high',
    'along', 'hold', 'land', 'fast', 'five', 'walk', 'grow', 'took',
    'eat', 'short', 'north', 'song', 'leave', 'color', 'sun', 'fish',
    'area', 'mark', 'dog', 'horse', 'bird', 'problem', 'complete',
    'room', 'knew', 'since', 'ever', 'piece', 'told', 'usually',
    'didn', 'friends', 'easy', 'red', 'door', 'finally', 'eggs',
    'already', 'lost', 'blue', 'money', 'outside', 'stand', 'snow',
    'voice', 'round', 'power', 'walked', 'cold', 'second', 'dark',
    'half', 'hour', 'class', 'fish', 'south', 'deep', 'north',
    'rest', 'carry', 'rock', 'anything', 'hour', 'paper', 'heart',
    'inside', 'ground', 'ago', 'town', 'build', 'less', 'family',
    'music', 'river', 'whole', 'story', 'times', 'today', 'care',
    'moon', 'strong', 'morning', 'south', 'four', 'child', 'ten',
    'body', 'measure', 'better', 'best', 'hour', 'measure', 'table',
    'early', 'nothing', 'though', 'book', 'eye', 'thought', 'under',
    'story', 'product', 'sure', 'sometimes', 'dry', 'wonder',
    'laughed', 'gone', 'word', 'feel', 'bring', 'quick', 'full',
    'seem', 'talk', 'government', 'please', 'gave', 'try', 'small',
    'country', 'plant', 'father', 'known', 'important', 'earth',
    'father', 'school', 'study', 'light', 'read', 'number',
    'always', 'together', 'watch', 'white', 'later', 'really',
    'almost', 'sentence', 'something', 'thought', 'turn', 'young',
    'idea', 'fish', 'enough', 'head', 'between', 'never', 'next',
    'hard', 'open', 'example', 'begin', 'seem', 'need', 'state',
    'speak', 'clear', 'turn', 'home', 'move', 'try', 'kind',
}

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
            if has_cn and any(kw in line for kw in [
                '大家好', '同学', '频道', '我们来', '一起看', '单词', 
                '下面', '首先', '进入', '开始讲', '来看', '第',
            ]):
                started = True
        
        if started:
            result.append(line)
    
    return result


def clean_chinese_text(text):
    """Clean Chinese text, removing filler words."""
    # Remove common filler words
    text = re.sub(r'[嗯啊哈呢吧嘛哦了诶]+', '', text)
    text = re.sub(r'^\s*和\s*', '', text)
    text = re.sub(r'^\s*那么\s*', '', text)
    text = re.sub(r'^\s*然后\s*', '', text)
    text = re.sub(r'^\s*就是\s*', '', text)
    text = re.sub(r'^\s*指的是?\s*', '', text)
    text = re.sub(r'^\s*表示\s*', '', text)
    text = text.strip()
    return text


def is_valid_word(word):
    """Check if a string is a valid English word to include."""
    word = word.strip()
    if len(word) < 2 or len(word) > 30:
        return False
    if not re.match(r'^[A-Za-z][A-Za-z\-\'\.]*$', word):
        return False
    if word.lower() in STOP_WORDS:
        return False
    if re.match(r'^[A-Z]{2,}$', word) and len(word) > 8:
        return False  # Long all-caps is probably not a real word
    return True


def extract_vocab_from_lines(lines):
    """Extract vocabulary entries from teaching lines.
    Returns list of dicts with word, definition, example, mastery.
    """
    entries = []
    seen_words = set()
    
    # Join all lines for context
    full_text = '\n'.join(lines)
    
    # Pattern groups for finding words and their definitions
    # Group 1: word introduction patterns
    patterns = [
        # "单词economy" or "单词是economy"
        (r'单词\s*(?:是|叫|呢\s*是|这个)?\s*\n?\s*([A-Za-z][A-Za-z\-\'\.]{1,25})',
         'word_intro'),
        # "economy这个单词"
        (r'([A-Za-z][A-Za-z\-\'\.]{1,25})\s*这个(?:单词|词汇|短语)',
         'word_suffix'),
        # "短语是trade in"
        (r'短语\s*(?:是|叫|呢\s*是)?\s*\n?\s*([A-Za-z][A-Za-z\s\-\'\.]{2,30})',
         'phrase_intro'),
        # "首先第一个单词economy"
        (r'(?:首先|下面|接下来|接着|好的|好)\s*(?:[一二三四五六七八九十]+个?)?\s*(?:单词|词汇|短语)?\s*(?:是|呢\s*是)?\s*\n?\s*([A-Za-z][A-Za-z\-\'\.]{1,25})',
         'seq_intro'),
        # "下面呢是market"
        (r'下面\s*呢?\s*是\s*\n?\s*([A-Za-z][A-Za-z\-\'\.]{1,25})',
         'below_intro'),
        # "看下economy" or "看一下economy"
        (r'看(?:一下)?\s*\n?\s*([A-Za-z][A-Za-z\-\'\.]{1,25})',
         'look_intro'),
    ]
    
    for pattern, ptype in patterns:
        for m in re.finditer(pattern, full_text, re.IGNORECASE):
            word = m.group(1).strip()
            
            # For phrase patterns, keep multi-word
            if ptype != 'phrase_intro' and ' ' in word:
                word = word.split()[0]
            
            # Normalize
            word_lower = word.lower()
            
            if not is_valid_word(word):
                continue
            if word_lower in seen_words:
                continue
            
            # Get context around the match
            start = max(0, m.start() - 100)
            end = min(len(full_text), m.end() + 300)
            context = full_text[start:end]
            
            # Extract definition
            definition = extract_definition_v2(context, word)
            if not definition:
                continue
            
            # Extract example
            example = extract_example_v2(context, word)
            
            # Extract mastery
            mastery = extract_mastery_v2(context, word)
            
            seen_words.add(word_lower)
            entries.append({
                'word': word,
                'definition': definition,
                'example': example,
                'mastery': mastery,
            })
    
    return entries


def extract_definition_v2(context, word):
    """Extract clean Chinese definition."""
    word_esc = re.escape(word)
    
    # Look for definition patterns after the word
    patterns = [
        # "指的是XXX"
        rf'{word_esc}\s*(?:这个单词)?\s*(?:指的是?|表示|意思是?|翻译成|可以翻译成)\s*([\u4e00-\u9fff][\u4e00-\u9fff\w\s，。、]{1,30})',
        # "做名词指的是XXX"
        rf'{word_esc}\s*做\s*(?:名词|动词|形容词|副词)\s*(?:指的是?|表示|意思是?)?\s*([\u4e00-\u9fff][\u4e00-\u9fff\w\s，。、]{1,30})',
        # "呢指的是XXX" or "呢表示XXX"
        rf'{word_esc}\s*呢\s*(?:指的是?|表示|就是|是)\s*([\u4e00-\u9fff][\u4e00-\u9fff\w\s，。、]{1,30})',
        # Chinese definition right after word: "economy 经济和节约"
        rf'{word_esc}\s*([\u4e00-\u9fff][\u4e00-\u9fff]{1,15})',
        # Before word: "经济的economical"
        rf'([\u4e00-\u9fff][\u4e00-\u9fff]{{1,10}})\s*{word_esc}',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, context)
        if m:
            defn = m.group(1).strip()
            defn = clean_chinese_text(defn)
            # Truncate at sentence boundary
            defn = re.split(r'[。！？\n]', defn)[0].strip()
            if 2 <= len(defn) <= 30:
                return defn
    
    return ''


def extract_example_v2(context, word):
    """Extract example or collocation."""
    word_esc = re.escape(word)
    
    patterns = [
        # "trade in something" style collocations
        rf'({word_esc}\s+(?:in|on|at|for|with|to|from|by|up|out|off|down|into|onto)\s+[A-Za-z]+)',
        # "fight for independence" style
        rf'((?:fight|make|take|give|have|do|get|keep|put|set)\s+{word_esc})',
        # "例如..." patterns
        rf'(?:例如|比如|比如说|像|举个例子)\s*([^\n。！？]{{5,50}})',
    ]
    
    for pattern in patterns:
        m = re.search(pattern, context, re.IGNORECASE)
        if m:
            ex = m.group(1).strip()
            if len(ex) > 3:
                return ex
    
    return ''


def extract_mastery_v2(context, word):
    """Extract mastery requirement."""
    ctx_lower = context.lower()
    
    if re.search(r'背会|背下来|必须记住|一定要记住|牢牢记住|这个挺重要|很重要|要记住', context):
        return '背会'
    if re.search(r'了解|不需要背|只需要|看看就行|看下就行|认识一下|知道就行', context):
        return '了解'
    
    return '认识'


def extract_phrases_v2(lines):
    """Extract important phrases."""
    full_text = '\n'.join(lines)
    phrases = []
    seen = set()
    
    # Look for "短语" introductions with multi-word patterns
    phrase_patterns = [
        r'短语\s*(?:是|呢\s*是|叫)\s*\n?\s*([A-Za-z]+\s+(?:in|on|at|for|with|to|from|by|up|out|off|down|into|onto)\s+[A-Za-z]+)',
        r'([A-Za-z]+\s+(?:in|on|at|for|with|to|from|by|up|out|off|down|into|onto)\s+[A-Za-z]+)\s*(?:指的是|表示|意思是)',
        r'(?:短语|搭配)\s*[:：]?\s*([A-Za-z]+\s+[A-Za-z]+(?:\s+[A-Za-z]+)?)\s*指的是',
    ]
    
    for pattern in phrase_patterns:
        for m in re.finditer(pattern, full_text, re.IGNORECASE):
            phrase = m.group(1).strip().lower()
            if phrase not in seen and len(phrase) > 5:
                ctx = full_text[max(0, m.start()-50):min(len(full_text), m.end()+200)]
                definition = extract_definition_v2(ctx, phrase.split()[0])
                if not definition:
                    # Try to get Chinese after "指的是"
                    dm = re.search(r'指的是?\s*([\u4e00-\u9fff][\u4e00-\u9fff\s，。]{1,20})', ctx)
                    if dm:
                        definition = clean_chinese_text(dm.group(1))
                
                seen.add(phrase)
                phrases.append({'phrase': phrase, 'definition': definition})
    
    return phrases


def has_vocab_content(lines):
    """Check if lines contain vocabulary teaching content."""
    text = '\n'.join(lines)
    # Must have both Chinese and English words mixed
    has_mixed = bool(re.search(r'[\u4e00-\u9fff].*[A-Za-z]{3,}', text))
    has_teaching_markers = bool(re.search(r'单词|词汇|短语|指的是|背会|认识', text))
    return has_mixed and has_teaching_markers


def generate_markdown(label, ch, theme, part, bvid, entries, phrases, has_content=True):
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
            word = e['word'].replace('|', '\\|')
            defn = e['definition'].replace('|', '\\|') if e['definition'] else '-'
            example = e['example'].replace('|', '\\|') if e['example'] else '-'
            mastery = e['mastery']
            lines.append(f"| {word} | {defn} | {example} | {mastery} |")
    elif not has_content:
        lines.append("*（该视频自动生成字幕内容不完整，未能提取到有效词汇）*")
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
            defn = p['definition'].replace('|', '\\|') if p['definition'] else '-'
            lines.append(f"| {phrase} | {defn} |")
    
    lines.append("")
    return '\n'.join(lines)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    
    for label, ch, theme, part, bvid in CHAPTERS:
        sub_path = os.path.join(SUB_DIR, f"{label}.txt")
        filename = f"{ch}-{theme}-{part}.md"
        out_path = os.path.join(OUT_DIR, filename)
        
        if not os.path.exists(sub_path) or os.path.getsize(sub_path) == 0:
            # No subtitle available
            md = generate_markdown(label, ch, theme, part, bvid, [], [], False)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(md)
            print(f"⚠️ {label}: no subtitle → placeholder")
            continue
        
        with open(sub_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Extract teaching lines
        teaching_lines = get_teaching_lines(text)
        
        if len(teaching_lines) < 10:
            md = generate_markdown(label, ch, theme, part, bvid, [], [], False)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(md)
            print(f"⚠️ {label}: too few lines → placeholder")
            continue
        
        # Check if content is actually vocabulary teaching
        if not has_vocab_content(teaching_lines):
            md = generate_markdown(label, ch, theme, part, bvid, [], [], False)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(md)
            print(f"⚠️ {label}: no vocab content → placeholder")
            continue
        
        # Extract vocabulary
        entries = extract_vocab_from_lines(teaching_lines)
        phrases = extract_phrases_v2(teaching_lines)
        
        # Generate markdown
        md = generate_markdown(label, ch, theme, part, bvid, entries, phrases, True)
        
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(md)
        
        print(f"✅ {label} → {filename}: {len(entries)} words, {len(phrases)} phrases")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
