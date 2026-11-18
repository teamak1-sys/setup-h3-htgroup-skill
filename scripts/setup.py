#!/usr/bin/env python3
"""Sổ checkpoint cài H3. Mọi cloud/GPU command qua cổng xin phép; status chỉ đọc."""
import argparse, json, os, pathlib, platform, re, shlex, shutil, subprocess, sys, tempfile, urllib.request, urllib.parse
from datetime import datetime, timezone
P=pathlib.Path


def _resolve_root() -> P:
    """Thư mục dự án trên máy ĐANG chạy: HT_PROJECT_ROOT -> ~/TAN-CONG-TOP-VIEW -> dò vài chỗ."""
    env = os.environ.get("HT_PROJECT_ROOT", "").strip()
    if env:
        cand = P(env).expanduser()
        if cand.is_dir():
            return cand.resolve()
    default = P.home() / "TAN-CONG-TOP-VIEW"
    if default.is_dir():
        return default.resolve()
    for base in (P.cwd(), P.home() / "projects", P.home() / "code", P.home() / "Documents", P("/opt"), P("/srv"), P("/workspace"), P("/data")):
        cand = base / "TAN-CONG-TOP-VIEW"
        if cand.is_dir():
            return cand.resolve()
    return default


ROOT=_resolve_root()
SKILL=P(__file__).resolve().parents[1]
BASE="http://127.0.0.1:8001"
STAGES=["lessons","target","prepare","install_approval","install","weights","gpu_approval","gpu","connect","verify","lessons_end","done"]
REQ=["scripts/server_bootstrap.sh","scripts/server_verify.sh","scripts/check_comfy_ready.py","scripts/download_minimax_h3.sh","scripts/download_models.sh","scripts/verify_weights.py","scripts/verify_image_weights.py","backend/scripts/check_workflow_templates.py","backend/requirements.txt","frontend/serve.py","docs/thu-modal-a100/app.py"]
def need(ok,msg):
    if not ok: raise ValueError(msg)
def stamp(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads(p.read_text())
def save(p,s):
    p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=p.parent)
    with os.fdopen(fd,"w",encoding="utf-8") as f: json.dump(s,f,ensure_ascii=False,indent=2); f.write("\n")
    os.replace(tmp,p)
def stage(s,st): need(s["stage"]==st,"đang ở "+s["stage"]+", không được nhảy tới "+st)
def move(s,to):
    need(STAGES.index(to)==STAGES.index(s["stage"])+1,"không được nhảy bước")
    s["history"].append({"stage":s["stage"],"at":stamp()}); s["stage"]=to
def choice(route,target):
    need(route in ("linux","modal"),"chọn linux hoặc modal")
    if route=="linux":
        need(target=="local" or bool(re.fullmatch(r"[a-zA-Z0-9_.-]+@[a-zA-Z0-9][a-zA-Z0-9.-]*",target or "")),"Linux cần local hoặc user@host thật, không có tùy chọn shell")
        if target=="local": need(platform.system()=="Linux","Mac không phải máy Linux GPU")
    else: need(bool(re.fullmatch(r"[A-Za-z0-9_.-]{1,100}",target or "")) and target!="modal","Modal cần tên profile thật do operator xác nhận")
def run(cmd,timeout=300,env=None,cwd=ROOT,weight_diagnostic=False):
    p=subprocess.run(cmd,cwd=cwd,env=env,capture_output=True,text=True,timeout=timeout)
    if weight_diagnostic and p.returncode!=0 and "HT_SETUP_WEIGHT_REPORT=" in p.stdout:
        return p.stdout
    need(p.returncode==0,"lệnh "+P(str(cmd[0])).name+" thất bại (mã "+str(p.returncode)+"); xem nguyên nhân qua giao diện/nhật ký đã che bí mật")
    return p.stdout+(("\n"+p.stderr) if "deploy" in cmd else "")
def get(url):
    with urllib.request.urlopen(url,timeout=10) as r:
        need(r.status==200,"HTTP không đạt")
        return json.load(r)
