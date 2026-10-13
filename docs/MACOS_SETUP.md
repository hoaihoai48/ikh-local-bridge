# Hướng dẫn cài đặt và chạy Local Bridge trên macOS

Tài liệu này hướng dẫn chi tiết cách cài đặt, cấu hình thư viện Skill độc lập và chạy Local Bridge cục bộ trên macOS (Apple Silicon M1/M2/M3/M4 hoặc Intel).

---

## 1. Yêu cầu hệ thống

- **Hệ điều hành**: macOS 12 (Monterey) trở lên.
- **Python**: Phiên bản 3.11 trở lên (khuyến nghị Python 3.11, 3.12, 3.13 hoặc 3.14).
- **Git** đã được cấu hình.

Kiểm tra phiên bản Python hiện tại trên máy:
```bash
python3 --version
```

---

## 2. Cài đặt môi trường

Từ thư mục gốc của repository `ikh-local-bridge`:

```bash
# 1. Tạo môi trường ảo riêng biệt
python3 -m venv .venv

# 2. Kích hoạt môi trường ảo
source .venv/bin/activate

# 3. Nâng cấp pip và cài đặt dependencies (bao gồm dev tools)
pip install --upgrade pip
pip install -e ".[dev]"
```

---

## 3. Cách quản lý Thư viện Skill (Độc lập với repo giáo trình)

`ikh-local-bridge` là **runtime dùng chung** cho nhiều Skill. Các Skill không bắt buộc phải nằm cố định trong repo giáo trình hay repo này. Bạn có thể tổ chức Skill theo các cách:

### Cách 1: Sử dụng thư mục mặc định người dùng (`~/.ikh-skills`)
Local Bridge tự động trỏ về `~/.ikh-skills` nếu không tìm thấy thư mục `skills/` cục bộ.
```bash
mkdir -p ~/.ikh-skills
# Sao chép hoặc clone các skill vào đây:
# ~/.ikh-skills/my-first-skill/
#   ├── SKILL.md
#   ├── skill.json
#   └── scripts/
```

### Cách 2: Trỏ tới bất kỳ thư mục Skill nào qua biến môi trường
Nếu bạn lưu Skill ở thư mục riêng, hoặc trong repo giáo trình, hãy thiết lập:
```bash
export IKH_BRIDGE_SKILLS_DIR="/path/to/your/skills-library"
```

Ví dụ trỏ tới thư mục Skill của repo giáo trình `giao-trinh-ikh`:
```bash
export IKH_BRIDGE_SKILLS_DIR="/Users/vu/projects/giao-trinh-ikh/skills"
```

---

## 4. Khởi chạy Local Bridge

Sau khi kích hoạt `.venv`:

```bash
# Khởi chạy trên cổng mặc định 8765
ikh-bridge

# Hoặc chỉ định cổng tùy chọn
ikh-bridge --port 9000
```

Mở trình duyệt truy cập:
👉 **http://127.0.0.1:8765**

> **Lưu ý bảo mật**: Local Bridge chỉ bind vào loopback (`127.0.0.1`), không mở ra mạng LAN hay Internet công cộng.

---

## 5. Quy trình Kiểm thử (Local Test & Verification)

### 5.1. Chạy Automated Unit & Integration Tests
```bash
source .venv/bin/activate
python -m unittest discover -s tests -v
```

### 5.2. Chạy Smoke Check thủ công với Skill Template
```bash
# 1. Trỏ library về thư mục skill-template mẫu
export IKH_BRIDGE_SKILLS_DIR="$(pwd)/skill-template/.."

# 2. Khởi chạy bridge
ikh-bridge --port 8765
```

Truy cập Web UI, chọn Skill mẫu `Example Local Check`, chọn Tool `check`, nhập một đường dẫn thư mục làm workspace, tích chọn xác nhận đã duyệt mã nguồn và nhấn **Chạy tool**. Kết quả thực thi JSON sẽ trả về ngay trên giao diện và được lưu vào SQLite.
