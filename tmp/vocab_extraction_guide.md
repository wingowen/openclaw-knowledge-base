# 词汇提取指南

## 目标格式（参考第01章）

```markdown
# 雅思词汇真经｜第X章｜主题（上/下）

**视频**: https://www.bilibili.com/video/BVxxx/
**章节**: 第X章 | 主题 | 上/下

## 📚 词汇笔记

### 话题分组名

| 单词 | 释义 | 例句/搭配 | 掌握要求 |
|------|------|-----------|----------|
| atmosphere | 大气层；气氛 | the earth's atmosphere 地球大气层；working atmosphere 工作气氛 | 📖 背会 |
| core | 中心，核心；地核；果核 | to the core 彻底地；He is rotten to the core. 他坏透了 | 📖 背会 |
| horizon | 地平线；眼界，范围 | broaden/widen somebody's horizons 开阔眼界；on the horizon 即将发生 | 📖 背会 |
```

## 提取规则

1. **只提取老师明确讲解的英文单词**，忽略片头歌词、闲聊
2. **释义必须是中文词汇释义**，不是字幕原文！
   - ❌ 错误："下面是"、"好下面的是"、"用这个单词"
   - ✅ 正确："大气层；气氛"、"灾难；失败"
3. **例句/搭配**：提取老师说的英文例句或固定搭配，附中文翻译
4. **掌握要求**：根据老师的强调程度判断
   - 📖 背会：老师明确说要背、重点强调
   - 📖 认识：老师讲解但未强调背诵
   - 📖 了解：简单提及
5. **话题分组**：按老师讲解的主题对单词分组（如"灾难类"、"气候与气象"）
6. **忽略内容**：
   - 片头音乐歌词（英文歌曲部分）
   - 弹幕互动（"大家好"、"谢谢支持"等）
   - 非词汇内容的闲聊

## 字幕源文件

字幕文件位置：`/root/.openclaw/workspace/tmp/subtitles/{章节}.txt`
- 例如：`10上.txt`、`12下.txt`
- 新下载的字幕在：`/root/.openclaw/workspace/bili_temp/BVxxx/BVxxx_chunk_0.txt`

## 输出文件

输出到：`/root/.openclaw/workspace/knowledge-base/06-english-learning/雅思词汇真经/第X章-{主题}-{上下}.md`

覆盖现有文件（内容是错误的，需要替换）。
