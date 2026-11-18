# Checkpoint và lệnh điều khiển

Chạy trên Mac hoặc máy điều khiển, Python 3.9+. Không dùng lệnh cài kiểu "copy rồi chạy tất cả". Mỗi lệnh đúng một bước; mã khác 0 giữ nguyên trạng thái.

```bash
S="<chỗ gói kỹ năng>/scripts/setup.py"
RUN="<mã-phiên-đã-chọn>"
python3 "$S" status --run "$RUN"
```

init chỉ cho phiên mới. Sổ thật do công cụ giữ, mỗi run một tệp trạng thái; không chỉnh tay. Khi thiếu dữ liệu, hỏi đúng dữ kiện, không tạo run khác để lách lỗi.

| Lệnh | Điều kiện |
|---|---|
| init | chưa có run |
| lessons --value "đã đọc..." | sau khi đọc BAI-HOC.md |
| choose --route linux --target user@host | operator chọn đúng SSH host; local chỉ trên Linux |
| choose --route modal --target PROFILE | operator xác nhận tên profile thật; không dùng tên ví dụ |
| prepare | kiểm dự án; Modal kiểm Mac local |
| approve-install --value "đồng ý" | chỉ sau lời đồng ý chi phí cài/tải/CPU/storage |
| install | cài xong theo nhánh; kiểm venv/CLI/profile/CUDA thật |
| weights [--download] | Modal CPU đọc header/size; --download chỉ khi cần và được phép; Linux kiểm ngay trên máy |
| approve-gpu --value "đồng ý" | đã đủ model và operator trả lời đồng ý GPU |
| start-gpu | Modal deploy đúng profile, Linux kiểm ComfyUI đang chạy |
| connect | backend trỏ đúng GPU đã chọn |
| verify | Linux 19/19 + strict GPU; Modal local + strict GPU + Volume |
| finish --value "..." | đã verify và ghi bài học |
| status | chỉ đọc state, không gọi mạng/GPU |

Ví dụ: python3 "$S" weights --run "$RUN" ; không chạy hết bảng như một shell script.
Nếu Modal CPU báo thiếu hoặc hỏng, kiểm nguyên nhân; --download dùng app CPU của HT-Group. App tải cũ bỏ qua file đã có kích thước dương, nên file hỏng có thể cần cách tải lại có kiểm soát; không tự xóa.
Check-local và selftest được phép chạy khi review skill, không tạo tác vụ thuê máy.

Các cổng:
- Weights: 4 H3 và SDXL có header hợp lệ, SDXL đúng 6.938.078.334 byte. Chưa hash toàn tệp, ghi rõ.
- GPU: A100 CUDA đủ VRAM, /system_stats, /object_info có dữ liệu, compile và đối chiếu input/model của H3 i2v/t2v và SDXL i2i/t2i. Nếu optional thiếu báo riêng.
- Kết thúc: không có công việc sinh thử; không tự nhận là đã render thành công.

Nếu lỗi mạng trong lúc deploy, trước khi chạy lại phải kiểm qua UI Modal xem app đã được deploy chưa (chỉ sau phép GPU vẫn còn hiệu lực); không tự deploy lặp nhiều lần. Nếu operator đã dừng máy/thu hồi đồng ý, không tiếp tục bằng phê duyệt cũ; bắt đầu run kiểm lại với quyền mới.
