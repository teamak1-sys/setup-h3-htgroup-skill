# Modal A100 — Mac điều khiển, Volume lưu model, GPU sinh

> Mọi lệnh dưới dùng `$HT_ROOT` = chỗ dự án trên máy đang chạy (đặt `HT_PROJECT_ROOT` khi máy có nhiều dự án; công cụ tự dò) và `$COMFY_DIR` = chỗ cài ComfyUI trên máy đó. Không tự dạo đĩa để đoán.

Máy Mac chỉ cài máy chủ dữ liệu, giao diện và CLI, không tải 44 GB model vào Mac. Xác nhận profile Modal thật của operator; không đoán tài khoản/workspace. Chỉ gọi CPU/storage sau approve-install; chỉ gọi GPU sau approve-gpu. Ngay cả HTTP /system_stats, /object_info tới endpoint Modal cũng có thể đánh thức GPU và tính giờ.

## 1. Mac local

Trước prepare, kiểm dự án và venv. Nếu thiếu, cài phụ thuộc local đúng dự án. Không dùng start_studio.py tự dò từ 8000. Kiểm cổng trước; nếu bị phần mềm khác giữ, báo lỗi, không kill. Khởi động từng tiến trình chỉ khi cần:
```bash
cd "$HT_ROOT"/backend
"$HT_ROOT/.venv/bin/python" -m uvicorn app.main:app --host 127.0.0.1 --port 8001
# tiến trình khác, sau health:
cd "$HT_ROOT"/frontend
python3 -c 'from serve import StudioFrontendHandler; from socketserver import TCPServer; TCPServer(("127.0.0.1",3001),StudioFrontendHandler).serve_forever()'
```
Backend 8001 và giao diện /studio/index.html cổng 3001 phải đạt; setup.py check-local không gọi GPU.

## 2. CLI và tài khoản

Sau approve-install, nếu CLI chưa có:
```bash
cd "$HT_ROOT"
python3 -m venv .tmp/modal-venv
.tmp/modal-venv/bin/pip install modal
```
Nếu chưa đăng nhập, operator tự hoàn tất browser:
```bash
MODAL_CONFIG_PATH="$PWD/.tmp/modal.toml" .tmp/modal-venv/bin/modal setup
```
Không đọc file modal.toml, không yêu cầu dán token, không chạy token set --token-secret trong shell. Giữ file cấu hình quyền 600. Người dùng xác nhận profile thật; setup.py dùng MODAL_PROFILE đúng tên và loại credential override khỏi môi trường gọi CLI. install kiểm CLI/profile local.

## 3. Volume, tải CPU và kiểm header

Chạy trên máy điều khiển:
```bash
S="<chỗ gói kỹ năng>/scripts/setup.py"
python3 "$S" weights --run "$RUN"
# nếu thiếu model và đã đồng ý tải:
python3 "$S" weights --run "$RUN" --download
```
weights --download gọi app docs/thu-modal-a100/app.py --action download, chạy CPU, có thể phát sinh phí CPU/storage/network, không tốn giờ GPU. Verifier scripts/modal_verify.py chạy CPU trên Volume topview-comfy-data và kiểm hai script chuẩn ở chỗ model trên Volume. Khác với --action status chỉ đếm tệp và byte.
Nếu Volume chưa có hoặc model hỏng, dừng báo lỗi; không tự xóa Volume hay ghi đè file khác. Model optional không phải bắt buộc. Chỉ header/size đã được kiểm, hash toàn bộ và render thật vẫn chưa kiểm.

## 4. Bật GPU sau phép riêng

Sau khi checkpoint gpu_approval và operator trả lời đồng ý, chạy approve-gpu, rồi start-gpu. Wrapper dùng app đúng profile và nhận URL thật từ output deploy. Nếu URL không trả, không đoán, không lặp deploy mù. Kiểm app trên UI Modal. A100-80GB, ComfyUI v0.45.0 là cấu hình trong app hiện có, không phải bằng chứng GPU đang chạy.
Khai đúng URL tại Cài đặt → Nhà cung cấp sinh → Máy GPU, bật mục phù hợp, cho phép URL công khai chỉ đối với endpoint operator vừa xác nhận. Không mở backend local ra Internet. Chạy connect, verify.
Cổng verify kiểm Mac, GPU A100 CUDA, /system_stats, /object_info, workflow bắt buộc và model được loader chấp nhận. Không dùng script 19 mục Linux hoặc quét chỗ model ComfyUI trên Mac.

## 5. Quản lý chi phí và tắt

GPU có scaledown_window=600 trong app hiện tại. Không hứa đã tắt chỉ vì im lặng 10 phút. Nếu operator xác nhận muốn tắt và không có task cần giữ, dùng profile đã chọn:
```bash
cd "$HT_ROOT"
MODAL_CONFIG_PATH="$PWD/.tmp/modal.toml" MODAL_PROFILE="$PROFILE" .tmp/modal-venv/bin/modal app stop -y topview-comfyui
```
Kiểm trạng thái bằng UI Modal, không gọi URL GPU sau stop. Sau app stop có thể cần deploy lại, không tự thức bằng HTTP. Không tự bật lại khi chạy setup review. Không tuyên bố đã sinh video, giao việc đó cho /auto-htgroup sau xin phép riêng.
