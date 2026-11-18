"""CPU-only Modal verifier. Chỉ chạy sau phê duyệt chi phí CPU/storage.
Dùng đúng Volume của app HT-Group, không deploy GPU, không đọc khóa.
"""
from pathlib import Path
import json, subprocess, sys
import modal

def _resolve_root():
    import os
    env = os.environ.get("HT_PROJECT_ROOT", "").strip()
    if env and Path(env).expanduser().is_dir():
        return Path(env).expanduser().resolve()
    default = Path.home()/"TAN-CONG-TOP-VIEW"
    if default.is_dir():
        return default.resolve()
    for base in (Path.cwd(), Path.home()/"projects", Path.home()/"code", Path("/opt"), Path("/srv"), Path("/workspace"), Path("/data")):
        cand = base/"TAN-CONG-TOP-VIEW"
        if cand.is_dir():
            return cand.resolve()
    return default
ROOT=_resolve_root()
app=modal.App("topview-h3-weight-check")
volume=modal.Volume.from_name("topview-comfy-data",create_if_missing=False)
image=(modal.Image.debian_slim(python_version="3.11")
       .add_local_file(str(ROOT/"scripts/verify_weights.py"),"/opt/verify_weights.py")
       .add_local_file(str(ROOT/"scripts/verify_image_weights.py"),"/opt/verify_image_weights.py"))
@app.function(image=image,volumes={"/data":volume},timeout=180,cpu=1,memory=1024)
def verify():
    result={}
    for key,script in (("h3","verify_weights.py"),("sdxl","verify_image_weights.py")):
        p=subprocess.run([sys.executable,"/opt/"+script,"--dir","/data/models","--json"],capture_output=True,text=True)
        try: data=json.loads(p.stdout)
        except ValueError: data={}
        result[key]={"ok":p.returncode==0 and data.get("ok") is True,"report":data}
    return result

@app.local_entrypoint()
def main():
    result=verify.remote()
    ok=result["h3"]["ok"] and result["sdxl"]["ok"]
    print("HT_SETUP_WEIGHT_REPORT="+json.dumps(result,ensure_ascii=False))
    if not ok: raise SystemExit(1)