def local_check():
    need(ROOT.is_dir() and all((ROOT/f).is_file() for f in REQ),"thiếu dự án hoặc script nguồn")
    need((ROOT/"backend/.venv/bin/python").is_file(),"thiếu venv backend")
    run([str(ROOT/"backend/.venv/bin/python"),"-c","import fastapi,uvicorn,sqlalchemy,aiosqlite,greenlet"])
    for tool in ("ffmpeg","ffprobe"):
        need(shutil.which(tool) or P("/opt/homebrew/bin",tool).is_file(),"thiếu "+tool)
    h=get(BASE+"/health")
    need(h.get("ok") is True and h.get("database",{}).get("status")=="connected","backend 8001/SQLite chưa khỏe")
    with urllib.request.urlopen("http://127.0.0.1:3001/studio/index.html",timeout=10) as r:
        need(r.status==200 and "html" in r.headers.get("Content-Type","").lower(),"frontend 3001 không trả HTML")
    with urllib.request.urlopen("http://127.0.0.1:3001/prototype/index.html",timeout=10) as r:
        need(r.status==200 and "topview" in r.read().decode("utf-8","replace").lower(),"giao diện chính không thuộc TOPVIEW")
    # Chỉ liệt kê schema MCP; không gọi comfy_status/generation, tránh đánh thức GPU.
    req=urllib.request.Request(BASE+"/mcp",data=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}).encode(),headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=10) as r: tools=json.load(r).get("result",{}).get("tools",[])
    names={t.get("name") for t in tools}
    need({"canvas_state_get","generation_submit","generation_refresh","timeline_export"}<=names,"MCP thiếu lệnh cần")
    return {"backend":8001,"frontend":3001,"mcp_tools":len(names),"ffprobe":True}
def linux(s,cmd,timeout=300):
    need(s["route"]=="linux" and s.get("install_consent"),"chưa có phép truy cập/cài trên Linux")
    if s["target"]=="local":
        line='cd '+shlex.quote(str(ROOT))+' && '+cmd
        return run(["bash","-lc",line],timeout)
    # Máy Linux từ xa: thư mục dự án trên máy đó lấy theo HT_REMOTE_ROOT,
    # mặc định $HOME/TAN-CONG-TOP-VIEW và do shell từ xa mở rộng $HOME.
    remote_root = os.environ.get("HT_REMOTE_ROOT","").strip() or "$HOME/TAN-CONG-TOP-VIEW"
    line='cd '+(('"'+remote_root+'"') if "$" in remote_root else shlex.quote(remote_root))+' && '+cmd
    return run(["ssh","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=10",s["target"],"bash -lc "+shlex.quote(line)],timeout)
def modal_env(profile):
    # Không mở file cấu hình/token. CLI tự xử lý; chỉ kiểm đường dẫn.
    v=ROOT/".tmp/modal-venv/bin/modal"
    cfg=ROOT/".tmp/modal.toml"
    need(v.is_file(),"thiếu Modal CLI; cài theo tài liệu trước")
    need(cfg.is_file(),"chưa đăng nhập Modal; người dùng tự hoàn thành modal setup")
    env=dict(os.environ); env["MODAL_CONFIG_PATH"]=str(cfg); env["MODAL_PROFILE"]=profile
    for key in ("MODAL_TOKEN_ID","MODAL_TOKEN_SECRET","MODAL_OAUTH_REFRESH_TOKEN","MODAL_OAUTH_CLIENT_ID","MODAL_OAUTH_CLIENT_SECRET","MODAL_OAUTH_JWT_KEY"): env.pop(key,None)
    return str(v),env
def modal_run(s,args,timeout=1800,gpu=False,weight_diagnostic=False):
    need(s["route"]=="modal" and s.get("install_consent"),"chưa có phép chi phí Modal")
    if gpu: need(s["stage"]=="gpu" and s.get("gpu_consent") and s.get("weight_report"),"chưa đủ cổng GPU")
    exe,env=modal_env(s["target"])
    return run([exe]+args,timeout,env,weight_diagnostic=weight_diagnostic)
