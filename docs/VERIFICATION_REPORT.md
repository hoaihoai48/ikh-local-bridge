# Báo cáo Kiểm chứng & Đánh giá Trạng thái Local Bridge (Verification Report)

**Thời điểm thực hiện**: 2026-10-13  
**Môi trường thử nghiệm**: macOS (Darwin arm64 / Apple Silicon), Python 3.14.7  
**Repository**: `hoaihoai48/ikh-local-bridge` (Private)

---

## 1. Tóm tắt kết quả kiểm chứng (Test Matrix)

| Hạng mục kiểm tra | Phạm vi / Kịch bản | Trạng thái | Ghi chú & Bằng chứng |
| :--- | :--- | :---: | :--- |
| **Manifest Parsing** | Đọc `skill.json`, kiểm tra schema version 1, slug match | ✅ **PASS** | `test_manifest.py`: Nhận diện đúng metadata, tên, phiên bản. |
| **Path Traversal Protection** | Chặn entrypoint `../../evil.py` hoặc đường dẫn tuyệt đối | ✅ **PASS** | `test_reject_path_traversal`: Ngăn chặn thành công escape ra ngoài thư mục Skill. |
| **Unmanaged Skills Discovery** | Thư mục chỉ có `SKILL.md` (chưa có `skill.json`) | ✅ **PASS** | Phát hiện nhưng đánh dấu `runnable: false`, không cho phép execute script tự do. |
| **Local Bridge Service Health** | Endpoint `GET /health` | ✅ **PASS** | Trả về `{"status": "ok", "app": "ikh-local-bridge", "version": "0.1.0"}` |
| **Skills Discovery API** | Endpoint `GET /api/skills` | ✅ **PASS** | Trả về danh sách skills, tools, trạng thái runnable và library path. |
| **Tool Execution Safety Gate** | Endpoint `POST /api/run` với `reviewed=False` | ✅ **PASS** | Trả về lỗi 400 Bad Request, bắt buộc cờ xác nhận `reviewed=True`. |
| **Tool Execution (Runner)** | Endpoint `POST /api/run` với `reviewed=True` | ✅ **PASS** | Thực thi subprocess với `sys.executable`, `shell=False`, truyền env `IKH_BRIDGE_WORKSPACE`. |
| **SQLite Job Store** | Ghi nhận job ID, status `COMPLETED`, exit code 0, log | ✅ **PASS** | `GET /api/jobs` phản hồi chính xác lịch sử thực thi vừa chạy. |
| **Loopback Binding Check** | CLI flag `--host` chỉ chấp nhận loopback | ✅ **PASS** | Từ chối các host không thuộc loopback (`0.0.0.0` hoặc IP mạng ngoài). |

---

## 2. Các phần ĐÃ KIỂM CHỨNG (Verified)

1. **Khả năng chạy độc lập ngoài repo giáo trình**:
   - `default_library()` đã được nâng cấp để fallback tự động (`IKH_BRIDGE_SKILLS_DIR` -> `./skills` -> `~/.ikh-skills`), không còn phụ thuộc cứng vào cấu trúc monorepo `parents[3]`.
2. **Khởi tạo và cài đặt venv trên macOS**:
   - Đã cài đặt thành công bản editable `pip install -e ".[dev]"` trên Python 3.14 macOS arm64.
3. **Bộ unit test và integration test hoàn chỉnh**:
   - 7/7 test passed tự động (`tests/test_manifest.py`, `tests/test_api_and_runner.py`).

---

## 3. Các phần CHƯA KIỂM CHỨNG & Giới hạn hiện tại (Known Limitations / Not Verified)

| Giới hạn | Chi tiết | Hướng xử lý tương lai |
| :--- | :--- | :--- |
| **OS Sandbox / Resource Isolation** | Quá trình chạy tool sử dụng quyền của user hiện tại, chưa có `sandbox-exec` (macOS Seatbelt) hay container cô lập filesystem. | Cần cẩn trọng khi duyệt mã script trước khi chạy. |
| **Process Cancellation / Streaming logs** | Quá trình chạy script hiện là synchronous blocking (`subprocess.run`). Chưa hỗ trợ hủy giữa chừng hoặc stream log trực tiếp qua WebSocket/SSE. | Bổ sung background worker / async process manager. |
| **Input Arguments Schema** | Chưa hỗ trợ truyền tham số động (parameter schema) từ UI vào tool; tool hiện chỉ nhận thư mục workspace. | Bổ sung khai báo params trong `skill.json` ở phiên bản v2. |
| **Tích hợp AI Provider** | Chưa có adapter tự động kết nối API LLM (OpenAI, Gemini, Claude, local Ollama). | Dự kiến bổ sung tầng Provider Adapter độc lập. |
