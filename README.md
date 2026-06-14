# platform-framework

心理支持对话系统 — 最小可用架构。

## 架构

```
assisent/
├── server.py           # FastAPI: /chat /health /history + 静态页面
├── config/
│   └── ai-persona.md   # AI 人格定义（系统提示词）
└── web/
    ├── index.html      # 聊天界面
    ├── app.js          # 前端逻辑
    └── styles.css      # 样式
```

## 核心原则

1. 聊天界面即产品
2. 对话持久化 = 追加 JSONL 文件
3. 系统提示词定义人格，即核心 IP

## 快速开始

```bash
cd assisent
pip install fastapi uvicorn
export ZHIPU_API_KEY=your_key
uvicorn server:app --host 127.0.0.1 --port 8000
```

打开 http://127.0.0.1:8000 即可对话。

## 技术栈

- Python 3.11+ / FastAPI
- ZhipuAI (glm-4.6)
- JSONL 会话持久化
- 纯 HTML/CSS/JS 前端
