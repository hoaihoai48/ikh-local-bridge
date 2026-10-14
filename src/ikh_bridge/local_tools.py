"""Workspace-scoped tools and read-only public-source retrieval for curriculum authoring."""
from __future__ import annotations
import ipaddress, os, socket, subprocess
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urljoin
from urllib.request import HTTPRedirectHandler, Request, build_opener

MAX_BYTES=220_000
MAX_ENTRIES=250
MAX_URL_BYTES=220_000
PROTECTED={".git",".ssh",".aws",".config","node_modules",".venv","__pycache__"}

TOOL_DEFINITIONS=[
{"type":"function","function":{"name":"list_files","description":"List direct children of a directory in the configured workspace.","parameters":{"type":"object","properties":{"path":{"type":"string","description":"Workspace-relative directory, defaults to ."}},"required":[],"additionalProperties":False}}},
{"type":"function","function":{"name":"read_file","description":"Read a UTF-8 text file inside the workspace, up to 220 KB.","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"],"additionalProperties":False}}},
{"type":"function","function":{"name":"write_file","description":"Create/update a UTF-8 text file inside the workspace; use only when the user's task and Skill gates authorize changes.","parameters":{"type":"object","properties":{"path":{"type":"string"},"content":{"type":"string"}},"required":["path","content"],"additionalProperties":False}}},
{"type":"function","function":{"name":"run_command","description":"Run an allowlisted read-only git command or a Python script/test/validator within the workspace. argv only, no shell; installs, network, git writes and destructive commands are blocked.","parameters":{"type":"object","properties":{"argv":{"type":"array","items":{"type":"string"},"minItems":1,"maxItems":40},"cwd":{"type":"string"},"timeout_seconds":{"type":"integer","minimum":1,"maximum":180}},"required":["argv"],"additionalProperties":False}}},
{"type":"function","function":{"name":"fetch_url","description":"Read a public HTTPS source page for evidence research. GET only; private/local IPs and redirects to them are blocked; response is size-limited and never uploads workspace content.","parameters":{"type":"object","properties":{"url":{"type":"string","description":"Public HTTPS source URL"}}, "required":["url"],"additionalProperties":False}}}]



def _path(root:Path,raw:str,must_exist=False)->Path:
    if not isinstance(raw,str) or not raw.strip(): raise ValueError("path must be non-empty")
    p=Path(raw).expanduser()
    if not p.is_absolute(): p=root/p
    p=p.resolve(); root=root.resolve()
    if not p.is_relative_to(root): raise ValueError("path escapes configured workspace")
    parts=p.relative_to(root).parts
    if any(x in PROTECTED or x==".env" or x.startswith(".env.") for x in parts): raise ValueError("protected config/runtime path blocked")
    if must_exist and not p.exists(): raise FileNotFoundError(f"path does not exist: {raw}")
    return p

def _list(root,raw="."):
    p=_path(root,raw,True)
    if not p.is_dir(): raise ValueError("path is not a directory")
    entries=[]
    for c in sorted(p.iterdir(),key=lambda x:x.name.casefold()):
        if c.name in PROTECTED or c.name==".env" or c.name.startswith(".env."): continue
        try: entries.append({"name":c.name,"type":"directory" if c.is_dir() else "file","size_bytes":c.stat().st_size if c.is_file() else None})
        except OSError: entries.append({"name":c.name,"type":"unreadable"})
        if len(entries)>=MAX_ENTRIES: break
    return {"ok":True,"path":str(p.relative_to(root.resolve())),"entries":entries,"truncated":len(entries)>=MAX_ENTRIES}

def _read(root,raw):
    p=_path(root,raw,True)
    if not p.is_file(): raise ValueError("path is not a file")
    if p.stat().st_size>MAX_BYTES: raise ValueError(f"file exceeds {MAX_BYTES} bytes")
    try: content=p.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc: raise ValueError("only UTF-8 text files supported") from exc
    return {"ok":True,"path":str(p.relative_to(root.resolve())),"bytes":p.stat().st_size,"content":content}

