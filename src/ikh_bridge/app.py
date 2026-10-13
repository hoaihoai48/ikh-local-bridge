"""Loopback-only web UI and API for the Local Bridge MVP."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from .jobs import JobStore
from .registry import default_library, discover_skills
from .runner import RunRejected, run_tool

app = FastAPI(title="iKH Local Bridge", version="0.1.0")
store = JobStore()


class RunRequest(BaseModel):
    skill_slug: str = Field(min_length=1, max_length=64)
    tool_id: str = Field(min_length=1, max_length=64)
    workspace: str = Field(min_length=1, max_length=2048)
    reviewed: bool = False


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": "ikh-local-bridge", "version": "0.1.0"}


@app.get("/api/skills")
def skills() -> dict:
    found, errors = discover_skills()
    return {
        "library": str(default_library()),
        "skills": [
            {
                "slug": skill.slug,
                "name": skill.name,
                "version": skill.version,
                "description": skill.description,
                "has_instructions": skill.has_instructions,
                "tools": [
                    {"id": tool.id, "description": tool.description, "entrypoint": tool.entrypoint,
                     "timeout_seconds": tool.timeout_seconds}
                    for tool in skill.tools
                ],
                "runnable": bool(skill.tools),
            }
            for skill in found
        ],
        "errors": errors,
    }


@app.get("/api/jobs")
def jobs() -> dict:
    return {"jobs": store.list()}


@app.post("/api/run")
def run(request: RunRequest) -> dict:
    found, errors = discover_skills()
    skill = next((item for item in found if item.slug == request.skill_slug), None)
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found in the configured library")
    tool = next((item for item in skill.tools if item.id == request.tool_id), None)
    if tool is None:
        raise HTTPException(status_code=400, detail="Tool is not declared in skill.json")
    if not request.reviewed:
        raise HTTPException(status_code=400, detail="Review the Skill script and explicitly confirm before running it")
    try:
        return run_tool(skill, tool, Path(request.workspace), store)
    except RunRejected as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    # Static UI; dynamic values are rendered via textContent, not HTML injection.
    return """<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>iKH Local Bridge</title>
<style>
:root{color-scheme:light dark;font:16px system-ui,sans-serif}body{max-width:1050px;margin:2rem auto;padding:0 1rem}
h1{margin-bottom:.25rem}.muted{opacity:.7}.panel{border:1px solid #8886;border-radius:12px;padding:1rem;margin:1rem 0}
.row{display:flex;gap:.75rem;flex-wrap:wrap;align-items:end}label{display:grid;gap:.35rem;flex:1;min-width:220px}
input,select,button{font:inherit;padding:.65rem;border-radius:8px;border:1px solid #8888}
button{cursor:pointer}pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:24rem;overflow:auto}
.skill{border-top:1px solid #8885;padding:.75rem 0}.pill{font-size:.8rem;border:1px solid #8888;border-radius:99px;padding:.15rem .5rem}
</style></head>
<body>
<h1>iKH Local Bridge</h1><p class="muted">Quản lý và kiểm tra Skill chạy local. Chưa tự gọi AI provider.</p>
<div class="panel"><h2>Skill Library</h2><p id="library" class="muted">Đang tải…</p><div id="skills"></div></div>
<div class="panel"><h2>Chạy tool đã khai báo</h2><p class="muted">Chạy script Python thật. Hãy đọc và tin cậy mã nguồn trước khi chạy; script có quyền của tài khoản máy hiện tại, chưa có sandbox hệ điều hành.</p>
<div class="row"><label>Skill<select id="skill"></select></label><label>Tool<select id="tool"></select></label>
<label>Workspace (thư mục có sẵn)<input id="workspace" placeholder="/duong/dan/thu-muc"></label>
<label style="flex-basis:100%"><span><input type="checkbox" id="reviewed"> Tôi đã xem mã nguồn của Skill/tool và đồng ý chạy script này.</span></label><button id="run">Chạy tool</button></div><pre id="result">Chọn Skill và Tool để bắt đầu.</pre></div>
<div class="panel"><h2>Lịch sử tác vụ</h2><button id="refresh">Làm mới</button><pre id="jobs">Đang tải…</pre></div>
<script>
const $=id=>document.getElementById(id);let skills=[];
async function loadSkills(){const r=await fetch('/api/skills');const d=await r.json();skills=d.skills||[];$('library').textContent='Thư mục: '+d.library;
$('skills').replaceChildren();for(const s of skills){const el=document.createElement('div');el.className='skill';const h=document.createElement('strong');h.textContent=s.name+' ('+s.slug+') ';const p=document.createElement('span');p.className='pill';p.textContent=s.runnable?'Có tool khai báo':'Chỉ đọc / chưa có tool';const desc=document.createElement('p');desc.textContent=s.description;el.append(h,p,desc);$('skills').append(el)}
$('skill').replaceChildren();for(const s of skills){const o=document.createElement('option');o.value=s.slug;o.textContent=s.name+' ('+s.slug+')';$('skill').append(o)}updateTools();
if(d.errors&&d.errors.length){const e=document.createElement('pre');e.textContent=JSON.stringify(d.errors,null,2);$('skills').append(e)}}
function updateTools(){const s=skills.find(x=>x.slug===$('skill').value);$('tool').replaceChildren();for(const t of (s?.tools||[])){const o=document.createElement('option');o.value=t.id;o.textContent=t.id+' — '+t.description;$('tool').append(o)}}
async function loadJobs(){const r=await fetch('/api/jobs');$('jobs').textContent=JSON.stringify((await r.json()).jobs,null,2)}
$('skill').addEventListener('change',updateTools);$('refresh').addEventListener('click',loadJobs);
$('run').addEventListener('click',async()=>{const workspace=$('workspace').value.trim();if(!workspace){$('result').textContent='Nhập đường dẫn workspace trước.';return}
if(!$('reviewed').checked){$('result').textContent='Bạn cần xác nhận đã xem và tin cậy mã nguồn trước khi chạy.';return}
$('result').textContent='Đang chạy…';const r=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({skill_slug:$('skill').value,tool_id:$('tool').value,workspace,reviewed:true})});$('result').textContent=JSON.stringify(await r.json(),null,2);loadJobs()});
loadSkills().catch(e=>$('library').textContent='Lỗi: '+e);loadJobs().catch(e=>$('jobs').textContent='Lỗi: '+e);
</script></body></html>"""
