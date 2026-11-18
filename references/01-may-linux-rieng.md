# Linux A100 riêng (Vast/RunPod/máy nhà)

> Mọi lệnh dưới dùng `$HT_ROOT` = chỗ dự án trên máy đang chạy (đặt `HT_PROJECT_ROOT` khi máy có nhiều dự án; công cụ tự dò) và `$COMFY_DIR` = chỗ cài ComfyUI trên máy đó. Không tự dạo đĩa để đoán.

Chỉ đọc nhánh này khi operator đã chọn Linux. Máy điều khiển có thể là Mac; mọi lệnh dưới trên máy Linux đã chọn, trừ SSH. Chưa được đồng ý chi phí thì không thuê, không SSH vào máy trả phí. Máy riêng cần Linux x86_64, A100 40/80 GB, RAM 32 GB trở lên, đĩa khoảng 150 GB, HTTPS và driver phù hợp. Kiểm thực tế, không coi cấu hình đề xuất là đã đạt.

## 1. Sau approve-install: kiểm máy và chuyển mã

Dùng SSH user@host thật với host key đã được xác nhận, không dùng StrictHostKeyChecking=no. Trước khi SSH, xác nhận máy thuộc quyền operator. Trên Linux:
```bash
uname -s
python3 --version
nvidia-smi
df -h
free -h
```
Không chạy các lệnh Linux trên Mac. Cài gói thiếu với quyền operator:
```bash
sudo apt-get update
sudo apt-get install -y git curl ffmpeg python3-venv python3-pip tmux
```
Đưa mã bằng repo/commit được phép hoặc danh sách file nguồn đã kiểm. Không rsync nguyên cây dự án: loại trừ .env*, .tmp, .git, storage, DB, venv, provider config, token, log, media riêng và model. Không gửi bí mật hoặc dữ liệu phim sang nhà cung cấp. Nếu không có mã trên Linux, kiểm và xác nhận danh sách trước khi chép.

## 2. Môi trường backend và ComfyUI

```bash
cd "$HT_ROOT"
bash scripts/server_bootstrap.sh --with-comfyui
```
Script từ chối macOS, cài backend + ComfyUI v0.45.0, PyTorch theo TORCH_INDEX_URL. Nếu CUDA không thấy GPU, đối chiếu driver/wheel trước khi sửa; không tự chọn cu121 thay cu124 nếu chưa kiểm.
Kiểm độc lập:
```bash
"$HT_ROOT/.venv/bin/python" -c 'import fastapi,uvicorn,sqlalchemy,aiosqlite'
"$COMFY_DIR/.venv/bin/python" -c 'import torch; assert torch.cuda.is_available(); print(torch.cuda.get_device_name(0))'
ffprobe -version | head -1
```
Trên máy điều khiển chạy setup.py install.

## 3. Tải và kiểm model trước khi bật ComfyUI

```bash
cd "$HT_ROOT"
"$HT_ROOT/.venv/bin/pip" install -U "huggingface_hub[cli]"
PATH="$HT_ROOT/.venv/bin:$PATH" COMFY_MODELS="$COMFY_DIR/models" bash scripts/download_minimax_h3.sh
COMFY_MODELS="$COMFY_DIR/models" bash scripts/download_models.sh --profile sdxl
python3 scripts/verify_weights.py --dir "$COMFY_DIR/models"
python3 scripts/verify_image_weights.py --dir "$COMFY_DIR/models"
```
H3 khoảng 37 GB; SDXL ~6,94 GB. Nếu gated, operator tự đăng nhập; không đưa token vào chat. Header hợp lệ không thay SHA-256; --hash là kiểm sâu tùy chọn. ref2v, turbo, PH3, ACE và SFX là tùy chọn, không bắt tải nếu không cần. Dùng setup.py weights trên máy điều khiển để kiểm lại thật qua SSH.

## 4. Sau approve-gpu: chạy đúng cổng

Kiểm cổng/session trước; nếu cổng thuộc chương trình khác, báo CHẶN, không kill và không đổi cổng. Chỉ bật process chưa có:
```bash
tmux new -d -s comfyui 'cd "$COMFY_DIR" && .venv/bin/python main.py --listen 127.0.0.1 --port 8188'
curl -fsS http://127.0.0.1:8188/system_stats
```
Chờ /system_stats JSON thật, không poll vô hạn. setup.py start-gpu.
Chạy local backend và GUI, không bind backend ra Internet:
```bash
tmux new -d -s ht-backend 'export HT_COMFY_URLS=http://127.0.0.1:8188 HT_COMFY_SLOTS=1; cd "$HT_ROOT" && .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001'
# chờ health đạt rồi chạy GUI, ép cổng, không gọi start_studio.py hoặc serve.py CLI tự dò
tmux new -d -s ht-frontend 'cd "$HT_ROOT" && python3 -c '"'"'from serve import StudioFrontendHandler; from socketserver import TCPServer; TCPServer(("127.0.0.1",3001),StudioFrontendHandler).serve_forever()'"'"''
```
SSH tunnel nếu cần truy cập từ máy điều khiển:
```bash
ssh -N -L 3001:127.0.0.1:3001 -L 8001:127.0.0.1:8001 user@host
```
Nếu cổng local đã có tiến trình, không đè tunnel lên chúng. Truy cập đúng host; không gọi nhầm Mac rồi kết luận Linux khỏe.

## 5. Kiểm tổng thể

setup.py connect, setup.py verify. Cổng verify chạy server_verify.sh trên chính Linux và đối chiếu GPU/template nghiêm ngặt. Không dùng server_verify trên Mac. Không dùng server_first_run.sh để thử render, vì sẽ đi vào sinh thật nếu thiếu --skip-shot. Render thật là quy trình /auto-htgroup và cần phê duyệt riêng.
