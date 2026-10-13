# Cài đặt và kiểm thử iKH Local Bridge trên macOS

## Mục tiêu

Một tiến trình Local Bridge chạy cho **một Skill cụ thể** và một thư mục làm việc. Bridge đọc SKILL.md, gửi nhiệm vụ đến model đã cấu hình, sau đó thực thi các thao tác file/lệnh tại máy local thông qua tool loop.

## 1. Cài đặt Bridge

Yêu cầu Python 3.11 trở lên.

    git clone https://github.com/hoaihoai48/ikh-local-bridge.git
    cd ikh-local-bridge
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -e ".[dev]"

## 2. Chuẩn bị model local mặc định

Cài Ollama từ https://ollama.com/, sau đó chạy:

    ollama pull qwen2.5-coder:7b
    ollama serve

Model phải hỗ trợ OpenAI-compatible chat completions và tool calling. Nếu chọn model khác, thay IKH_BRIDGE_MODEL bằng tên model đó.

## 3. Chọn đúng một Skill và workspace

Thay đường dẫn mẫu bằng đường dẫn thực tế:

    export IKH_BRIDGE_SKILL_FILE="/absolute/path/to/your-skill/SKILL.md"
    export IKH_BRIDGE_WORKSPACE="/absolute/path/to/working-directory"
    export IKH_BRIDGE_MODEL="qwen2.5-coder:7b"
    export IKH_BRIDGE_MODEL_BASE_URL="http://127.0.0.1:11434/v1"
    ikh-bridge --port 8765

Giữ nguyên các biến môi trường đó trong terminal chạy Bridge. Mở http://127.0.0.1:8765. Trang phải hiển thị đúng một đường dẫn Skill, một workspace, model và endpoint.

## 4. Chạy thử thực tế

Trước khi thử Skill chính, hãy dùng một workspace tạm thời và một Skill có hướng dẫn ngắn, ví dụ yêu cầu tạo file hello.txt rồi đọc lại file đó.

Kiểm tra:
1. Bridge hiển thị đúng Skill và workspace đã cấu hình.
2. Model phản hồi được; không có fallback sang cloud nếu endpoint local tắt.
3. Agent gọi tool write_file để tạo file.
4. Agent gọi read_file hoặc run_command để kiểm tra kết quả.
5. Transcript có kết quả tool thật; file tồn tại trong workspace.
6. Nếu model endpoint không chạy, Bridge trả lỗi rõ ràng chứ không giả vờ đã hoàn tất.

## 5. Kiểm thử tự động

Trong virtualenv tại thư mục repo:

    python -m compileall -q src tests
    python -m unittest discover -s tests -v

Các test unit/integration không thay thế lần chạy thực tế với model local. Chỉ ghi PASS khi đã chạy lệnh và xem kết quả.

## 6. Dùng provider từ xa (chỉ khi chủ động chọn)

Chỉ khi chấp nhận gửi nội dung Skill, yêu cầu và kết quả tool ra ngoài, mới cấu hình endpoint HTTPS và API key phù hợp:

    export IKH_BRIDGE_MODEL_BASE_URL="https://provider.example/v1"
    export IKH_BRIDGE_MODEL="provider-model-name"
    export IKH_BRIDGE_MODEL_API_KEY="your-key"

Không commit API key vào repo. Bridge không tự chuyển sang provider từ xa khi model local lỗi.

## Giới hạn hiện tại

- Tool file bị giới hạn trong workspace, nhưng lệnh hệ điều hành chạy với quyền tài khoản hiện tại và chưa có OS sandbox.
- Model coding/text không tự sinh ảnh. Cần adapter/model tạo ảnh local thực sự nếu Skill yêu cầu.
- Chưa được coi là production-ready cho dữ liệu quan trọng; thử nghiệm trước trong workspace dùng một lần.