def weight_report(text):
    lines=[x.split("HT_SETUP_WEIGHT_REPORT=",1)[1] for x in text.splitlines() if "HT_SETUP_WEIGHT_REPORT=" in x]
    need(len(lines)==1,"không nhận được báo cáo kiểm weight thật trên Volume")
    d=json.loads(lines[0]); h=d.get("h3",{}); i=d.get("sdxl",{})
    files=h.get("report",{}).get("files",[])
    bad=[str(x.get("name") or "H3") for x in files if x.get("ok") is not True]
    if len(files)!=4: bad.append("H3 chưa đủ 4 file")
    if i.get("ok") is not True: bad.append("SDXL")
    need(not bad,"model thiếu/hỏng: "+", ".join(bad))
    need(h.get("ok") is True and len(files)==4 and all(x.get("ok") is True for x in files) and i.get("ok") is True and i.get("report",{}).get("header_ok") is True and i.get("report",{}).get("size_bytes")==6938078334,"H3/SDXL thiếu, cụt hoặc hỏng header")
    return {"h3_files":4,"sdxl_files":1,"method":"header+size","at":stamp()}
def modal_url(out):
    urls=re.findall(r"https://[a-zA-Z0-9-]+--topview-comfyui-comfy(?:\.[a-zA-Z0-9-]+)*\.modal\.run",out)
    urls=list(dict.fromkeys(urls)); need(len(urls)==1,"không nhận URL ComfyUI duy nhất từ deploy; không đoán workspace")
    return urls[0]
def require_provider(url):
    d=get(BASE+"/api/v1/media/providers")
    need(d.get("ok") is True and any(x.get("enabled") is not False and str(x.get("base_url","")).rstrip("/")==url.rstrip("/") for x in d.get("comfy",[])),"backend chưa có máy GPU đã bật đúng URL trong Cài đặt > Nhà cung cấp sinh")
def report_linux_weights(out):
    lines=[x for x in out.splitlines() if x.startswith("HT_SETUP_LINUX_WEIGHTS_OK")]
    need(len(lines)==1,"Linux chưa có kết quả kiểm model")
    return {"h3_files":4,"sdxl_files":1,"method":"header+size","at":stamp()}
def linux_ready(out):
    need("Đã kiểm tra 19 mục: 19 đạt, 0 hỏng." in out and "TẤT CẢ ĐÚNG" in out,"server_verify chưa đạt đúng 19/19")
def gpu_report(out):
    d=json.loads(out.strip().splitlines()[-1])
    need(d.get("ok") is True and d.get("gpu_count",0)>0 and d.get("object_nodes",0)>0 and {"image_to_video","text_to_video","text_to_image","image_to_image"}<=set(d.get("required_templates",[])),"GPU/template chưa được kiểm đủ")
    return d
def approval(s,st,value):
    stage(s,st)
    need(value=="đồng ý","chỉ chấp nhận đồng ý rõ ràng của operator ở lượt hỏi hiện tại")
    if st=="gpu_approval": need(s.get("weight_report"),"chưa có bằng chứng trọng số")
    s["install_consent" if st=="install_approval" else "gpu_consent"]=stamp()
    move(s,STAGES[STAGES.index(st)+1])
