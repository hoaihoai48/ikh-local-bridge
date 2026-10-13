"""Local UI for one Skill and one local workspace."""
from __future__ import annotations

import os
import re
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, field_validator

from .agent import AgentError, run_agent
from .jobs import JobStore

app = FastAPI(title="iKH Local Bridge", version="0.3.0")


def get_store() -> JobStore:
    return JobStore()


def configured_skill_file() -> Path:
    raw = os.environ.get("IKH_BRIDGE_SKILL_FILE", "").strip()
    return Path(raw).expanduser().resolve() if raw else Path.cwd().resolve() / "SKILL.md"


def configured_workspace() -> Path:
    raw = os.environ.get("IKH_BRIDGE_WORKSPACE", "").strip()
    return Path(raw).expanduser().resolve() if raw else Path.cwd().resolve()


def skill_metadata(skill_file: Path) -> dict[str, str]:
    """Extract a readable identity from SKILL.md without requiring a manifest."""
    title = skill_file.parent.name.replace("-", " ").replace("_", " ").strip().title() or "Local Skill"
    description = "Không gian làm việc chuyên biệt cho Skill này."
    try:
        content = skill_file.read_text(encoding="utf-8")
        heading = re.search(r"(?m)^#\s+(.+?)\s*$", content)
        if heading:
            title = heading.group(1).strip()
        # Prefer a short frontmatter description; otherwise use the first prose paragraph.
        frontmatter = re.search(r"(?ms)^---\s*\n(.*?)\n---\s*(?:\n|$)", content)
        if frontmatter:
            match = re.search(r"(?m)^description:\s*[\"']?(.+?)[\"']?\s*$", frontmatter.group(1))
            if match:
                description = match.group(1).strip()
        if description == "Không gian làm việc chuyên biệt cho Skill này.":
            lines = content.splitlines()
            for i, line in enumerate(lines):
                if line.startswith("#"):
                    for candidate in lines[i + 1:]:
                        if candidate.strip() and not candidate.startswith("#") and not candidate.startswith("---"):
                            description = candidate.strip().strip("*")
                            break
                    break
    except OSError:
        pass
    return {"skill_name": title, "skill_description": description[:240]}


class TaskRequest(BaseModel):
    task: str = Field(min_length=1, max_length=20000)

    @field_validator("task")
    @classmethod
    def task_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("task must not be blank")
        return value.strip()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": "ikh-local-bridge", "version": "0.3.0"}


@app.get("/api/status")
def status() -> dict:
    skill_file = configured_skill_file()
    workspace = configured_workspace()
    metadata = skill_metadata(skill_file) if skill_file.is_file() else {
        "skill_name": "Chưa cấu hình Skill",
        "skill_description": "Trỏ Bridge tới file SKILL.md mà bạn muốn chạy.",
    }
    return {
        **metadata,
        "skill_file": str(skill_file),
        "skill_exists": skill_file.is_file() and skill_file.name == "SKILL.md",
        "workspace": str(workspace),
        "workspace_exists": workspace.is_dir(),
        "model": os.environ.get("IKH_BRIDGE_MODEL", "qwen2.5-coder:7b"),
        "model_endpoint": os.environ.get("IKH_BRIDGE_MODEL_BASE_URL", "http://127.0.0.1:11434/v1"),
        "execution_mode": "single_skill_local_agent",
        "cloud_fallback": False,
        "custom_ui": (skill_file.parent / "bridge-ui.html").is_file(),
    }


@app.get("/api/jobs")
def jobs() -> dict:
    return {"jobs": get_store().list()}


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
    store = get_store()
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
    # A Skill may ship its own complete UI next to SKILL.md. This makes the Bridge
    # a dedicated app for that Skill; the built-in workbench is the fallback.
    skill_file = configured_skill_file()
    custom_ui = skill_file.parent / "bridge-ui.html"
    if skill_file.is_file() and custom_ui.is_file():
        return custom_ui.read_text(encoding="utf-8")

    return r"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Skill Workbench · iKH Local Bridge</title>
