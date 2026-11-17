# Bằng chứng gate và required checks trên pull request

Cập nhật: 2026-11-16. PR #1 đã được dùng để kiểm tra cả lượt lỗi bị gate chặn,
lượt sửa được cho qua và trạng thái check bắt buộc trên nhánh `main`.

| Bước | Commit/run | Kết quả |
|---|---|---|
| PR sạch sau khi xử lý xung đột | [run 43729623939](https://github.com/gialong611/DevSecOps_Project/actions/runs/43729623939) | Python tests, scan, IaC, image và gate pass |
| Gieo lỗi D01 SQL injection | [run 43729980295](https://github.com/gialong611/DevSecOps_Project/actions/runs/43729980295) | Scanner jobs pass; gate G2 fail với blocker HIGH |
| Hoàn nguyên lỗi D01 | [run 43730231762](https://github.com/gialong611/DevSecOps_Project/actions/runs/43730231762) | Python tests, scan, IaC, image và gate pass |
| Lượt CI cuối trên nhánh PR | [run 43730524460](https://github.com/gialong611/DevSecOps_Project/actions/runs/43730524460) | Cả 6 check context pass trước khi PR được merge |

## Kết quả block/pass

Run `43729980295` ghi hai blocker HIGH trong `gate_input.json`:

- `rules.semgrep.python.sqli.concatenation`
- `python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query`

Step `Chạy Security Gate (Conftest + Rego)` kết thúc với exit code 1; các job
Python tests, security scans, IaC và image đều thành công. Sau khi hoàn nguyên
fixture D01, run `43730231762` cho gate pass. Đây là bằng chứng gate chặn lỗi
gieo cài và cho qua sau khắc phục.

## Ruleset đang áp dụng cho `main`

Đã đọc trực tiếp cấu hình GitHub repository ruleset ngày 2026-11-16:

- Ruleset **Protect main** đang `active`, target `refs/heads/main`.
- Bắt buộc tạo pull request trước khi cập nhật nhánh; yêu cầu 0 lượt review.
- Bắt buộc 6 status checks pass trước khi cập nhật nhánh:
  `Prepare Trivy and Grype vulnerability DB snapshots`, `Run Python tests`,
  `Security scans (collection mode)`, `iac`, `image`, `gate (Conftest Rego)`.
- Bật chặn xóa nhánh và force push; bypass được đặt là `never`.
- Tùy chọn yêu cầu nhánh phải cập nhật trước khi merge đang tắt (`strict=false`).
- Lệnh `gh pr checks 1 --required` hiện trả về đủ 6 check bắt buộc và cả 6 đều
  pass. Tuy nhiên, PR #1 được merge lúc `2026-11-15T15:35:38Z`, còn ruleset được
  tạo lúc `2026-11-15T23:08:08+07:00` (16:08:08Z). Vì vậy PR #1 merge trước khi
  ruleset tồn tại; run `43730524460` xác nhận các check đã pass nhưng không chứng
  minh ruleset đã chặn merge ở PR đó.

Ruleset active và danh sách check bắt buộc đã được xác minh qua API. Cần một PR
mới được tạo sau thời điểm bật ruleset để chứng minh trực tiếp GitHub từ chối
merge khi check pending/fail rồi cho merge khi cả sáu check pass. Quy tắc hiện
không bắt buộc review hoặc cập nhật nhánh trước khi merge; cần trình bày đúng
các giới hạn này.

## Lượt xác minh bổ sung: PR #3 (2026-11-17)

PR nháp [#3](https://github.com/gialong611/DevSecOps_Project/pull/3) trên
nhánh `codex/demo-d01-gate` dùng fixture D01 để kiểm tra lại đường đi block/pass:

| Bước | Commit/run | Kết quả |
|---|---|---|
| Gieo D01 SQL injection | [run 44036479351](https://github.com/gialong611/DevSecOps_Project/actions/runs/44036479351), commit `42aad675a70a3736b0412c3a57830c0ad30cddcb` | Scanner phát hiện hai rule SQL injection HIGH; gate G2 fail đúng dự kiến. Python, scanner, IaC và image jobs hoàn tất thành công. |
| Gỡ D01 sau khi xác nhận block | [run 44036927972](https://github.com/gialong611/DevSecOps_Project/actions/runs/44036927972), commit `3dbfe99d5da19a74be0cbb815f801f310379f29a` | Gate pass; DB, Python, security scans, IaC và image đều pass. `release` và `deploy-smoke` được workflow bỏ qua. |

Run đầu ghi nhận `python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query`
và `rules.semgrep.python.sqli.concatenation`, cả hai mức HIGH. Run sửa dùng
baseline sạch sau khi hoàn nguyên file ứng dụng về nội dung của `main`.

### Trạng thái enforcement trong lượt PR #3

Ngày 2026-11-17, GitHub API trả ruleset `Protect main` ở trạng thái
`disabled`. Vì vậy PR #3 chứng minh workflow chạy và gate block/pass theo mã
nguồn, nhưng GitHub không bắt buộc các check đó trước khi merge tại thời điểm
này. PR vẫn là draft và chưa merge; lượt này không được tính là bằng chứng
branch protection chặn merge.

## Bốn PR demo riêng biệt: xác minh scanner và policy (2026-11-17)

Bốn PR nháp được tách riêng từ `main`, mỗi PR chứa một lỗi có chủ đích. Đây là
bằng chứng chạy demo và hành vi policy; không tính thành PR block/pass được GitHub
enforce vì ruleset đang tắt.

| Fixture / PR | Run | Finding quan sát được | Kết quả |
|---|---|---|---|
| D08 secret, [PR #4](https://github.com/gialong611/DevSecOps_Project/pull/4) | [44048101443](https://github.com/gialong611/DevSecOps_Project/actions/runs/44048101443) | Gitleaks `generic-api-key` | Gate G2 BLOCK; scanner và các job kiểm tra còn lại hoàn tất. |
| D09 dependency, [PR #5](https://github.com/gialong611/DevSecOps_Project/pull/5) | [44048111994](https://github.com/gialong611/DevSecOps_Project/actions/runs/44048111994) | Trivy `CVE-2024-35195` | Gate G2 WARN; các required workflow checks đều pass. |
| D13 container root, [PR #6](https://github.com/gialong611/DevSecOps_Project/pull/6) | [44048122714](https://github.com/gialong611/DevSecOps_Project/actions/runs/44048122714) | Checkov `CKV_DOCKER_3` | Gate G2 BLOCK. Test `test_e4_dockerfile_checks_real_files` cũng fail do xác nhận thuộc tính non-root bị vi phạm. |
| D16 SSH công khai, [PR #7](https://github.com/gialong611/DevSecOps_Project/pull/7) | [44048132559](https://github.com/gialong611/DevSecOps_Project/actions/runs/44048132559) | Checkov `CKV_AWS_24` | Gate G2 BLOCK; các job kiểm tra còn lại pass. |

Sau khi D08 được thêm, Gitleaks mặc định quét tất cả Git refs cục bộ và khiến
secret giả xuất hiện ngoài PR D08. Workflow được sửa ở commit main `3a96932`
để giới hạn lịch sử quét bằng `--log-opts="HEAD"`; run [44047990981](https://github.com/gialong611/DevSecOps_Project/actions/runs/44047990981)
trên `main` thành công. Bốn run trên xác nhận lỗi cross-branch không còn làm
nhiễu kết quả D09, D13 và D16.

Các PR #4–#7 vẫn là draft, chưa merge. `release` và `deploy-smoke` bị skip ở
các lượt PR; kết quả này chỉ chứng minh lớp kiểm tra CI/gate liên quan, không
phải bằng chứng deploy thành công hoặc ruleset chặn thao tác merge.

## D01 được gieo lại để demo gate BLOCK (2026-11-17)

Sau khi PR #3 được dùng để kiểm tra lượt sửa/pass, fixture D01 được khôi phục
trên branch `codex/demo-d01-gate`, commit `ed081521173b1ec1c659201ef49677176b7c2cfb`.
Run [44052476001](https://github.com/gialong611/DevSecOps_Project/actions/runs/44052476001)
đã hoàn tất với Python tests, security scan, IaC và image pass; riêng gate G2
BLOCK đúng hai finding SAST HIGH:

- `python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query`
- `rules.semgrep.python.sqli.concatenation`

Gate ghi `22 tests, 0 passed, 20 warnings, 2 failures`; hai failure là hai
blocker SQL injection, còn 20 warning baseline không phải nguyên nhân làm run
đỏ. `release` và `deploy-smoke` được skip. Đây là lượt demo lỗi được gieo; run
block/pass trước đó vẫn là bằng chứng lịch sử riêng.

PR #5 / D09 vẫn chứa `requests==2.31.0`; run `44048111994` quan sát
`CVE-2024-35195` và G2 WARN. Các check xanh ở D09 là hành vi đúng theo policy:
finding Medium được báo để khắc phục nhưng không chặn release.
