# Runbook demo trực tiếp: D01 và 4 lỗi bảo mật bổ sung

Tài liệu này gồm fixture D01 SQL injection trên PR #3 và bốn demo bổ sung D08,
D09, D13, D16. Mỗi fixture nằm trên branch/PR riêng; không merge các PR lỗi.
Bạn có thể mở diff của từng lỗi và xem check tương ứng.

## Branch demo

| Fixture | Branch riêng | PR nháp |
|---|---|---|
| D01 SQL injection | `codex/demo-d01-gate` | [PR #3](https://github.com/gialong611/DevSecOps_Project/pull/3) |
| D08 secret hardcode | `codex/demo-d08-secret` | [PR #4](https://github.com/gialong611/DevSecOps_Project/pull/4) |
| D09 dependency có CVE | `codex/demo-d09-sca-warn` | [PR #5](https://github.com/gialong611/DevSecOps_Project/pull/5) |
| D13 container chạy root | `codex/demo-d13-container-root` | [PR #6](https://github.com/gialong611/DevSecOps_Project/pull/6) |
| D16 SSH mở ra Internet | `codex/demo-d16-open-ssh` | [PR #7](https://github.com/gialong611/DevSecOps_Project/pull/7) |

## Run đã xác minh trên GitHub

| Demo | Run | Kết quả thực tế |
|---|---|---|
| D01 | [44052476001](https://github.com/gialong611/DevSecOps_Project/actions/runs/44052476001) | Semgrep và scanner SAST phát hiện SQL injection HIGH; gate G2 BLOCK. Python tests, scan, IaC và image pass. |
| D08 | [44048101443](https://github.com/gialong611/DevSecOps_Project/actions/runs/44048101443) | Gitleaks phát hiện `generic-api-key`; gate G2 BLOCK. Các scanner và job khác pass. |
| D09 | [44048111994](https://github.com/gialong611/DevSecOps_Project/actions/runs/44048111994) | Trivy phát hiện `CVE-2024-35195`; G2 WARN và các job kiểm tra pass. |
| D13 | [44048122714](https://github.com/gialong611/DevSecOps_Project/actions/runs/44048122714) | Checkov phát hiện `CKV_DOCKER_3`; gate BLOCK. Unit test non-root cũng fail đúng assertion `non_root_user`; các scanner/IaC/image jobs pass. |
| D16 | [44048132559](https://github.com/gialong611/DevSecOps_Project/actions/runs/44048132559) | Checkov phát hiện `CKV_AWS_24`; gate G2 BLOCK, các job kiểm tra khác pass. |

Run D01 dùng commit `ed08152`. Từ commit main `3a96932`, Gitleaks quét lịch sử `HEAD` của branch đang checkout
thay vì mọi ref; nhờ vậy secret giả của D08 không làm nhiễu các demo khác.
`release` và `deploy-smoke` được workflow bỏ qua trong các lượt PR.

Mỗi PR chứa đúng một thay đổi lỗi trên branch đó. Khi mở PR, vào **Files changed**
để xem dòng gieo lỗi; vào **Checks** để xem pipeline. Checks tự chạy khi PR được
tạo. Để chạy lại, mở run tương ứng trong **Actions** rồi chọn **Re-run all jobs**;
hoặc dùng lệnh PowerShell bên dưới. Cách này giữ nguyên event pull request và
quét đúng lỗi đã commit trên branch.

`D01`, `D08`, `D13` và `D16` làm gate G2 đỏ vì bị `BLOCK`. Riêng D13 còn làm
test `test_e4_dockerfile_checks_real_files` fail ở điều kiện non-root; đây là
kiểm soát bảo vệ cùng thuộc tính, không phải lỗi Python do thay đổi Dockerfile.
Với D09, gate G2 dự kiến `WARN` và cho workflow qua; đây là demo ngưỡng cảnh báo.
Các PR đang để draft; đừng merge vì mỗi branch cố ý chứa lỗi. Ruleset hiện tắt
nên GitHub không enforce required checks trước merge.

### Chạy lại bằng PowerShell/gh

Lấy run ID của branch demo rồi yêu cầu GitHub chạy lại:

```powershell
# Chạy từ thư mục gốc của repository. Đổi branch cho từng demo.
$gh = 'C:\Program Files\GitHub CLI\gh.exe'
$ref = "codex/demo-d08-secret" # D09: codex/demo-d09-sca-warn; D13: codex/demo-d13-container-root; D16: codex/demo-d16-open-ssh
& $gh run list --workflow .github/workflows/ci.yml --branch $ref --limit 5
$runId = "123456789" # thay bằng run ID của PR/branch đang trình bày
& $gh run rerun $runId
```

Đổi `$ref` theo branch cần demo. Để theo dõi run đang chạy:

```powershell
& $gh run watch $runId
```

`gh run watch` có thể trả exit code 1 ở D08, D13, D16 vì gate chặn đúng lỗi;
hãy đọc job `gate (Conftest Rego)` và artifact thay vì coi riêng exit code đó là
lỗi cài đặt workflow.

## Kịch bản và nội dung cần giải thích

| ID | Thay đổi trong branch | Công cụ / finding dự kiến | Kết quả G2 | Cách khắc phục |
|---|---|---|---|---|
| **D01 – SQL injection** | Thêm endpoint `/search` với truy vấn SQL nối trực tiếp tham số `q` trong `Code/DevSecOps/src/app/main.py` | Semgrep `rules.semgrep.python.sqli.concatenation`; SAST SQL raw query | **BLOCK** – hai finding HIGH trong run 44052476001 | Dùng truy vấn tham số hóa; không ghép input vào câu SQL. |
| **D08 – Secret hardcode** | Thêm một `API_TOKEN` giả vào cuối `Code/DevSecOps/src/app/main.py`, sau endpoint `list_users()` | Gitleaks, `generic-api-key` | **BLOCK** – secret không được phép commit vào source | Xóa secret khỏi lịch sử cần thiết; dùng biến môi trường hoặc secret manager; nếu là credential thật thì thu hồi/rotate ngay. |
| **D09 – Dependency có CVE** | Thêm `requests==2.31.0` vào `Code/DevSecOps/src/requirements.txt`, ngay dưới `email-validator==2.3.0` | Trivy SCA, `CVE-2024-35195` | **WARN** – G2 hạ CVE Medium này xuống cảnh báo; G1 dự kiến BLOCK | Nâng `requests` lên bản đã vá (`2.32.0` trở lên), khóa dependency và quét lại. |
| **D13 – Container chạy root** | Xóa chỉ thị `USER 10001` ở khoảng dòng 45 của `Code/DevSecOps/Dockerfile`; mặc định image chạy bằng root | Checkov Dockerfile, `CKV_DOCKER_3` | **BLOCK**; unit test kiểm tra `non_root_user` cũng dự kiến fail vì cùng invariant | Khôi phục `USER 10001` hoặc UID không đặc quyền tương đương. Với fixture Dockerfile D12–D15, workflow cố ý bỏ qua build/Trivy image/SBOM/Grype; Checkov vẫn quét cấu hình Dockerfile. |
| **D16 – Security group mở SSH công khai** | Thêm ingress TCP/22 với `cidr_blocks = ["0.0.0.0/0"]` vào `aws_security_group.alb` trong `Code/DevSecOps/infra/security_groups.tf` | Checkov IaC, `CKV_AWS_24` | **BLOCK** – SSH mở toàn Internet là khóa kiểm soát cao | Xóa ingress SSH công khai; giới hạn CIDR quản trị cụ thể hoặc dùng SSM/bastion theo thiết kế. |

Các mức G2 trên là hành động kỳ vọng ghi trong
`Code/DevSecOps/ground_truth/ground_truth.csv`; kết quả thực tế của buổi demo
phải đọc từ run và artifact vừa chạy. E1/E2 đã có observation live cho bộ
fixture; không dùng bảng kỳ vọng thay cho artifact nếu đang trình bày kết quả
của một run cụ thể.

## Lời dẫn ngắn khi thuyết trình

- **D08:** “Đây là token giả được hardcode trong source. Gitleaks tìm thấy chuỗi
  giống API key; policy coi secret là rủi ro không được đưa vào repository nên
  gate chặn.”
- **D01:** “Endpoint ghép trực tiếp input vào câu SQL. Hai rule SAST nhận ra
  SQL injection mức HIGH nên gate chặn trước khi triển khai.”
- **D09:** “Dependency đang dùng phiên bản có CVE. G1 chặn, còn G2 chỉ cảnh báo
  CVE Medium này để tránh chặn mọi rủi ro mức vừa. Check xanh là có chủ đích:
  finding vẫn được báo, nhưng policy chỉ WARN; nhóm vẫn cần lên kế hoạch vá.”
- **D13:** “Container mặc định chạy root làm tăng tác động nếu ứng dụng bị chiếm.
  Checkov phát hiện Dockerfile không khai báo user không đặc quyền; gate chặn.”
- **D16:** “Security group mở SSH từ mọi địa chỉ Internet. Checkov phát hiện
  `CKV_AWS_24`; policy chặn cấu hình này trước khi triển khai IaC.”

## Vị trí patch và kiểm tra khả năng áp dụng

Patch nằm tại `Code/DevSecOps/ground_truth/patches/`:

- `D01_sqli_concat.patch`
- `D08_hardcoded_token.patch`
- `D09_cve_py.patch`
- `D13_dockerfile_root_user.patch`
- `D16_sg_open_ssh_world.patch`

Đã xác nhận patch D01 và bốn patch demo bổ sung áp dụng trên `origin/main`;
mỗi lỗi được commit riêng vào branch tương ứng. Workflow Gitleaks giới hạn
lịch sử quét ở `HEAD` của branch để secret trong PR D08 không làm nhiễu các PR
khác. Không merge các branch demo vào `main`.