def selftest():
    cases=[]
    def reject(fn):
        try: fn(); return False
        except ValueError: return True
    cases.append(("không nhảy bước",reject(lambda:move({"stage":"lessons","history":[]},"gpu"))))
    cases.append(("không chọn nhà cung cấp thay operator",reject(lambda:choice("other",""))))
    cases.append(("Linux SSH không chấp nhận shell option",reject(lambda:choice("linux","-o bad"))))
    cases.append(("không nhận ok mơ hồ",reject(lambda:approval({"stage":"install_approval"},"install_approval","ok"))))
    cases.append(("không xin GPU khi chưa có weights",reject(lambda:approval({"stage":"gpu_approval"},"gpu_approval","đồng ý"))))
    cases.append(("chặn lệnh Modal chưa đồng ý",reject(lambda:modal_run({"route":"modal"},["deploy"],gpu=True))))
    cases.append(("chặn deploy trước consent GPU",reject(lambda:modal_run({"route":"modal","install_consent":True,"stage":"gpu"},["deploy"],gpu=True))))
    cases.append(("chặn status chỉ có tên/dung lượng",reject(lambda:weight_report('total: 44 GiB'))))
    cases.append(("chặn H3 thiếu tệp",reject(lambda:weight_report('HT_SETUP_WEIGHT_REPORT='+json.dumps({"h3":{"ok":True,"report":{"files":[{"ok":True}]}},"sdxl":{"ok":True}})))))
    good={"h3":{"ok":True,"report":{"files":[{"ok":True}]*4}},"sdxl":{"ok":True,"report":{"header_ok":True,"size_bytes":6938078334}}}
    cases.append(("header + kích thước đủ qua",weight_report('HT_SETUP_WEIGHT_REPORT='+json.dumps(good))["h3_files"]==4))
    cases.append(("không đoán URL",reject(lambda:modal_url("deploy done"))))
    cases.append(("đọc URL từ deploy",modal_url("https://abc--topview-comfyui-comfy.us-east.modal.run")=="https://abc--topview-comfyui-comfy.us-east.modal.run"))
    cases.append(("19 mục thiếu một bị chặn",reject(lambda:linux_ready("Đã kiểm tra 19 mục: 18 đạt, 1 hỏng."))))
    cases.append(("19/19 qua",linux_ready("Đã kiểm tra 19 mục: 19 đạt, 0 hỏng. TẤT CẢ ĐÚNG") is None))
    cases.append(("GPU báo skip không qua",reject(lambda:gpu_report('{"ok":true,"gpu_count":1,"object_nodes":0}'))))
    for label,ok in cases: print(("ĐẠT " if ok else "HỎNG ")+label)
    print(f"{sum(ok for _,ok in cases)}/{len(cases)} tình huống đúng")
    return 0 if all(ok for _,ok in cases) else 1
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("action",choices=["init","status","lessons","choose","prepare","approve-install","install","weights","approve-gpu","start-gpu","connect","verify","finish","selftest","check-local"])
    ap.add_argument("--run"); ap.add_argument("--route"); ap.add_argument("--target"); ap.add_argument("--value"); ap.add_argument("--download",action="store_true")
    a=ap.parse_args()
    if a.action=="selftest": return selftest()
    if a.action=="check-local": print(json.dumps(local_check(),ensure_ascii=False)); return 0
    need(a.run and re.fullmatch(r"[A-Za-z0-9_-]{1,80}",a.run),"thiếu/sai --run")
    p=ROOT/".tmp/setup-h3-htgroup"/a.run/"state.json"
    if a.action=="init":
        need(not p.exists(),"run đã có; dùng status")
        save(p,{"stage":"lessons","history":[]}); print(p); return 0
    s=read(p); action=a.action
    if action=="status": print(json.dumps(s,ensure_ascii=False,indent=2)); return 0
    if action=="lessons":
        stage(s,"lessons"); need((SKILL/"references/BAI-HOC.md").is_file() and a.value,"đọc bài học, xác nhận"); move(s,"target")
    elif action=="choose":
        stage(s,"target"); choice(a.route,a.target); s.update(route=a.route,target=a.target); move(s,"prepare")
    elif action=="prepare":
        stage(s,"prepare"); need(ROOT.is_dir() and all((ROOT/f).is_file() for f in REQ),"thiếu dự án hoặc scripts")
        if s["route"]=="modal": s["local_report"]=local_check()
        move(s,"install_approval")
    elif action=="approve-install": approval(s,"install_approval",a.value)
    elif action=="install":
        stage(s,"install"); need(s.get("install_consent"),"chưa duyệt cài")
        if s["route"]=="modal":
            exe,env=modal_env(s["target"]); run([exe,"--version"],env=env)
            need(run([exe,"profile","current"],env=env).strip()==s["target"],"profile Modal không đúng")
            # Chỉ CLI local; không đọc file token và không gọi cloud ở bước này.
        else:
            out=linux(s,'test "$(uname -s)" = Linux && nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits | grep -q A100 && test -x backend/.venv/bin/python && backend/.venv/bin/python -c "import fastapi,uvicorn,sqlalchemy,aiosqlite" && "$HOME/ComfyUI/.venv/bin/python" -c "import torch; assert torch.cuda.is_available()" && command -v ffmpeg && command -v ffprobe')
            need(out.strip(),"Linux chưa kiểm được môi trường")
        move(s,"weights")
    elif action=="weights":
        stage(s,"weights"); need(s.get("install_consent"),"chưa duyệt chi phí cài")
        if s["route"]=="modal":
            if a.download: modal_run(s,["run",str(ROOT/"docs/thu-modal-a100/app.py"),"--action","download"],timeout=10800)
            out=modal_run(s,["run",str(SKILL/"scripts/modal_verify.py")],timeout=900,weight_diagnostic=True)
            s["weight_report"]=weight_report(out)
        else:
            need(not a.download,"Linux tải theo reference trên đúng máy; bước này chỉ kiểm")
            out=linux(s,'python3 scripts/verify_weights.py --dir "$HOME/ComfyUI/models" && python3 scripts/verify_image_weights.py --dir "$HOME/ComfyUI/models" && echo HT_SETUP_LINUX_WEIGHTS_OK')
            s["weight_report"]=report_linux_weights(out)
        move(s,"gpu_approval")
    elif action=="approve-gpu": approval(s,"gpu_approval",a.value)
    elif action=="start-gpu":
        stage(s,"gpu"); need(s.get("gpu_consent") and s.get("weight_report"),"chưa đủ cổng GPU")
        if s["route"]=="modal":
            out=modal_run(s,["deploy",str(ROOT/"docs/thu-modal-a100/app.py")],timeout=1800,gpu=True)
            s["comfy_url"]=modal_url(out)
        else:
            # Linux chỉ xác minh ComfyUI đã được khởi động đúng nơi sau consent.
            out=linux(s,'curl -fsS --max-time 20 http://127.0.0.1:8188/system_stats')
            need(json.loads(out).get("devices"),"ComfyUI chưa chạy")
            s["comfy_url"]="http://127.0.0.1:8188"
        move(s,"connect")
    elif action=="connect":
        stage(s,"connect")
        need(s.get("gpu_consent") and s.get("comfy_url"),"chưa có máy GPU đúng run")
        if s["route"]=="modal": require_provider(s["comfy_url"])
        else: linux(s,'curl -fsS http://127.0.0.1:8001/health >/dev/null && curl -fsS http://127.0.0.1:3001/studio/index.html >/dev/null')
        move(s,"verify")
    elif action=="verify":
        stage(s,"verify"); need(s.get("gpu_consent") and s.get("weight_report"),"chưa đủ cổng xác nhận")
        if s["route"]=="linux":
            out=linux(s,'HT_FRONTEND_URL=http://127.0.0.1:3001/prototype COMFY_URL=http://127.0.0.1:8188 COMFY_MODELS="$HOME/ComfyUI/models" HT_COMFY_URLS=http://127.0.0.1:8188 bash scripts/server_verify.sh',timeout=600)
            linux_ready(out)
            strict=linux(s,"backend/.venv/bin/python -c "+shlex.quote((SKILL/"scripts/verify_gpu.py").read_text())+" http://127.0.0.1:8188",timeout=180)
            s["verify_report"]={"linux_checks":19,"passed":19,**gpu_report(strict)}
        else:
            require_provider(s["comfy_url"]); s["local_report"]=local_check()
            out=run([str(ROOT/"backend/.venv/bin/python"),str(SKILL/"scripts/verify_gpu.py"),s["comfy_url"]],timeout=180)
            s["verify_report"]=gpu_report(out)
        move(s,"lessons_end")
    elif action=="finish":
        stage(s,"lessons_end"); need(s.get("verify_report") and a.value and (SKILL/"references/BAI-HOC.md").is_file(),"chưa có kiểm thật/ghi bài học")
        s["render_test"]="not_run"; move(s,"done")
    save(p,s); print("CHECKPOINT="+s["stage"]); return 0
if __name__=="__main__":
    try: sys.exit(main())
    except Exception as e: print("CHẶN: "+str(e),file=sys.stderr); sys.exit(1)
