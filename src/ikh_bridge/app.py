"""Local UI for one Skill and one local workspace."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from .agent import AgentError, run_agent
from .jobs import JobStore

app = FastAPI(title="iKH Local Bridge", version="0.2.0")
store = JobStore()


def configured_skill_file() -> Path:
    raw = os.environ.get("IKH_BRIDGE_SKILL_FILE", "").strip()
    return Path(raw).expanduser().resolve() if raw else Path.cwd().resolve() / "SKILL.md"


def configured_workspace() -> Path:
    raw = os.environ.get("IKH_BRIDGE_WORKSPACE", "").strip()
    return Path(raw).expanduser().resolve() if raw else Path.cwd().resolve()


class TaskRequest(BaseModel):
    task: str = Field(min_length=1, max_length=20000)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": "ikh-local-bridge", "version": "0.2.0"}


@app.get("/api/status")
def status() -> dict:
    skill_file = configured_skill_file()
    workspace = configured_workspace()
    return {
        "skill_file": str(skill_file),
        "skill_exists": skill_file.is_file() and skill_file.name == "SKILL.md",
        "workspace": str(workspace),
        "workspace_exists": workspace.is_dir(),
        "model": os.environ.get("IKH_BRIDGE_MODEL", "qwen2.5-coder:7b"),
        "model_endpoint": os.environ.get("IKH_BRIDGE_MODEL_BASE_URL", "http://127.0.0.1:11434/v1"),
        "execution_mode": "single_skill_local_agent",
        "cloud_fallback": False,
    }


@app.get("/api/jobs")
def jobs() -> dict:
    return {"jobs": store.list()}


@app.post("/api/task")
def run_task(request: TaskRequest) -> dict:
    skill_file = configured_skill_file()
    workspace = configured_workspace()
    if not skill_file.is_file() or skill_file.name != "SKILL.md":
        raise HTTPException(
            status_code=400,
            detail="Set IKH_BRIDGE_SKILL_FILE to the one Skill's existing SKILL.md before starting the Bridge.",
        )
    if not workspace.is_dir():
        raise HTTPException(
            status_code=400,
            detail="Set IKH_BRIDGE_WORKSPACE to an existing local working directory.",
        )
    job_id = store.create(skill_file.parent.name, "agent_task", str(workspace))
    try:
        result = run_agent(skill_file, workspace, request.task.strip())
        store.finish(job_id, result["status"], 0, result.get("answer", ""), "")
        result["job_id"] = job_id
        return result
    except AgentError as exc:
        store.finish(job_id, "FAILED", None, "", "", str(exc))
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        store.finish(job_id, "FAILED", None, "", "", f"{type(exc).__name__}: {exc}")
        raise HTTPException(status_code=500, detail="Local agent failed. Check the task history for details.") from exc


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """<!doctype html>
<html lang="vi">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>iKH Local Bridge</title>
<style>
:root{color-scheme:light dark;font:16px system-ui,sans-serif}body{max-width:1000px;margin:2rem auto;padding:0 1rem}
.panel{border:1px solid #8886;border-radius:12px;padding:1rem;margin:1rem 0}.muted{opacity:.72}
textarea,button{font:inherit;padding:.7rem;border:1px solid #8888;border-radius:8px}textarea{box-sizing:border-box;width:100%;min-height:140px}
button{cursor:pointer}pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:28rem;overflow:auto}
</style></head>
<body><h1>iKH Local Bridge</h1>
<p class="muted">Một Bridge = một Skill + một workspace cục bộ. Không có danh mục nhiều Skill.</p>
<section class="panel"><h2>Cấu hình phiên chạy</h2><pre id="status">Đang kiểm tra…</pre>
<p class="muted">Model mặc định chạy qua endpoint local Ollama-compatible. Bridge không tự chuyển sang cloud nếu model local không khả dụng.</p></section>
<section class="panel"><h2>Giao nhiệm vụ cho Skill</h2>
<p>Bridge nạp nội dung SKILL.md và cho agent thao tác file/chạy lệnh trong workspace đã cấu hình.</p>
<textarea id="task" placeholder="Mô tả công việc cần Skill thực hiện…"></textarea>
<p><button id="run">Bắt đầu chạy local</button></p><pre id="result">Chưa chạy tác vụ.</pre></section>
<section class="panel"><h2>Lịch sử</h2><button id="refresh">Làm mới</button><pre id="jobs">Đang tải…</pre></section>
<script>
const $=id=>document.getElementById(id);
async function loadStatus(){const r=await fetch('/api/status');const d=await r.json();$('status').textContent=JSON.stringify(d,null,2);
if(!d.skill_exists||!d.workspace_exists){$('status').textContent+='\n\nCần cấu hình IKH_BRIDGE_SKILL_FILE và IKH_BRIDGE_WORKSPACE rồi khởi động lại.'}}
async function loadJobs(){const r=await fetch('/api/jobs');$('jobs').textContent=JSON.stringify((await r.json()).jobs,null,2)}
$('refresh').addEventListener('click',loadJobs);
$('run').addEventListener('click',async()=>{const task=$('task').value.trim();if(!task){$('result').textContent='Nhập yêu cầu trước khi chạy.';return}
$('run').disabled=true;$('result').textContent='Đang chạy trên môi trường local…';
try{const r=await fetch('/api/task',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task})});const d=await r.json();$('result').textContent=JSON.stringify(d,null,2)}catch(e){$('result').textContent='Lỗi kết nối: '+e}finally{$('run').disabled=false;loadJobs()}});
loadStatus().catch(e=>$('status').textContent=String(e));loadJobs().catch(e=>$('jobs').textContent=String(e));
</script></body></html>"""