<style>
:root{color-scheme:dark;--bg:#0b1020;--panel:#121a2d;--panel2:#172239;--line:#273550;--text:#eef3ff;--muted:#91a0bb;--accent:#8bb8ff;--green:#5ee0b5;--amber:#f6c879;font:15px/1.5 Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 10% 0%,#182b4a 0,transparent 38%),var(--bg);color:var(--text)}
button,textarea{font:inherit}button{cursor:pointer}.app{display:grid;grid-template-columns:260px minmax(0,1fr);min-height:100vh}.side{padding:26px 18px;border-right:1px solid var(--line);background:#0c1324cc}.brand{display:flex;align-items:center;gap:11px;font-weight:750;letter-spacing:.02em}.logo{display:grid;place-items:center;width:36px;height:36px;border-radius:12px;background:linear-gradient(145deg,#8bb8ff,#a6f0dc);color:#102039;font-weight:900}.eyebrow{font-size:11px;text-transform:uppercase;letter-spacing:.14em;color:var(--muted);font-weight:750}.skill-card{margin-top:34px;padding:17px 14px;background:linear-gradient(145deg,#1a2943,#121a2d);border:1px solid #344664;border-radius:16px}.skill-card h2{font-size:17px;line-height:1.3;margin:9px 0}.skill-card p{font-size:12px;color:var(--muted);margin:0}.side-nav{margin-top:25px;display:grid;gap:7px}.nav-item{padding:10px 12px;border-radius:9px;color:#c4d0e5;font-size:13px}.nav-item.active{background:#1c2b46;color:#fff}.nav-item span{display:inline-block;width:25px;color:var(--accent)}.side-foot{position:sticky;top:90vh;margin-top:44px;font-size:12px;color:var(--muted)}.dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--green);margin-right:7px}
main{max-width:1180px;width:100%;padding:34px clamp(20px,4vw,54px);margin:0 auto}.top{display:flex;justify-content:space-between;gap:20px;align-items:flex-start}.top h1{font-size:clamp(26px,3vw,38px);line-height:1.15;letter-spacing:-.04em;margin:8px 0 10px}.top p{color:var(--muted);margin:0;max-width:650px}.local-pill{white-space:nowrap;border:1px solid #28624f;color:var(--green);background:#102b29;border-radius:99px;padding:7px 11px;font-size:12px}
.metrics{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:28px 0}.metric,.panel{background:#111a2bdb;border:1px solid var(--line);border-radius:15px}.metric{padding:14px 16px}.metric .label{font-size:12px;color:var(--muted)}.metric .value{font-size:14px;font-weight:650;margin-top:6px;overflow-wrap:anywhere}.metric .value.ok{color:var(--green)}.metric .value.warn{color:var(--amber)}
.workspace{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(250px,.8fr);gap:15px;align-items:start}.panel{padding:22px}.panel-head{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:14px}.panel h2{font-size:16px;margin:0}.sub{font-size:12px;color:var(--muted);margin:5px 0 0}.step{display:flex;gap:12px;margin:18px 0 22px}.step-num{width:28px;height:28px;flex:0 0 28px;border-radius:9px;display:grid;place-items:center;background:#233958;color:var(--accent);font-weight:750}.step strong{font-size:13px}.step p{margin:3px 0 0;font-size:12px;color:var(--muted)}textarea{width:100%;min-height:155px;resize:vertical;background:#0b1221;border:1px solid #34435d;border-radius:12px;padding:14px;color:var(--text);outline:none}textarea:focus{border-color:var(--accent);box-shadow:0 0 0 3px #8bb8ff1b}.actions{display:flex;align-items:center;gap:12px;margin-top:13px}.primary{background:var(--accent);border:0;color:#101b2d;font-weight:800;border-radius:10px;padding:11px 16px}.primary:disabled{opacity:.5;cursor:wait}.hint{font-size:11px;color:var(--muted)}.result{margin-top:18px;border-top:1px solid var(--line);padding-top:16px}.result h3{font-size:12px;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin:0 0 10px}.output{white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.65 ui-monospace,SFMono-Regular,Menlo,monospace;color:#dbe7fa;max-height:340px;overflow:auto}.empty{color:var(--muted);font-size:13px}.outline{width:100%;text-align:left;background:transparent;color:var(--text);border:1px solid var(--line);border-radius:10px;padding:11px 12px;margin-top:9px}.outline:hover{background:var(--panel2)}.config{display:grid;gap:14px}.config-row{display:grid;gap:4px}.config-row .k{font-size:11px;text-transform:uppercase;letter-spacing:.09em;color:var(--muted)}.config-row .v{font-size:12px;overflow-wrap:anywhere}.config-note{border-radius:10px;padding:12px;background:#171f31;color:#aebbd1;font-size:12px}.history{margin-top:15px}.history-list{display:grid;gap:8px}.job{padding:11px 12px;border:1px solid var(--line);border-radius:10px}.job-top{display:flex;justify-content:space-between;gap:10px;font-size:12px}.job small{display:block;color:var(--muted);margin-top:4px}.status-tag{font-size:10px;color:var(--green)}.status-tag.failed{color:#ff9e9e}
@media(max-width:900px){.app{grid-template-columns:1fr}.side{border-right:0;border-bottom:1px solid var(--line);padding:14px 18px}.skill-card,.side-nav,.side-foot{display:none}main{padding-top:24px}.workspace{grid-template-columns:1fr}.metrics{grid-template-columns:1fr 1fr}.metrics .metric:last-child{grid-column:1/-1}}
@media(max-width:520px){.top{display:block}.local-pill{display:inline-block;margin-top:15px}.metrics{grid-template-columns:1fr}.metrics .metric:last-child{grid-column:auto}.panel{padding:16px}}
</style></head>
<body><div class="app">
<aside class="side"><div class="brand"><div class="logo">iK</div><div>iKH <span style="color:var(--muted);font-weight:500">/ BRIDGE</span></div></div>
<div class="skill-card"><div class="eyebrow">Skill đang hoạt động</div><h2 id="sideSkill">Đang đọc Skill…</h2><p id="sideDescription">Một ứng dụng local dành riêng cho một quy trình.</p></div>
<nav class="side-nav"><div class="nav-item active"><span>01</span>Không gian làm việc</div><div class="nav-item"><span>02</span>Lịch sử tác vụ</div><div class="nav-item"><span>03</span>Cấu hình local</div></nav>
<div class="side-foot"><span class="dot"></span>Local runtime · Không tự chuyển cloud</div></aside>
<main>
<header class="top"><div><div class="eyebrow">Skill workbench / Local runtime</div><h1 id="headline">Không gian làm việc</h1><p id="description">Giao việc cho Skill đã cấu hình. Bridge dùng model và công cụ trên máy của bạn để làm việc trong workspace được chỉ định.</p></div><div class="local-pill">● CHẠY TRÊN MÁY LOCAL</div></header>
<section class="metrics"><div class="metric"><div class="label">Skill</div><div class="value" id="skillState">Đang kiểm tra…</div></div><div class="metric"><div class="label">Model local</div><div class="value" id="modelState">Đang kiểm tra…</div></div><div class="metric"><div class="label">Workspace</div><div class="value" id="workspaceState">Đang kiểm tra…</div></div></section>
<div class="workspace"><section class="panel"><div class="panel-head"><div><h2>Giao nhiệm vụ</h2><p class="sub">Mô tả kết quả mong muốn; Skill sẽ tự áp dụng hướng dẫn của nó.</p></div></div>
<div class="step"><div class="step-num">1</div><div><strong>Giao yêu cầu</strong><p>Nêu rõ mục tiêu, đầu ra cần tạo và điều kiện cần kiểm tra.</p></div></div>
<textarea id="task" placeholder="Ví dụ: Đọc nội dung trong workspace, kiểm tra theo quy tắc của Skill, sửa các lỗi đã xác minh và ghi báo cáo kết quả…"></textarea>
<div class="actions"><button class="primary" id="run">▶  Chạy Skill</button><span class="hint" id="runHint">Không tự gửi dữ liệu lên cloud.</span></div>
<div class="result"><h3>Kết quả thực thi</h3><div id="result" class="output empty">Chưa có tác vụ. Kết quả và bằng chứng sẽ hiển thị tại đây.</div></div></section>
<aside><section class="panel"><div class="panel-head"><div><h2>Runtime local</h2><p class="sub">Cấu hình phiên hiện tại</p></div></div><div class="config"><div class="config-row"><div class="k">Đường dẫn Skill</div><div class="v" id="skillPath">—</div></div><div class="config-row"><div class="k">Thư mục làm việc</div><div class="v" id="workspacePath">—</div></div><div class="config-row"><div class="k">Model endpoint</div><div class="v" id="endpoint">—</div></div></div><div class="config-note" style="margin-top:17px" id="configNote">Đang kiểm tra cấu hình…</div></section>
<section class="panel history"><div class="panel-head"><div><h2>Tác vụ gần đây</h2><p class="sub">Lịch sử phiên chạy local</p></div><button class="outline" style="width:auto;margin:0;padding:7px 10px" id="refresh">Làm mới</button></div><div class="history-list" id="jobs"><div class="empty">Đang tải lịch sử…</div></div></section></aside></div>
</main></div>
<script>
const $=id=>document.getElementById(id);
function shortPath(s){if(!s)return "—";return s.length>58?"…"+s.slice(-55):s}
async function loadStatus(){const r=await fetch('/api/status');const d=await r.json();
$('sideSkill').textContent=d.skill_name;$('headline').textContent=d.skill_name;$('sideDescription').textContent=d.skill_description;$('description').textContent=d.skill_description;
$('skillState').textContent=d.skill_exists?'Đã nạp SKILL.md':'Chưa cấu hình';$('skillState').className='value '+(d.skill_exists?'ok':'warn');
$('modelState').textContent=d.model;$('workspaceState').textContent=d.workspace_exists?'Sẵn sàng':'Không tồn tại';$('workspaceState').className='value '+(d.workspace_exists?'ok':'warn');
$('skillPath').textContent=d.skill_file;$('workspacePath').textContent=d.workspace;$('endpoint').textContent=d.model_endpoint;
$('configNote').textContent=!d.skill_exists?'Chưa tìm thấy SKILL.md. Cấu hình IKH_BRIDGE_SKILL_FILE rồi khởi động lại.':!d.workspace_exists?'Workspace chưa tồn tại. Cấu hình IKH_BRIDGE_WORKSPACE rồi khởi động lại.':d.custom_ui?'Đang dùng giao diện riêng do Skill cung cấp.':'Đang dùng Workbench mặc định; có thể đặt bridge-ui.html cạnh SKILL.md để thiết kế giao diện riêng cho Skill này.';
}
async function loadJobs(){const r=await fetch('/api/jobs');const d=await r.json();const items=d.jobs||[];$('jobs').innerHTML='';
if(!items.length){$('jobs').innerHTML='<div class="empty">Chưa có tác vụ nào.</div>';return}
items.slice().reverse().slice(0,6).forEach(j=>{const el=document.createElement('div');el.className='job';const top=document.createElement('div');top.className='job-top';const name=document.createElement('strong');name.textContent=j.kind||j.name||'Tác vụ Skill';const state=document.createElement('span');state.className='status-tag '+((j.status||'').includes('FAIL')?'failed':'');state.textContent=j.status||'—';top.append(name,state);const small=document.createElement('small');small.textContent=[j.created_at||j.started_at||'',j.workspace||''].filter(Boolean).join(' · ')||('ID '+(j.id||j.job_id||''));el.append(top,small);$('jobs').append(el)})}
$('refresh').addEventListener('click',()=>loadJobs().catch(e=>$('jobs').textContent=String(e)));
$('run').addEventListener('click',async()=>{const task=$('task').value.trim();if(!task){$('result').textContent='Nhập yêu cầu trước khi chạy.';return}
$('run').disabled=true;$('run').textContent='Đang chạy…';$('runHint').textContent='Skill đang thực hiện công việc local; tác vụ có thể mất vài phút.';$('result').className='output';$('result').textContent='Đang khởi tạo agent…';
try{const r=await fetch('/api/task',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task})});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Tác vụ thất bại');$('result').textContent=(d.answer||'Đã chạy xong nhưng model không trả lời dạng văn bản.')+'\n\n---\nTrạng thái: '+d.status+'\nJob: '+(d.job_id||'—')+'\nModel: '+(d.model||'—')+'\nSố vòng: '+(d.rounds??'—');$('runHint').textContent='Hoàn tất. Kiểm tra các tệp đầu ra trong workspace.'}
catch(e){$('result').textContent='Không chạy được: '+e.message;$('runHint').textContent='Kiểm tra model local, cấu hình Skill và workspace.'}
finally{$('run').disabled=false;$('run').textContent='▶  Chạy Skill';loadJobs().catch(()=>{})}});
loadStatus().catch(e=>$('configNote').textContent='Lỗi đọc cấu hình: '+e);loadJobs().catch(e=>$('jobs').textContent=String(e));
</script></body></html>"""
