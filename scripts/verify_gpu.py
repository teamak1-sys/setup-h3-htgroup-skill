#!/usr/bin/env python3
"""Kiểm máy GPU qua API thật; không gửi workflow sinh media."""
import argparse, json, pathlib, re, sys, urllib.request, urllib.parse
def _resolve_root():
    import os
    env = os.environ.get("HT_PROJECT_ROOT", "").strip()
    if env and pathlib.Path(env).expanduser().is_dir():
        return pathlib.Path(env).expanduser().resolve()
    default = pathlib.Path.home()/"TAN-CONG-TOP-VIEW"
    if default.is_dir():
        return default.resolve()
    for base in (pathlib.Path.cwd(), pathlib.Path.home()/"projects", pathlib.Path.home()/"code", pathlib.Path("/opt"), pathlib.Path("/srv"), pathlib.Path("/workspace"), pathlib.Path("/data")):
        cand = base/"TAN-CONG-TOP-VIEW"
        if cand.is_dir():
            return cand.resolve()
    return default
ROOT=_resolve_root()
def need(ok,msg):
    if not ok: raise ValueError(msg)
def read_json(url,timeout=30):
    with urllib.request.urlopen(url,timeout=timeout) as r:
        need(r.status==200,"HTTP không phải 200")
        d=json.load(r)
        need(isinstance(d,dict) and d,"JSON rỗng/sai định dạng")
        return d
def valid_url(url):
    p=urllib.parse.urlsplit(url)
    need(p.scheme in ("http","https") and p.hostname and not p.username and not p.password and not p.query and not p.fragment and p.path in ("","/"),"URL phải là gốc HTTP(S), không có token/query")
    return url.rstrip("/")
def validate_gpu(stats):
    devices=stats.get("devices") or []
    candidates=[d for d in devices if isinstance(d,dict) and "cuda" in str(d.get("type","")).lower() and "A100" in str(d.get("name","")).upper() and int(d.get("vram_total") or 0)>=39_000*1024**2]
    need(candidates,"không có CUDA A100 đủ VRAM (>=39.000 MiB)")
    return len(candidates)
def validate_templates(info):
    sys.path.insert(0,str(ROOT/"backend"))
    from scripts.check_workflow_templates import sample_requests, validate_graph
    from app.services import workflow_compiler as comp
    required={"image_to_video","text_to_video","text_to_image","image_to_image"}
    checked=set(); failures=[]; optional=[]
    for request in sample_requests():
        picked=comp.pick_template(request)
        tag=request["task_type"]
        if not picked:
            if tag in required: failures.append(tag+": thiếu mẫu")
            continue
        file,template=picked
        is_optional=bool((template.get("_ht") or {}).get("optional_weights"))
        graph=comp.compile_for(request)
        if graph is None:
            if not is_optional: failures.append(tag+": không compile được")
            else: optional.append(tag)
            continue
        errors,warnings=validate_graph(graph,info)
        # Không bỏ qua thiếu model như checker chung; ảnh mẫu không có file trên GPU là bình thường.
        weights=[w for w in warnings if re.search(r"\.(safetensors|ckpt|pt|gguf|bin|pth)\b",w,re.I)]
        if is_optional:
            if errors or weights: optional.append(tag)
            continue
        checked.add(tag)
        failures.extend(f"{tag}: {x}" for x in errors+weights)
    need(required<=checked,"chưa kiểm đủ 4 template bắt buộc: "+str(sorted(required-checked)))
    need(not failures,"mẫu/model GPU lỗi: "+"; ".join(failures[:12]))
    return {"required_templates":sorted(checked),"optional_unavailable":sorted(set(optional))}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("url")
    args=ap.parse_args(); url=valid_url(args.url)
    stats=read_json(url+"/system_stats")
    count=validate_gpu(stats)
    info=read_json(url+"/object_info",90)
    report=validate_templates(info)
    report.update(ok=True,gpu_count=count,object_nodes=len(info))
    print(json.dumps(report,ensure_ascii=False))
if __name__=="__main__":
    try: main()
    except Exception as e:
        print("CHẶN: "+str(e),file=sys.stderr); sys.exit(1)
