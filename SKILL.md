---
name: setup-h3-htgroup
description: "Nạp ngay khi operator gọi /setup-h3-htgroup, setup h3, cài h3, cài máy GPU, dựng máy phim, cài ComfyUI H3 hoặc tiếp tục cài HT-Group. Kiểm tra và cài môi trường HT-Group trên Linux A100 hoặc Modal A100 theo checkpoint: chọn đúng máy/tài khoản, kiểm Mac hoặc Linux, xin phép chi phí, cài môi trường, xác minh H3 và SDXL trên đúng nơi lưu, xin phép bật GPU, kết nối backend 8001/giao diện 3001, kiểm ComfyUI 8188 và workflow. Không tự thuê máy, không tự chạy thử video, không báo hoàn tất khi còn thiếu bằng chứng."
compatibility: "Python 3.9+; dự án HT-Group do công cụ tự tìm; Mac điều khiển Modal hoặc SSH Linux A100; ffmpeg/ffprobe; Modal CLI hoặc SSH theo nhánh."
---

# /setup-h3-htgroup — CÀI VÀ KIỂM MÁY H3 THEO CHECKPOINT

## Hợp đồng vận hành

Kích hoạt khi người dùng muốn cài, sửa hoặc tiếp tục cài hệ thống. Nếu họ chỉ yêu cầu kiểm/sửa skill, đọc tệp và chạy selftest/check-local, không thực thi cài đặt, không truy cập máy thuê. Trả lời tiếng Việt ngắn, nêu **đã kiểm chứng / suy luận / chưa kiểm chứng**, kèm lệnh và kết quả thật.

- Không tự chọn nhà cung cấp, SSH host, workspace/profile Modal hoặc thuê máy. Hỏi khi chưa biết; dữ kiện đã chốt thì dùng lại.
- Không đọc/in/copy API key, token, .env, media_providers.json hoặc modal.toml. Người dùng tự đăng nhập qua UI/browser; không xin họ dán token vào chat hoặc terminal log. Không truyền khoá từ máy khác.
- Không mở/chiếm cổng 8000 hoặc dừng phần mềm đang chạy trên đó. Backend 8001, frontend 3001, ComfyUI 8188. Không dùng start_studio.py vì tự dò cổng 8000–8050; không mở backend không xác thực ra Internet.
- CPU, storage, tải dữ liệu và thời gian thuê Linux/Modal có thể tốn tiền; phải xác nhận trước. Lời đồng ý cài CPU không cho phép bật GPU. Mọi deploy/health probe tới URL Modal có thể làm GPU thức: chỉ thực hiện sau cổng approve-gpu.
- Không chạy sinh video bằng server_first_run.sh hoặc first_shot.py; setup chỉ kiểm sẵn sàng, không thay quyền phê duyệt của /auto-htgroup.
- Không tin tên file, kích thước gần đúng, HTTP 200 hay mã thoát 0 khi checker báo bỏ qua. Phải kiểm đúng route, header trọng số, node/model/input và backend thật.
- Mỗi lần cài có RUN riêng. State trên đĩa là nguồn sự thật. Không tự sửa state.json, không nhảy checkpoint, không tạo run mới để né lỗi. Lỗi thì dừng đúng bước và sửa. Đọc đúng tệp tham chiếu của bước hiện tại, không đọc cả gói.

## Máy nào cần gì

- **Làm phim** (skill điều phối): máy khác không cần bản sao dự án, chỉ cần mạng tới máy chủ dữ liệu 8001. Skill này và skill điều phối dùng chung máy chủ đó.
- **Cài máy H3** (skill này): máy chạy lệnh cài **cần mã dự án** (script nguồn, môi trường Python của dự án) vì nó chạy/deploy chính mã đó; máy Linux/GPU nhận mã bằng cách kéo repo ngay trên máy đó, không chép từ máy điều khiển.
- Không đọc mã sản phẩm để "hiểu hệ thống"; lỗi thì báo chủ dự án, không tự sửa mã đang khoá.

## Lấy gói này ở đâu