def _write(root,raw,content):
    if not isinstance(content,str): raise ValueError("content must be a string")
    size=len(content.encode("utf-8"))
    if size>MAX_BYTES: raise ValueError(f"content exceeds {MAX_BYTES} bytes")
    p=_path(root,raw); existed=p.exists()
    if existed and not p.is_file(): raise ValueError("target exists and is not a regular file")
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text(content,encoding="utf-8")
    return {"ok":True,"path":str(p.relative_to(root.resolve())),"bytes_written":size,"overwrote_existing_file":existed}

def _validate_public_https(url):
    p=urlparse(url)
    if p.scheme!="https" or not p.hostname or p.username or p.password or p.port not in (None,443):
        raise ValueError("fetch_url accepts public HTTPS URLs only, without credentials or custom ports")
    if p.hostname.lower() in {"localhost","localhost.localdomain"} or p.hostname.endswith(".local"):
        raise ValueError("local hostnames are blocked")
    try: addresses={item[4][0] for item in socket.getaddrinfo(p.hostname,443,type=socket.SOCK_STREAM)}
    except OSError as exc: raise ValueError(f"Cannot resolve public source host: {exc}") from exc
    if not addresses: raise ValueError("source host did not resolve")
    for address in addresses:
        ip=ipaddress.ip_address(address.split("%")[0])
        if not ip.is_global: raise ValueError("private, loopback, link-local, reserved, or non-public IP targets are blocked")
    return url

class _SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _validate_public_https(urljoin(req.full_url,newurl))
        return super().redirect_request(req,fp,code,msg,headers,newurl)

class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.parts=[]; self.hidden=0
    def handle_starttag(self,tag,attrs):
        if tag in {"script","style","noscript","svg"}: self.hidden+=1
        elif tag in {"p","div","br","li","tr","h1","h2","h3","h4","section"}: self.parts.append("\n")
    def handle_endtag(self,tag):
        if tag in {"script","style","noscript","svg"} and self.hidden: self.hidden-=1
        elif tag in {"p","div","li","tr","h1","h2","h3","h4","section"}: self.parts.append("\n")
    def handle_data(self,data):
        if not self.hidden and data.strip(): self.parts.append(data.strip()+" ")

def _fetch_url(raw):
    if not isinstance(raw,str) or len(raw)>4096: raise ValueError("url must be a string up to 4096 characters")
    url=_validate_public_https(raw)
    opener=build_opener(_SafeRedirect())
    req=Request(url,headers={"User-Agent":"iKH-Local-Bridge/0.2 (read-only curriculum source fetch)","Accept":"text/html,text/plain,application/json;q=0.9,*/*;q=0.1"},method="GET")
    try:
        with opener.open(req,timeout=20) as response:
            final_url=_validate_public_https(response.geturl())
            kind=response.headers.get_content_type()
            if kind not in {"text/html","text/plain","application/json","application/xml","text/xml"}:
                raise ValueError(f"unsupported source content type: {kind}")
            body=response.read(MAX_URL_BYTES+1)
    except HTTPError as exc: raise ValueError(f"source returned HTTP {exc.code}") from exc
    except URLError as exc: raise ValueError(f"source fetch failed: {exc.reason}") from exc
    if len(body)>MAX_URL_BYTES: body=body[:MAX_URL_BYTES]
    text=body.decode(response.headers.get_content_charset() or "utf-8",errors="replace")
    if kind=="text/html":
        parser=_TextExtractor(); parser.feed(text); text="".join(parser.parts)
    return {"ok":True,"url":final_url,"content_type":kind,"truncated":len(body)>=MAX_URL_BYTES,"text":text[:MAX_URL_BYTES]}

