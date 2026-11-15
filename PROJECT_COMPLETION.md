# Trạng thái hoàn thiện đề tài 21

Cập nhật: 2026-11-15. Báo cáo này phân biệt số đo từ scanner/CI trực tiếp với
dữ liệu mô phỏng. Các file raw lớn nằm trong thư mục kết quả cục bộ và không
được commit; bảng dưới đây ghi số đo, mã commit và URL để truy vết.

## Tóm tắt kết quả

| Thí nghiệm | Kết quả đã đo | Diễn giải |
|---|---|---|
| E1 – scanner D/C/N | 38/38 fixture D/C và 8/8 negative control hoàn tất; scanner kỳ vọng tìm thấy 28/28 lỗi D; C có finding mới 0/10; finding false positive theo rule đích trên N là 0/8 | Đo trực tiếp từ raw scanner reports, không lấy ground truth làm kết quả phát hiện |
| E2 – gate G0/G1/G2 | G1: TP/FN/FP/TN = 28/0/0/10; G2 = 23/0/0/15. Block recall trên D đều 100%, false-block trên C là 0%. Block khớp rule đích: G1 27/28, G2 22/23 | Gate khớp hành động kỳ vọng 38/38. Có 1 N bị G1 chặn (1/8); G0/G2 chặn 0/8. Một số blocker đúng mức release nhưng không trùng rule/CVE gieo cài |
| E3 – thời gian CI | 5 lượt cold + 5 warm cùng commit và cùng snapshot Trivy/Grype. Wall median: 104s cold, 110s warm; IQR 4s/6s; scan-stage median 88s/90s; tổng runner-minutes median 3.17/3.25 | Pip cache warm chậm hơn 6s (5.77%) trong mẫu này; không có bằng chứng cải thiện tốc độ. Job image là job dài nhất: median 56s cold, 63s warm |
| E4 – image/SBOM | 4.486 → 206 finding (-95,4%); CRITICAL 18 → 0, HIGH 804 → 47; SBOM 22.943 → 2.856 gói (-87,6%) | Cùng Python 3.13.18, Debian 13.7, amd64, Trivy 0.76.1 và DB snapshot theo từng scan đã khớp. Có thể quy delta cho toàn bộ thay đổi Dockerfile/image, không tách riêng tác động từng package |

## Bằng chứng và giới hạn

- E1/E2: tổng hợp 48 observation (2 baseline theo SHA, 38 D/C và 8 N), tool
  versions và snapshot DB ghim nhất quán. Báo cáo live ở
  `Code/DevSecOps/tests/results/combined-live-study-bb94f33-a0d6a8e/metrics/e1-e2-live/`;
  nguồn và run URL nằm trong `source-manifest.json` và JSON cạnh Markdown.
- E3: [10 lượt đo trên cùng commit](https://github.com/gialong611/DevSecOps_Project/actions/runs/43720462402)
  đến [run cuối](https://github.com/gialong611/DevSecOps_Project/actions/runs/43722229167),
  một warm-up bị loại. So sánh chỉ thay đổi pip cache; scanner jobs tiếp tục chạy
  song song. Vì vậy kết luận giới hạn ở profile này và không chứng minh serial-vs-parallel.
- E4: [GitHub Actions run 43723320787](https://github.com/gialong611/DevSecOps_Project/actions/runs/43723320787/attempts/1).
  Hai image có config digest và Dockerfile SHA-256; chưa có registry manifest
  digest vì image chỉ được scan cục bộ. Kết quả được đánh `comparable`, DB snapshot
  được xác minh trước/sau từng lần scan. Số liệu SBOM/finding lấy lại từ raw Trivy
  và Syft report.
- E1/E2 và E3 đã ghi nhận G2 baseline bị BLOCK do finding Gitleaks trong lịch sử
  repo. Pipeline test, DB và scanner vẫn hoàn thành ở các lượt E3 được chấp nhận;
  trạng thái gate không bị che giấu. Chủ repo cần xác minh, thu hồi credential nếu
  còn hiệu lực và xử lý lịch sử trước khi coi baseline là sạch. Không đưa giá trị
  secret vào báo cáo.
- GitHub hiện chưa có branch protection/ruleset cho `main` (API protection trả
  404 và danh sách rulesets rỗng tại thời điểm kiểm tra). Do đó chưa có bằng chứng
  PR lỗi bị required check chặn, PR đã sửa được merge, hay check bắt buộc trước merge.
- T0 KEV/EPSS trong E4 vẫn là mô phỏng; không trình bày như dữ liệu lịch sử CISA/FIRST.
  Chưa có registry digest nên không khẳng định cùng một image đã publish.

## Mức hoàn thiện theo tiêu chí đánh giá

Phần thực nghiệm và dữ liệu đo đã tiến bộ rõ: E1–E4 có số đo CI, snapshot và
nguồn truy vết. Các hạng mục chưa thể đánh dấu hoàn tất là xác minh gate qua PR
thật/branch protection, xử lý finding Gitleaks lịch sử, và bổ sung bằng chứng
registry/provenance nếu muốn chứng minh image phát hành. Vì vậy chưa nên ghi đề tài
100/100 hoặc tuyên bố toàn bộ quy trình merge đã được kiểm chứng.

AWS được hoãn để giữ trọng tâm và bảo toàn tính tái lập. Theo phạm vi đã thống
nhất, DOCX/PPTX không được chỉnh sửa trong lượt này; số liệu đã được cập nhật vào
tài liệu Markdown trong repo.

## Chạy lại thí nghiệm

Từ `Code/DevSecOps`, máy cần GitHub CLI đã đăng nhập và quyền dispatch workflow:

```bash
python tests/run_fixture_matrix.py --ref main --out-dir tests/results/live-study --parallelism 4

python tests/run_fixture_matrix.py --ref main --skip-fixtures \
  --e3-cold-repeats 5 --e3-warm-repeats 5 --out-dir tests/results/e3-live
```

Script ghim một SHA cho từng study, lưu run URL/ID, observation, timing và hỗ trợ
resume. Nếu Trivy hoặc Grype DB snapshot khác nhau, tách nhóm snapshot hoặc chạy
lại; không gộp các mẫu không tương thích. E4 có thể phân tích lại artifact bằng
`tests/analyze_e4_artifact.py`; chỉ quy kết delta khi `causal_attribution_allowed`
là `true`.

## Việc còn lại để khép đề tài

1. Xử lý finding Gitleaks lịch sử một cách an toàn; chạy baseline sạch sau xử lý.
2. Bật branch protection/ruleset trên `main` với Python tests và gate là required checks.
3. Tạo PR chứa lỗi nghiêm trọng để xác nhận bị chặn, rồi PR đã sửa để xác nhận qua.
4. Nếu cần bằng chứng cho artifact phát hành, push image theo digest cố định và
   liên kết digest đó với SBOM, scan report và provenance.