- Địa chỉ: `https://github.com/teamak1-sys/setup-h3-htgroup-skill.git` (repo **riêng**, cần đăng nhập GitHub trên máy đích).
- Cài trên máy khác: `git clone https://github.com/teamak1-sys/setup-h3-htgroup-skill.git "<chỗ bộ nạp kỹ năng đọc>"`. Không có mạng hoặc không đăng nhập được thì nhận tệp nén của gói, giải nén vào đúng chỗ đó.
- Cập nhật: `git -C "<chỗ gói kỹ năng>" pull --ff-only`. Máy nào dùng bản cũ thì bảo chủ dự án cập nhật, không tự sửa tay cho khác bản.

## Sổ chạy bắt buộc

Đọc references/00-checkpoint.md lúc bắt đầu/tiếp tục. Dùng:

```bash
S="<chỗ gói kỹ năng>/scripts/setup.py"
python3 "$S" init --run "$RUN"
python3 "$S" status --run "$RUN"
```

Chỗ dự án: công cụ tự dò (đặt `HT_PROJECT_ROOT` khi máy có nhiều dự án). Không thấy thì dừng, hỏi người dùng kéo từ repo hoặc chỉ chỗ đã copy, không tự tạo chỗ rỗng. `setup.py` tự dò cùng cách.
Khi tiếp tục, lấy RUN hiện có trong "sổ chạy của skill (do công cụ giữ)"; không init lại. Trong các bước dưới, mỗi lệnh setup.py có thêm --run "$RUN". Chỉ chuyển khi mã thoát 0 và CHECKPOINT đúng. Chạy trên máy điều khiển; Linux command cài đặt chạy đúng máy SSH/local Linux, không chạy trên Mac.

| Checkpoint | Bằng chứng và hành động |
|---|---|
| lessons | đọc references/BAI-HOC.md; lessons --value "đã đọc..." |
| target | hỏi loại máy và host/profile thật; choose --route ... --target ... |
| prepare | mở đúng tài liệu Linux/Modal; kiểm dự án; Modal kiểm Mac 8001/3001/MCP/ffprobe; prepare |
| install_approval | hỏi chi phí CPU/storage/máy Linux; approve-install --value "đồng ý" sau phản hồi |
| install | cài đúng nhánh, xác thực tài khoản qua browser nếu cần; install |
| weights | tải khi cần rồi kiểm H3 4/4 + SDXL 1/1 ở nơi model thực nằm; weights |
| gpu_approval | hỏi có đồng ý bật/kiểm GPU thuê tốn tiền không; dừng; approve-gpu --value "đồng ý" |
| gpu | Modal deploy qua start-gpu; Linux khởi động ComfyUI sau phép rồi start-gpu kiểm |
| connect | kết nối backend với đúng URL; connect |
| verify | chạy kiểm nhánh riêng; verify |
| lessons_end | ghi lỗi mới nếu có; finish --value "đã ghi..." |
| done | status; báo mức sẵn sàng, model, URL/cổng, chưa render thật |

## Thứ tự thực hiện theo nhánh

### lessons → target → prepare
Đọc BAI-HOC.md. Nếu chưa biết máy, hỏi đúng một câu: "Bạn muốn cài trên Linux A100 riêng (Vast/RunPod/máy nhà, SSH user@host) hay Modal A100 (tên profile của tài khoản bạn)?" Không chọn chỉ vì đã có một cấu hình cũ.
- Linux: đọc references/01-may-linux-rieng.md, choose --route linux --target user@host (local chỉ khi máy thực sự Linux). Không SSH khi chưa được phép.
- Modal: đọc references/02-may-thue-modal.md, xác nhận tên profile do operator chọn, choose --route modal --target TEN_PROFILE. Mac là máy điều khiển, không cài ComfyUI/model lên Mac. Kiểm dịch vụ local nếu chưa chạy, dùng đúng cổng cố định theo tài liệu.
- prepare kiểm nguồn và (nhánh Modal) local thật. Nếu thiếu, sửa đúng môi trường, không bỏ qua.