def _run(root,argv,cwd=".",timeout_seconds=60):
    if not isinstance(argv,list) or not argv or len(argv)>40 or not all(isinstance(x,str) and x for x in argv): raise ValueError("argv must be a non-empty list of strings")
    if isinstance(timeout_seconds,bool) or not isinstance(timeout_seconds,int) or not 1<=timeout_seconds<=180: raise ValueError("timeout_seconds must be 1..180")
    workdir=_path(root,cwd,True)
    if not workdir.is_dir(): raise ValueError("cwd must be a directory")
    # Accept command names only. Checking Path(argv[0]).name would also accept
    # an arbitrary executable such as /tmp/python, defeating the allowlist.
    allowed_executables = {"python", "python3", "python3.11", "python3.12", "pytest", "git"}
    if argv[0] not in allowed_executables:
        raise ValueError("executable must be an allowlisted command name without a path")
    exe=argv[0]; args=argv[1:]
    if exe in {"python","python3","python3.11","python3.12"}:
        if not args: raise ValueError("interactive Python blocked")
        if args[0]=="-m":
            if len(args)<2 or args[1] not in {"unittest","compileall","pytest"}: raise ValueError("only unittest, compileall, pytest modules allowed")
        elif args[0].startswith("-"): raise ValueError("Python flags/inline code blocked; pass a script path")
        else:
            script=_path(root,args[0],True)
            if not script.is_file() or script.suffix!=".py": raise ValueError("Python may execute only an existing .py file inside workspace")
            args=[str(script),*args[1:]]
        command=[argv[0],*args]
    elif exe=="pytest":
        command=[argv[0],*args]
    elif exe=="git":
        if not args or args[0] not in {"status","diff","log","ls-files","show"}: raise ValueError("only read-only git status/diff/log/ls-files/show allowed")
        if any(x in {"push","commit","checkout","reset","clean","fetch","pull","apply","config","rm","add"} for x in args): raise ValueError("git write/network command blocked")
        # Read-only subcommands can still write outside the workspace or run
        # external helpers if dangerous options are passed (e.g. diff --output,
        # --ext-diff, or --textconv). Keep this tool strictly observational.
        blocked_git_options = {
            "-o", "--output", "--ext-diff", "--external-diff", "--textconv",
            "--git-dir", "--work-tree", "--config-env", "--exec-path",
            "--upload-pack", "--receive-pack", "--no-index",
        }
        if any(arg in blocked_git_options or any(arg.startswith(option + "=") for option in ("--output", "--git-dir", "--work-tree", "--config-env", "--exec-path", "--upload-pack", "--receive-pack")) for arg in args):
            raise ValueError("git option may write outside the workspace or execute external helpers")
        command=[argv[0],*args]
    else: raise ValueError("executable not allowlisted; use python/python3, pytest or read-only git")
    env={"PATH":os.environ.get("PATH",""),"HOME":str(Path.home()),"PYTHONIOENCODING":"utf-8","PYTHONUTF8":"1"}
    done=subprocess.run(command,cwd=str(workdir),env=env,capture_output=True,text=True,timeout=timeout_seconds,check=False,shell=False)
    return {"ok":done.returncode==0,"argv":command,"cwd":str(workdir),"returncode":done.returncode,"stdout":done.stdout[-24000:],"stderr":done.stderr[-12000:]}

def execute_tool(name:str,args:dict[str,Any],workspace:Path)->dict[str,Any]:
    root=workspace.resolve()
    if name=="list_files": return _list(root,args.get("path","."))
    if name=="read_file": return _read(root,args.get("path",""))
    if name=="write_file": return _write(root,args.get("path",""),args.get("content",""))
    if name=="run_command": return _run(root,args.get("argv"),args.get("cwd","."),args.get("timeout_seconds",60))
    if name=="fetch_url": return _fetch_url(args.get("url",""))
    return {"ok":False,"error":f"Unknown tool: {name}"}
