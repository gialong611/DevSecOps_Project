# E4 – Ảnh hưởng của khắc phục lên image và SBOM

> **RQ5 / phân công Tài**: so sánh image trước và sau khi sửa;
> đo độ nhạy quyết định khi tín hiệu KEV/EPSS thay đổi. T0 là mô phỏng,
> không phải snapshot lịch sử có nguồn dẫn.

## 1. Khắc phục cấu trúc Dockerfile

| Chiều kiểm soát | Trước (Dockerfile.vuln) | Sau (Dockerfile) |
|---|---|---|
| USER không root | VI PHẠM | ĐẠT |
| Không ADD từ URL | VI PHẠM | ĐẠT |
| Không sshd / cổng 22 | VI PHẠM | ĐẠT |
| Multi-stage (không base đầy đủ) | VI PHẠM | ĐẠT |

Số chiều được khắc phục: **4/4**

## 2. Độ nhạy chính sách với tín hiệu KEV/EPSS

Mô phỏng chính sách với tín hiệu KEV/EPSS T0 được tạo có chủ đích; không phải snapshot lịch sử CISA/FIRST và không mô tả trạng thái thật của CVE.

| CVE | Quyết định G2 tại T0 | Quyết định G2 tại T1 |
|---|---|---|
| CVE-2024-35195 | BLOCK | WARN |
| CVE-2023-45803 | BLOCK | WARN |
| CVE-2024-24762 | BLOCK | BLOCK |

Số quyết định thay đổi giữa tín hiệu T0 mô phỏng và tập T1 đã ghim: **2**
- CVE-2024-35195: BLOCK → WARN
- CVE-2023-45803: BLOCK → WARN

## 3. So sánh image/SBOM (chế độ live)

| Chỉ số | Trước | Sau | Delta |
|---|---:|---:|---:|
| Gói trong SBOM | 22921 | 2860 | -20061 |
| Lỗ hổng CRITICAL | 21 | 0 | -21 |
| Lỗ hổng HIGH | 531 | 52 | -479 |
| Lỗ hổng MEDIUM | 2037 | 71 | -1966 |
| Lỗ hổng LOW | 2030 | 64 | -1966 |
| Lỗ hổng UNKNOWN | 102 | 1 | -101 |
| Tổng lỗ hổng | 4721 | 188 | -4533 |

### Nhận dạng image và tính so sánh

- before: image ID `sha256:5310731d113763ab98be5751527dbea9ccae7fbbc03b5a6927ac95e0a25fc1f2`, Python `3.12.15`, OS `{'Family': 'debian', 'Name': '13.7'}`, architecture `amd64`.
- after: image ID `sha256:c99a5a371e35e898fffb680ccb384c9132bf7965db403e47cc0d78a257f639fa`, Python `3.12.16`, OS `{'Family': 'debian', 'Name': '13.7'}`, architecture `amd64`.
- Trạng thái E4 live: **limited**; được phép quy kết delta cho thay đổi Dockerfile: **False**.
- Cùng phiên bản Python: **False**; cùng OS: **True**; cùng architecture: **True**; cùng Trivy DB snapshot đã xác minh theo từng lần quét: **False**; snapshot mức job đã ghi: **True**.
- Yếu tố khác nhau cần ghi nhận: Python version `3.12.15` → `3.12.16`.
- CI run: `41288998886`.
- `before` config digest: `sha256:5310731d113763ab98be5751527dbea9ccae7fbbc03b5a6927ac95e0a25fc1f2`; manifest digest trên registry: `chưa có`; Dockerfile SHA-256: `không có`.
- `after` config digest: `sha256:c99a5a371e35e898fffb680ccb384c9132bf7965db403e47cc0d78a257f639fa`; manifest digest trên registry: `chưa có`; Dockerfile SHA-256: `không có`.
- Trivy vulnerability DB cập nhật: `2026-11-01 07:08:40.846369079 +0000 UTC`.

