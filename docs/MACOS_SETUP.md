# Cài đặt và kiểm thử iKH Local Bridge trên macOS

## 1. Cài đặt

Yêu cầu Python 3.11 trở lên.

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
```

## 2. Tạo Skill Library tối giản

Một Skill chỉ cần `SKILL.md`. Không cần thêm `skill.json` hay script nếu Skill không có công cụ cục bộ cần đăng ký.

```bash
mkdir -p ~/.ikh-skills/local-bridge-discovery-test
cat > ~/.ikh-skills/local-bridge-discovery-test/SKILL.md <<'EOF'
---
name: local-bridge-discovery-test
description: Kiểm tra Local Bridge có phát hiện được Skill chỉ gồm SKILL.md hay không.
---

# Local Bridge Discovery Test

## Mục tiêu
Xác nhận Bridge phát hiện và hiển thị Skill chỉ có một file SKILL.md.

## Tiêu chí
- Skill xuất hiện trong danh sách Skill Library.
- Tên và mô tả hiển thị đúng.
- Bridge không yêu cầu tạo skill.json hoặc script chỉ để nhận diện Skill.

## Giới hạn
Đây chỉ là kiểm thử phát hiện Skill, không phải kiểm thử thực thi AI.
EOF
export IKH_BRIDGE_SKILLS_DIR="$HOME/.ikh-skills"
ikh-bridge --port 8765
```

Mở http://127.0.0.1:8765. Skill `local-bridge-discovery-test` cần xuất hiện với trạng thái chỉ đọc/chưa có tool. Đây là kết quả đúng của phiên bản hiện tại.

## 3. Kiểm tra tự động

Trong terminal khác, tại thư mục repo và sau khi kích hoạt virtualenv:

```bash
python -m compileall -q src tests
python -m unittest discover -s tests -v
```

Chỉ ghi PASS khi các lệnh thực sự chạy và kết quả được quan sát. Các test này kiểm tra Bridge và Python runner hiện tại, không chứng minh AI có thể tự thực thi Skill.

## 4. Skill nào dùng cho kiểm thử end-to-end?

Skill đích là **iKH Curriculum Authoring Skill v1.3**, không phải `Example Local Check` và cũng không phải `local-bridge-discovery-test`.

Kiểm thử end-to-end chỉ được coi là hoàn thành khi Bridge có thể:
1. Nạp nội dung `SKILL.md` của iKH Curriculum Authoring Skill v1.3.
2. Gửi nhiệm vụ đến AI runtime/provider mà người dùng chủ động chọn.
3. Cho AI dùng công cụ local được cho phép để tạo/chỉnh artifact và chạy validator.
4. Thu thập đầu ra, log và bằng chứng; xử lý lỗi thay vì báo PASS giả.
5. Trả về artifact và báo cáo kết quả có phân biệt PASS / FAIL / NOT VERIFIED.

**Trạng thái hiện tại: chưa đạt end-to-end.** Phiên bản Bridge trong repo chưa tích hợp AI provider/agent orchestration. Chưa được diễn giải kết quả discovery test hoặc script test thành bằng chứng rằng quy trình AI chạy được.

## 5. Lưu ý an toàn

Bridge mặc định chỉ lắng nghe trên loopback. Python script chạy với quyền của tài khoản máy hiện tại và chưa có OS sandbox. Chỉ chạy script đã xem xét; không dùng workspace chứa dữ liệu quan trọng cho lần thử đầu.