### install_approval → install → weights
Xin phép chi phí riêng cho tải/cài/CPU/storage; Linux thuê có thể tính giờ ngay khi đang cài. Chỉ ghi approve-install sau lời đồng ý rõ ràng; "làm tiếp" không phải đồng ý chi phí.
- Linux: cài gói, đồng bộ mã không có bí mật, tạo venv, ComfyUI và CUDA theo tham chiếu; install kiểm thật trên host đã chọn. Tải H3/SDXL rồi weights kiểm bằng hai verifier trên Linux.
- Modal: cài CLI nếu thiếu; operator đăng nhập profile đúng bằng browser. install xác nhận CLI/profile. Chạy weights trước để kiểm Volume CPU thật; nếu thiếu model và đã có phép tải thì weights --download. Không deploy GPU trong khâu này. Chạy verifier thực tế bằng CPU trên Volume của máy GPU, không kiểm file Mac thay cho model Modal.
- Nếu file có nhưng hỏng: báo tên file lỗi, không tự xóa Volume hoặc model; sửa/tải lại đúng file với sự đồng ý của operator. Tùy chọn ref2v/PH3/ACE/SFX không phải điều kiện bắt buộc, báo riêng.
- Đạt weights mới xuất CHECKPOINT=gpu_approval. Nếu thiếu tài khoản, dừng đúng bước và hướng dẫn đăng nhập; không lách.

### gpu_approval — dừng bắt buộc
Hỏi: "H3 4/4 và SDXL 1/1 đã qua kiểm trọng số. Bạn có đồng ý bật máy GPU A100 để kiểm kết nối và workflow không? Việc này có thể tốn tiền theo giờ."
Chờ trả lời. Không thì giữ checkpoint. Không xem đồng ý tải model ở bước trước là đồng ý GPU.

### gpu → connect → verify
Sau approve-gpu, chạy start-gpu.
- Modal: chỉ deploy thông qua setup.py start-gpu, nhận URL thật từ deploy, không tự ghép URL từ workspace; không probe trước phép. Khai đúng URL ở Cài đặt → Nhà cung cấp sinh → Máy GPU, bật một mục mới hoặc sửa mục đã được operator chỉ định; không xóa máy khác. connect xác minh đúng URL trong backend.
- Linux: start ComfyUI đúng 127.0.0.1:8188 trên Linux sau phép rồi start-gpu xác minh. Chạy máy chủ dữ liệu và giao diện cố định trên Linux theo tham chiếu, dùng SSH tunnel, connect kiểm HTTP.
- verify: Linux phải đạt server_verify 19/19, check GPU thật, node/model/template bắt buộc. Modal không dùng server_verify trên Mac: kiểm Mac + H3/SDXL trên Volume + /system_stats CUDA A100 + /object_info và 4 template H3/SDXL bắt buộc trên đúng URL. Không đưa đường dẫn model Mac cho checker Modal. Bất kỳ lỗi/skip/rỗng đều chặn.

### lessons_end → done
Ghi BAI-HOC.md nếu có lỗi mới, cả khi bị chặn; không ghi khóa hoặc thông tin tài khoản. finish mới chuyển done khi verify_report có thật.
Báo đã cài/kiểm gì, checkpoint, còn thiếu gì, GPU đang bật hay đã tắt (không đoán). Không tự tắt máy đang phục vụ task khác. Nếu operator muốn tắt Modal, hướng dẫn lệnh dừng đúng app/profile chỉ khi xác nhận và không có task đang chạy; không gọi URL sau stop để thử.
Chỉ nói **sẵn sàng về cấu hình** khi done; render thật chưa chạy. Khi làm phim, /auto-htgroup vẫn phải kiểm ảnh và xin phép GPU theo run phim, kể cả setup đã đạt.

## Kiểm thử skill không tốn GPU

```bash
python3 scripts/setup.py selftest
python3 scripts/setup.py check-local
```

Selftest là kiểm logic, check-local là kiểm Mac thật, không gọi GPU. Ca thử hành vi đặt ở evals/; không gọi dịch vụ cloud chỉ để kiểm skill.
