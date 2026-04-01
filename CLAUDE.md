# video-agent-hero

LangGraph驱动的本地视频生成CLI工具，输入brief生成1080×1920竖版MP4。

## 技术栈
- **核心**: LangGraph + SQLite + ChromaDB + PIL + FFmpeg + Typer CLI
- **LLM**: claude-sonnet-4-6（需ANTHROPIC_API_KEY），否则用mock planner
- **输出**: 1080×1920 H.264 MP4, 30fps, 烧录SRT字幕 + logo水印

## 启动方式
```bash
# 安装
pip install -e .

# 常用命令
vah init
vah demo
vah new --brief "..."
vah run --project ID [--yes]
vah feedback --project ID --text "..."
```

## 踩过的坑
- **LangGraph state**：不要把非TypedDict的key（如`_db`）传进state，会报错。用`agent/deps.py`全局单例
- commit message要写用户可读的产品语言，不要写开发jargon（因为changelog自动从git log生成，直接展示给用户）

## 测试
```bash
python3.11 -m pytest tests/ -v  # 23个测试
```

## 当前状态
- CLI完整可用
- HF Space部署：ejzhu2026/video-agent-hero
