#!/usr/bin/env python3
"""
批量生成句子音频 → 压缩 → 上传 Supabase Storage → 写入 sentence_audios 表
"""
import os
import sys
import json
import time
import base64
import subprocess
import tempfile
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

def supabase_api(method, path, **kwargs):
    url = f"{SUPABASE_URL}{path}"
    headers = {**HEADERS, **kwargs.pop("headers", {})}
    resp = requests.request(method, url, headers=headers, **kwargs)
    return resp

def get_all_sentences():
    """获取所有句子（分页）"""
    all_sentences = []
    offset = 0
    limit = 200
    while True:
        resp = supabase_api("GET", f"/rest/v1/sentences",
            params={
                "select": "id,content,article_id,sequence_order",
                "order": "id",
                "offset": offset,
                "limit": limit,
            })
        data = resp.json()
        if not data:
            break
        all_sentences.extend(data)
        offset += limit
        print(f"  已加载 {len(all_sentences)} 句...")
    return all_sentences

def generate_audio(text, tmp_wav):
    """用 KittenTTS 生成音频"""
    from kittentts import KittenTTS
    import soundfile as sf
    global _tts_model
    if '_tts_model' not in globals():
        _tts_model = KittenTTS(model_path=MODEL_PATH, voices_path=VOICES_PATH)
    audio = _tts_model.generate(text, voice=VOICE)
    sf.write(tmp_wav, audio, 24000)
    return len(audio) / 24000  # duration in seconds

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
    if resp.status_code in (200, 201):
        # 获取公开 URL
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{storage_path}"
        return public_url
    else:
        print(f"  上传失败: {resp.status_code} {resp.text}")
        return None

def insert_audio_record(sentence_id, audio_url, speaker, duration_ms, file_size):
    """写入 sentence_audios 表"""
    resp = supabase_api("POST", "/rest/v1/sentence_audios",
        headers={"Prefer": "return=representation"},
        json={
            "sentence_id": sentence_id,
            "audio_url": audio_url,
            "speaker": speaker,
            "speed": 1.0,
            "duration_ms": duration_ms,
            "file_size": file_size,
        })
    return resp.status_code in (200, 201)

def main():
    print("=" * 50)
    print("KittenTTS 批量音频生成")
    print(f"语音: {VOICE}")
    print(f"存储: Supabase Storage /{BUCKET}")
    print("=" * 50)

    # 1. 获取所有句子
    print("\n📖 获取句子列表...")
    sentences = get_all_sentences()
    print(f"共 {len(sentences)} 句")

    if not sentences:
        print("没有句子，退出")
        return

    # 2. 批量生成
    print(f"\n🎙️ 开始生成音频...")
    success = 0
    failed = 0
    skipped = 0
    total_size = 0
    start_time = time.time()

    with tempfile.TemporaryDirectory() as tmpdir:
        for i, sent in enumerate(sentences):
            sid = sent["id"]
            text = sent["content"].strip()

            if not text:
                skipped += 1
                continue

            # 进度
            if (i + 1) % 50 == 0 or i == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                eta = (len(sentences) - i - 1) / rate if rate > 0 else 0
                print(f"  [{i+1}/{len(sentences)}] 成功:{success} 跳过:{skipped} 失败:{failed} | {rate:.1f}句/秒 | ETA:{eta:.0f}s")

            try:
                wav_path = os.path.join(tmpdir, f"{sid}.wav")
                opus_path = os.path.join(tmpdir, f"{sid}.opus")

                # 生成 WAV
                duration_s = generate_audio(text, wav_path)

                # 压缩 Opus
                file_size = compress_to_opus(wav_path, opus_path)
                total_size += file_size

                # 上传
                audio_url = upload_to_storage(sid, opus_path)
                if not audio_url:
                    failed += 1
                    continue

                # 写入数据库
                duration_ms = int(duration_s * 1000)
                ok = insert_audio_record(sid, audio_url, VOICE, duration_ms, file_size)
                if ok:
                    success += 1
                else:
                    failed += 1
                    print(f"  ❌ 句子 {sid} DB写入失败")

            except Exception as e:
                failed += 1
                print(f"  ❌ 句子 {sid} 错误: {e}")

    # 3. 汇总
    elapsed = time.time() - start_time
    print(f"\n{'='*50}")
    print(f"✅ 完成！")
    print(f"  成功: {success}")
    print(f"  跳过: {skipped}")
    print(f"  失败: {failed}")
    print(f"  总大小: {total_size/1024/1024:.1f} MB")
    print(f"  耗时: {elapsed:.0f} 秒 ({elapsed/60:.1f} 分钟)")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
