#!/usr/bin/env python3
"""Extract vocabulary teaching content from Bilibili auto-generated subtitles.
Filters out music lyrics and extracts Chinese teaching lines with English words.
"""

import re
import os
import json
import sys

SUB_DIR = '/root/.openclaw/workspace/tmp/subtitles'
OUT_DIR = '/root/.openclaw/workspace/tmp/extracted'

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

def is_english_lyric(line):
    """Check if a line is English music lyric (no Chinese chars)."""
    if not line.strip():
        return True
    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', line))
    if has_chinese:
        return False
    # Pure English/lyric lines
    return True

def extract_teaching_content(text):
    """Extract lines that contain vocabulary teaching content."""
    lines = text.split('\n')
    teaching_lines = []
    in_teaching = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', line))
        has_english_word = bool(re.search(r'[a-zA-Z]{2,}', line))
        
        # Start teaching section when we see Chinese intro
        if has_chinese and not in_teaching:
            # Check if this looks like teaching content
            if any(kw in line for kw in ['大家好', '各位', '同学', '单词', '下面', '首先', '这个']):
                in_teaching = True
        
        if in_teaching:
            teaching_lines.append(line)
    
    return '\n'.join(teaching_lines)

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    
    for label, ch, theme, part, bvid in CHAPTERS:
        sub_path = os.path.join(SUB_DIR, f"{label}.txt")
        if not os.path.exists(sub_path):
            print(f"⚠️ Missing: {label}")
            continue
        
        with open(sub_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        if len(text.strip()) == 0:
            print(f"⚠️ Empty: {label}")
            continue
        
        teaching = extract_teaching_content(text)
        
        out_path = os.path.join(OUT_DIR, f"{label}.txt")
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(teaching)
        
        print(f"✅ {label}: {len(teaching)} chars extracted (from {len(text)} chars)")
    
    print("\nDone!")

if __name__ == "__main__":
    main()
