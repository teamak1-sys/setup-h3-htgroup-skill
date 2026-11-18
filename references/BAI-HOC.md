# BÀI HỌC — nhật ký lỗi của /setup-h3-htgroup

Đọc tệp này **trước mỗi lần chạy** (bước 0). Gặp lỗi mới thì **nối một dòng** vào
bảng dưới (bước 4). Không ghi lại lỗi đã có.

| Ngày | Hiện tượng | Nguyên nhân | Cách tránh |
| --- | --- | --- | --- |
| 2026-11-17 | `modal setup` báo «Token flow did not complete in time» | trình duyệt không kịp xác nhận | operator hoàn thành đăng nhập lại qua trình duyệt, không dán token vào lệnh/chat |
| 2026-11-17 | Sau `modal app stop` gọi URL trả 404 mãi | stop xong phải deploy lại mới sống | bật máy = `modal deploy`, đừng chỉ gọi URL |
| 2026-11-17 | Script PowerShell tiếng Việt bị xô dấu trên Windows | lưu UTF-8 không BOM, PowerShell 5.1 đọc ANSI | lưu UTF-8 có BOM, hoặc dùng `pwsh`, hoặc ASCII |
| 2026-11-17 | `not in list` cho tệp `.safetensors` | thiếu trọng số trên ComfyUI | chạy lại `download_minimax_h3.sh` (video) / `download_models.sh --profile sdxl` (ảnh) |
| 2026-11-17 | `PyTorch không thấy CUDA` | sai bản wheel so driver | chạy lại `server_bootstrap.sh` với `TORCH_INDEX_URL=.../cu121` khớp driver |
| 2026-11-17 | ComfyUI «Required input is missing» | mẫu workflow thiếu tham số bắt buộc | đối chiếu `/object_info`, bổ sung tham số |
| 2026-11-17 | Cổng 8000 bị chiếm | phần mềm khác | giữ backend ở 8001; không tắt hay dùng phần mềm ở 8000 |
| 2026-11-18 | Dùng bảng Linux 19 mục trên Mac, hoặc status Volume chỉ đếm byte, rồi báo sẵn sàng | sai phạm vi kiểm; không có cổng riêng cho CPU/GPU; launcher dò cổng động | tách nhánh bằng setup.py, cố định cổng, kiểm header trên Volume và xin phép trước mọi lệnh GPU; kiểm workflow thật |
