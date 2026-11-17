# Runbook demo trực tiếp: 4 lỗi bảo mật

Tài liệu này dùng bốn fixture D08, D09, D13 và D16 đã có trong bộ thực nghiệm.
Mỗi lượt chạy chỉ áp dụng một lỗi trên runner GitHub Actions; patch không được
commit vào `main` và không làm bẩn working tree trên máy trình diễn.

## Cách chạy trên GitHub

1. Mở repository → **Actions** → **DevSecOps CI** → **Run workflow**.
2. Chọn branch `codex/demo-d01-gate` ở **Use workflow from**.
3. Nhập một `fixture_id` trong bảng dưới đây. Không để `baseline`, vì baseline
   không gieo lỗi.
4. Bỏ chọn **Run the slower before/after image remediation experiment**.
   Experiment E4 chỉ chạy trên baseline; bỏ chọn giúp tránh nhầm với demo lỗi.
5. Chọn `benchmark_role = warmup`, đặt `study_id` riêng, ví dụ `demo-D08`.
   Như vậy lượt trình diễn không bị tính nhầm vào phép đo E3.
6. Chạy từng fixture một. Xem **Summary** và artifact `report-gate`; mở
   `report-scan`, `report-iac` hoặc `report-image` để chỉ ra finding của scanner.

Các lượt được chạy bằng `workflow_dispatch`. Workflow tự gọi
`tests/apply_fixture_patch.py` trong runner để áp patch tương ứng; không sửa file
nguồn trên máy bạn. Nếu gate G2 `BLOCK`, job gate hiện đỏ là kết quả mong đợi của
demo chặn lỗi. D09 được kỳ vọng `WARN` ở G2 nên gate không chặn lượt đó.

### Chạy bằng PowerShell/gh

Chạy **một lệnh mỗi lượt**, đợi Actions hoàn tất rồi mới chạy ID tiếp theo:

```powershell
# Chạy từ thư mục gốc của repository.
$gh = 'C:\Program Files\GitHub CLI\gh.exe'
$ref = "codex/demo-d01-gate"
$fixtureId = "D08" # lần sau đổi thành D09, D13 hoặc D16
$studyId = "demo-$fixtureId"
& $gh workflow run .github/workflows/ci.yml --ref $ref `
  -f fixture_id=$fixtureId -f run_e4=false -f benchmark_role=warmup -f study_id=$studyId
```

Đổi `$fixtureId` sau khi run hiện tại hoàn tất; mỗi lần chỉ dispatch một fixture.

Để lấy URL/run ID và theo dõi:

```powershell
& $gh run list --workflow .github/workflows/ci.yml --branch $ref --limit 5
$runId = "123456789" # thay bằng RUN_ID vừa được liệt kê
& $gh run watch $runId
```

`gh run watch` có thể trả exit code 1 ở D08, D13, D16 vì gate chặn đúng lỗi;
hãy đọc job `gate (Conftest Rego)` và artifact thay vì coi riêng exit code đó là
lỗi cài đặt workflow.

## Bốn kịch bản và nội dung cần giải thích

| ID | Thay đổi fixture trong runner | Công cụ / finding dự kiến | Kết quả G2 | Cách khắc phục |
|---|---|---|---|---|
| **D08 – Secret hardcode** | Thêm một `API_TOKEN` giả vào cuối `Code/DevSecOps/src/app/main.py`, sau endpoint `list_users()` | Gitleaks, `generic-api-key` | **BLOCK** – secret không được phép commit vào source | Xóa secret khỏi lịch sử cần thiết; dùng biến môi trường hoặc secret manager; nếu là credential thật thì thu hồi/rotate ngay. |
| **D09 – Dependency có CVE** | Thêm `requests==2.31.0` vào `Code/DevSecOps/src/requirements.txt`, ngay dưới `email-validator==2.3.0` | Trivy SCA, `CVE-2024-35195` | **WARN** – G2 hạ CVE Medium này xuống cảnh báo; G1 dự kiến BLOCK | Nâng `requests` lên bản đã vá (`2.32.0` trở lên), khóa dependency và quét lại. |
| **D13 – Container chạy root** | Xóa chỉ thị `USER 10001` ở khoảng dòng 45 của `Code/DevSecOps/Dockerfile`; mặc định image chạy bằng root | Checkov Dockerfile, `CKV_DOCKER_3` | **BLOCK** | Khôi phục `USER 10001` hoặc UID không đặc quyền tương đương. Với fixture Dockerfile D12–D15, workflow cố ý bỏ qua build/Trivy image/SBOM/Grype; Checkov vẫn quét cấu hình Dockerfile. |
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
- **D09:** “Dependency đang dùng phiên bản có CVE. G1 chặn, còn G2 chỉ cảnh báo
  trường hợp Medium này để tránh chặn mọi rủi ro mức vừa. Ngưỡng thấp hơn vẫn
  cần được theo dõi và vá.”
- **D13:** “Container mặc định chạy root làm tăng tác động nếu ứng dụng bị chiếm.
  Checkov phát hiện Dockerfile không khai báo user không đặc quyền; gate chặn.”
- **D16:** “Security group mở SSH từ mọi địa chỉ Internet. Checkov phát hiện
  `CKV_AWS_24`; policy chặn cấu hình này trước khi triển khai IaC.”

## Vị trí patch và kiểm tra khả năng áp dụng

Patch nằm tại `Code/DevSecOps/ground_truth/patches/`:

- `D08_hardcoded_token.patch`
- `D09_cve_py.patch`
- `D13_dockerfile_root_user.patch`
- `D16_sg_open_ssh_world.patch`

Đã xác nhận cả bốn patch áp dụng sạch trên branch demo hiện tại bằng
`git apply --check`. Để đổi lỗi trình diễn, chỉ đổi `fixture_id`; không tự áp
patch lên `main`.
