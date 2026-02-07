import os
from pathlib import Path
from typing import List, Dict, Optional
import uuid
import json
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

try:
    from zai import ZhipuAiClient
except Exception:
    ZhipuAiClient = None


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    temperature: Optional[float] = 0.6
    model: Optional[str] = "glm-4.6"
    session_id: Optional[str] = None


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


persona_path = Path("config/ai-persona.md")
system_prompt: Optional[str] = None
if persona_path.exists():
    try:
        system_prompt = persona_path.read_text(encoding="utf-8")
    except Exception:
        system_prompt = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
def chat(req: ChatRequest):
    api_key = os.environ.get("ZHIPU_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="未设置 ZHIPU_API_KEY 环境变量")

    if ZhipuAiClient is None:
        raise HTTPException(status_code=500, detail="zai 包未安装")

    client = ZhipuAiClient(api_key=api_key)

    messages: List[Dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    for m in req.messages:
        messages.append({"role": m.role, "content": m.content})

    try:
        response = client.chat.completions.create(
            model=req.model or "glm-4.6",
            messages=messages,
            temperature=req.temperature if req.temperature is not None else 0.6,
        )
        content = response.choices[0].message.content
        session_id = req.session_id or uuid.uuid4().hex
        conv_dir = Path("conversations")
        conv_dir.mkdir(exist_ok=True)
        fp = conv_dir / f"{session_id}.jsonl"
        try:
            last_user = None
            for m in reversed(req.messages):
                if m.role == "user":
                    last_user = m.content
                    break
            now = datetime.utcnow().isoformat()
            with fp.open("a", encoding="utf-8") as f:
                if last_user is not None:
                    f.write(json.dumps({"ts": now, "role": "user", "content": last_user}) + "\n")
                f.write(json.dumps({"ts": now, "role": "assistant", "content": content}) + "\n")
        except Exception:
            pass
        return {"content": content, "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 静态页面
web_dir = Path("web")
web_dir.mkdir(exist_ok=True)
app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="static")

@app.get("/history/{session_id}")
def history(session_id: str):
    fp = Path("conversations") / f"{session_id}.jsonl"
    if not fp.exists():
        return []
    out: List[Dict[str, str]] = []
    with fp.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out

from mcp.registry import ServiceRegistry
from mcp.monitor import Monitor
from mcp.client import MCPClient
from pydantic import BaseModel

registry = ServiceRegistry()
monitor = Monitor()
client_mcp = MCPClient(registry, monitor)

class McpCallRequest(BaseModel):
    service: str
    path: str
    method: Optional[str] = "GET"
    payload: Optional[dict] = None
    headers: Optional[dict] = None

def _role_from_key(api_key: Optional[str]) -> str:
    if not api_key:
        return ""
    try:
        mapping = os.environ.get("MCP_API_KEYS")
        if mapping:
            import json as _json
            m = _json.loads(mapping)
            return m.get(api_key, "")
    except Exception:
        pass
    if api_key == os.environ.get("MCP_DEMO_KEY"):
        return "admin"
    return ""

def _allowed(role: str, method: str) -> bool:
    if role == "admin":
        return True
    if role == "operator":
        return method.upper() in ("GET", "POST", "PUT")
    if role == "viewer":
        return method.upper() == "GET"
    return False

@app.get("/mcp/services")
async def mcp_services(request: Request):
    api_key = request.headers.get("X-API-Key")
    role = _role_from_key(api_key)
    if not role:
        raise HTTPException(status_code=401, detail="unauthorized")
    return registry.list()

@app.get("/mcp/stats")
async def mcp_stats(request: Request):
    api_key = request.headers.get("X-API-Key")
    role = _role_from_key(api_key)
    if not role:
        raise HTTPException(status_code=401, detail="unauthorized")
    return monitor.stats()

@app.post("/mcp/call")
async def mcp_call(req: McpCallRequest, request: Request):
    api_key = request.headers.get("X-API-Key")
    role = _role_from_key(api_key)
    if not role:
        raise HTTPException(status_code=401, detail="unauthorized")
    if not _allowed(role, req.method or "GET"):
        raise HTTPException(status_code=403, detail="forbidden")
    res = await client_mcp.call(req.service, req.path, req.method or "GET", req.payload, req.headers)
    return res