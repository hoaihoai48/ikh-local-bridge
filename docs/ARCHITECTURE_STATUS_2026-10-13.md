# Trạng thái kiến trúc Local Bridge — 2026-10-13

## Quy ước Skill

`SKILL.md` là file duy nhất bắt buộc. `skill.json` chỉ là manifest riêng để đăng ký Python tools cho Bridge hiện tại. Scripts, tests, references và README là tùy chọn.

## Trạng thái runtime

- **Đã có:** phát hiện Skill; hiển thị Skill và Python tools đã đăng ký; chạy tool Python theo manifest; lưu lịch sử job.
- **Chưa có:** AI provider adapter; agent orchestration; vòng lặp AI gọi local tools; tạo nhiều artifact theo một yêu cầu; chạy validator rồi tự sửa lỗi; kiểm thử end-to-end với AI.

Do đó, các PASS trong `VERIFICATION_REPORT.md` chỉ áp dụng cho phần deterministic được mô tả ở đó. Chúng không chứng minh AI có thể tự thực thi Skill. Các lệnh test chưa được chạy lại trong lần chỉnh sửa tài liệu này.

## Hai cấp kiểm thử

1. **Discovery smoke test:** dùng `examples/local-bridge-discovery-test/SKILL.md`, chỉ một file. Xác minh Bridge phát hiện Skill trong thư mục được cấu hình.
2. **End-to-end acceptance test:** dùng `iKH Curriculum Authoring Skill v1.3`, với AI runtime/provider được người dùng chọn, local tools, validators và kiểm tra artifact. **Chưa thể chạy bằng runtime hiện tại** vì chưa có agent orchestration.

Không được coi cấp 1 là thay thế cho cấp 2 hoặc báo PASS cho tính năng chưa triển khai.
