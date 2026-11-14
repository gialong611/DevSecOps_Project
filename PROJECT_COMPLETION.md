# Trạng thái hoàn thiện đề tài 21

Cập nhật: 2026-11-14. Tài liệu tách bằng chứng CI đã có khỏi kết quả thí nghiệm
chưa chạy; không dùng dữ liệu thăm dò để tuyên bố recall hoặc false-positive rate.

## Tóm tắt điều hành

- Artifact baseline mới nhất đã phân tích là [GitHub Actions run ID 43599931890](https://github.com/gialong611/DevSecOps_Project/actions/runs/43599931890/attempts/1), commit `9ca131a678017e89d804033c3d6b75e0f2c0f366`, event `push`. Gate của artifact trả `WARN` nhưng pass với 0 blocker và 19 warning trên 292 finding. Số liệu được lưu tại `Code/DevSecOps/tests/results/metrics/ci_baseline_latest.json`.
- Artifact xác nhận 17 HIGH chưa có bản vá và 2 MEDIUM có bản vá; run là baseline cold một lần. E4 không được yêu cầu và chưa có bằng chứng PR/branch protection.
- Run 43599931890 có Checkov JSON hợp lệ, 77 finding Checkov, 11 Trivy IaC misconfiguration, và gate liên kết đủ 19/19 cảnh báo CVE với finding nguồn. Trivy IaC có 2 HIGH và 6 MEDIUM chưa hiện trong G2 warning.
- CI ghi thời gian scan security 30s, IaC 34s, image 117s; đường găng song song là 117s và runner-minutes là 3.017. Đây là một lượt đơn, không phải kết luận E3.
- `decisions.csv` và `runs.csv` là dữ liệu phát lại/thăm dò. Chúng không chứng minh scanner phát hiện lỗi hay đo được thời gian CI thật.
- Run 43599931890 xác nhận parser Trivy `FAIL`/`FAILED`, sửa egress, Checkov JSON array và `conftest verify` trên CI. Sau artifact, policy G2 được cập nhật để gom các cấu hình IaC/K8s cần review thành một cảnh báo có liên kết finding; thay đổi policy và correlation này chưa có CI run.
- Các thay đổi hiện tại thêm thu thập ma trận D/C/N, so sánh pip cache cold/warm, kiểm tra E4 nghiêm ngặt hơn và đưa các script phân tích vào pytest. Chưa có dữ liệu live đủ cho các thí nghiệm D/C/N.
- AWS được hoãn đến sau khi hoàn tất bằng chứng cốt lõi. DOCX sẽ được cập nhật sau khi có số liệu thực nghiệm; PPTX không thuộc phạm vi cập nhật.

## Bảng trạng thái có thể kiểm tra nhanh

| Hạng mục | Bằng chứng hiện có | Trạng thái | Điều kiện để đánh dấu hoàn tất |
|---|---|---|---|
| Pipeline baseline | Run 43599931890: gate WARN/pass, 0 blocker, 19 warnings; 292 finding | Có baseline chạy được | Chạy lại để xác nhận cảnh báo IaC tổng hợp mới trong G2 |
| E1 scanner theo D/C/N | `findings.csv` là dữ liệu dự kiến; chưa có đủ raw observation theo fixture | **Chưa đạt** | Baseline + D01–D28 + C01–C10 + N01–N08 có observation complete, cùng commit/tool/Trivy DB phù hợp |
| E2 G0/G1/G2 | Metric hiện có phát lại `decisions.csv`; G2 ghi 20/28 lỗi bị chặn trong dữ liệu đó | **Thăm dò, chưa phải số đo live** | Tổng hợp policy decision từ cùng các observation CI thực tế; báo riêng D, C và N |
| PR block/pass | Workflow có gate trên pull request; chưa có bằng chứng required status check của nhánh và PR lỗi/sửa thật | **Chưa xác minh** | PR lỗi bị gate BLOCK, PR sau sửa được gate PASS; branch rule bắt buộc `gate (Conftest Rego)` và `Run Python tests` |
| E3 thời gian | Run 43599931890: cold một lượt; job 30/34/117 giây, đường găng 117 giây, runner 3,017 phút | **Chưa đủ** | Tối thiểu 5 lượt cache cold và 5 lượt cache warm cùng commit; loại warm-up; báo median/IQR, thời gian từng job, wall time và runner-minutes |
| E4 image/SBOM | Run #13: lỗ hổng 4.721→188, SBOM 22.921→2.860; Python 3.12.15→3.12.16; DB chỉ ghi ở cấp job | **Live nhưng limited; không quy kết nhân quả** | E4 mới xác nhận cùng Python, OS, architecture và Trivy DB riêng cho từng lần quét; lưu image config digest, Dockerfile SHA-256, hai báo cáo Trivy và hai SBOM |
| Tài liệu | README và báo cáo Markdown được làm mới theo trạng thái này | Đã cập nhật Markdown | Điền số CI thật vào DOCX sau khi E1–E4 hoàn tất; không sửa PPTX |
| AWS | Chưa triển khai | **Hoãn có chủ đích** | Chỉ xem xét sau khi các mục D/C/N, PR, E3, E4 có bằng chứng tái lập |

## Thay đổi mã trong lượt này

- CI chạy `pytest` cho cả `src/test` và `tests`, bao gồm test các script phân tích/thu thập.
- Workflow có tên run chứa fixture, cache profile và commit; artifact `experiment-<fixture>` chỉ giữ observation, gate report và timing để tổng hợp ma trận mà không phải tải toàn bộ raw reports.
- Có thể bật/tắt pip cache cho các job test, Semgrep và Checkov. E3 warm-up được đánh dấu riêng và không tính vào thống kê.
- `tests/run_fixture_matrix.py` dispatch từng fixture độc lập, khóa tất cả vào một commit, tải observation và tự tạo báo cáo E1/E2. Script cũng hỗ trợ lặp E3 cold/warm và resume sau khi bị gián đoạn.
- `tests/summarize_e3_live.py` báo median, IQR, p90, wall time, runner-minutes, từng job, số lượt hợp lệ và trạng thái thiếu bằng chứng.
- E4 đọc phiên bản Python trực tiếp trong container, ghi config digest và SHA-256 Dockerfile, dùng lại Trivy DB đã ghi metadata và có chế độ fail nếu so sánh không tương thích.
- Bản image runtime được vá APT/zlib theo security floor, cập nhật FastAPI/Starlette, và loại pip khỏi runtime. Xác minh local: image build thành công, 64/64 pytest pass, Trivy không còn ba CVE đang gây BLOCK và không còn HIGH/CRITICAL có bản vá; vẫn cần CI run mới để xác nhận gate thực tế.
- Normalizer nhận cả Trivy config status `FAIL` và `FAILED`; G2/enrichment chặn `CKV_AWS_382` và `AWS-0104`. IaC baseline giới hạn egress ALB/app theo cổng và vùng VPC, bỏ egress của DB; D16/C05/N06 patches còn áp dụng sạch.
- Thêm `conftest verify` cho G0/G1/G2 vào CI. Lần xác minh local trước đây đạt 64 pytest; artifact mới xác nhận Trivy config còn 11 finding và không còn `AWS-0104`, đồng thời workflow gate hoàn tất trên GitHub.
- G2 hiện gom các control IaC/K8s đã chọn (`CKV_AWS_21/129/145/161/226/293`, `CKV_K8S_11/35/43`, `CKV2_AWS_11/12/30`, `AWS-0132/0178/0077/0176/0177/0090`, `KSV-0125`) vào một advisory; report bridge nhận diện ID và liên kết lại các finding nguồn. Mục tiêu là thêm tối đa một dòng cảnh báo vào baseline 19 warning hiện tại; đây là dự kiến, cần CI mới xác nhận.
- Metric E1/E2/E3 phát lại từ CSV được gắn rõ nhãn thăm dò; không thể hiện như kết quả scanner live.

## Cách thu bằng chứng sau khi các thay đổi được đẩy lên GitHub

Từ thư mục `Code/DevSecOps`, sau khi `gh auth login` có quyền chạy workflow và tải artifact:

```bash
python tests/run_fixture_matrix.py \
  --ref main \
  --out-dir tests/results/live-study \
  --e3-cold-repeats 5 \
  --e3-warm-repeats 5
```

Lệnh này chạy baseline và 46 fixture độc lập, sau đó chạy một warm-up cache và
10 lượt E3 đo chính thức. Mỗi lượt lưu run URL, commit, trạng thái gate, timing
và observation. Kết quả được ghi trong `tests/results/live-study/metrics/`.
Nếu Trivy DB thay đổi trong lúc chạy ma trận, bộ tổng hợp đánh dấu dữ liệu chưa
đủ so sánh; cần chạy lại nhóm fixture trên baseline mới cùng snapshot.

Chạy E4 riêng bằng workflow `DevSecOps CI`, chọn `fixture_id=baseline` và
`run_e4=true`. Workflow hiện lỗi nếu không có báo cáo live hoặc các yếu tố so
sánh không khớp. Chỉ nhập số E4 vào báo cáo khi `causal_attribution_allowed`
là `true`.

## Việc cần làm bên ngoài repo

1. Đẩy thay đổi lên GitHub, đợi CI mới chạy; nếu lỗi, sửa trước khi thu dữ liệu.
2. Trong branch ruleset/protection của `main`, bật required checks cho
   `gate (Conftest Rego)` và `Run Python tests`. Tạo PR lỗi nghiêm trọng để chứng
   minh bị chặn, rồi PR đã sửa để chứng minh được qua.
3. Chạy ma trận fixture và E3 bằng script ở trên. Không sửa ground truth sau khi
   đã đóng băng bộ đáp án.
4. Chạy E4 riêng, tải và đối chiếu raw artifact. Sau đó mới chốt điểm tự đánh
   giá và cập nhật DOCX bằng các số có run URL.

Điểm tự đánh giá trước đây dựa trên run #13 không được tự động nâng lên chỉ vì
đã thêm mã thu thập. Chỉ tính lại rubric sau khi có kết quả live và PR evidence.
