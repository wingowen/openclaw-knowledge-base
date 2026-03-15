#!/usr/bin/env python3
"""
修复 4 句 TTS 生成失败的句子：
问题：content 字段包含英文原文 + 中文版本差异注释，导致超长
方案：只取英文部分（第一个中文字符之前）生成音频
"""
import os
import re
import sys
import subprocess
import requests

# 配置
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
MODEL_PATH = os.path.expanduser("~/.openclaw/workspace/kitten_tts_nano_v0_1.onnx")
VOICES_PATH = os.path.expanduser("~/.openclaw/workspace/voices.npz")
VOICE = "expr-voice-5-f"
BUCKET = "sentence-audios"
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

FAILED_IDS = [618, 882, 960, 1068]

def supabase_api(method, path, **kwargs):
    url = f"{SUPABASE_URL}{path}"
    headers = {**HEADERS, **kwargs.pop("headers", {})}
    return requests.request(method, url, headers=headers, **kwargs)

def extract_english(text):
    """提取英文部分（第一个中文字符之前）"""
    match = re.search(r'[\u4e00-\u9fff]', text)
    if match:
        return text[:match.start()].strip()
    return text.strip()

def generate_audio(text, tmp_wav):
    """用 KittenTTS 生成音频"""
    from kittentts import KittenTTS
    import soundfile as sf
    global _tts_model
    if '_tts_model' not in globals():
        _tts_model = KittenTTS(model_path=MODEL_PATH, voices_path=VOICES_PATH)
    audio = _tts_model.generate(text, voice=VOICE)
    sf.write(tmp_wav, audio, 24000)
    return len(audio) / 24000

def compress_to_opus(wav_path, opus_path):
    """压缩为 opus"""
    subprocess.run([
        "ffmpeg", "-y", "-i", wav_path,
        "-c:a", "libopus", "-b:a", "24k",
        "-ar", "24000", "-ac", "1",
        opus_path
    ], capture_output=True, check=True)
    return os.path.getsize(opus_path)

def upload_to_storage(sentence_id, opus_path):
    """上传到 Supabase Storage"""
    storage_path = f"{sentence_id}.opus"
    with open(opus_path, "rb") as f:
        resp = supabase_api("POST", f"/storage/v1/object/{BUCKET}/{storage_path}",
            headers={"Content-Type": "audio/ogg"},
            data=f)
    return resp.status_code in (200, 201)

def check_existing(sentence_id):
    """检查是否已存在"""
    storage_path = f"{sentence_id}.opus"
    resp = supabase_api("GET", f"/storage/v1/object/info/{BUCKET}/{storage_path}")
    return resp.status_code == 200

import tempfile

def main():
    print(f"=== 修复 {len(FAILED_IDS)} 句 TTS 失败句子 ===\n")
    
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for sid in FAILED_IDS:
        # 获取句子内容
        resp = supabase_api("GET", f"/rest/v1/sentences?id=eq.{sid}&select=id,content")
        data = resp.json()
        if not data:
            print(f"ID {sid}: 句子不存在，跳过")
            fail_count += 1
            continue
        
        full_content = data[0]["content"]
        english_text = extract_english(full_content)
        
        print(f"ID {sid}:")
        print(f"  原文长度: {len(full_content)} chars")
        print(f"  英文长度: {len(english_text)} chars")
        print(f"  英文内容: {english_text[:80]}...")
        
        if not english_text or len(english_text) < 5:
            print(f"  ⚠️ 英文部分太短，跳过")
            skip_count += 1
            continue
        
        # 检查是否已存在
        if check_existing(sid):
            print(f"  ⏭️ 音频已存在，跳过")
            skip_count += 1
            continue
        
        # 生成音频
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
            wav_path = tmp_wav.name
        with tempfile.NamedTemporaryFile(suffix=".opus", delete=False) as tmp_opus:
            opus_path = tmp_opus.name
        
        try:
            duration = generate_audio(english_text, wav_path)
            size = compress_to_opus(wav_path, opus_path)
            print(f"  生成成功: {duration:.1f}s, {size/1024:.1f}KB")
            
            if upload_to_storage(sid, opus_path):
                print(f"  ✅ 上传成功")
                success_count += 1
            else:
                print(f"  ❌ 上传失败")
                fail_count += 1
        except Exception as e:
            print(f"  ❌ 生成失败: {e}")
            fail_count += 1
        finally:
            os.unlink(wav_path)
            os.unlink(opus_path)
        
        print()
    
    print(f"=== 完成: 成功 {success_count}, 跳过 {skip_count}, 失败 {fail_count} ===")

if __name__ == "__main__":
    main()
