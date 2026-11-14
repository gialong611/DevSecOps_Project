## Mục 1. Câu hỏi nghiên cứu (RQ1–RQ5)
RQ1 (E1): Mức độ hiệu quả và tỷ lệ chặn nhầm của chính sách an ninh mặc định là bao nhiêu?
RQ2 (E1): Chính sách mặc định tạo ra bao nhiêu cảnh báo và kéo dài thời gian chạy pipeline ra sao?
RQ3 (E2): Chính sách nào chặn đủ lỗi nghiêm trọng mà ít chặn nhầm mã sạch nhất?
RQ4 (E3): Việc thay đổi cấu hình kiểm tra ảnh hưởng thế nào đến thời gian chạy và số cảnh báo trên mỗi PR?
RQ5 (E4): Quyết định gate thay đổi thế nào khi tín hiệu KEV/EPSS khác nhau, và việc vá image đổi SBOM/lỗ hổng ra sao?

## Thiết kế đo và cách diễn giải

| Thí nghiệm | Đơn vị đo và biến | Chỉ số đầu ra | Cách kết luận |
|---|---|---|---|
| E1 | Một fixture D/C/N trên cùng commit baseline; tool versions và metadata Trivy DB phải khớp | Finding mới khớp tool/rule/file; phát hiện đúng hoặc bỏ sót theo D; finding mới trên C/N | Tính recall trên D; báo scanner false positive trên N riêng với finding trên C |
| E2 | Cùng một observation được đánh giá bằng G0, G1, G2 | TP/FN trên D; FP/TN trên C; số N bị chặn | So recall và false-block rate; báo N controls riêng, không gộp false positive scanner với false block gate |
| E3 | Baseline giống nhau; cấu hình cache và mức song song là biến độc lập; tối thiểu 5 lần cho mỗi cấu hình | Thời gian mỗi job và thời gian tường của workflow | Báo median và min–max (hoặc IQR); phân biệt tổng runner-minutes với đường găng của job song song |
| E4 | Cùng source/architecture và snapshot cơ sở dữ liệu; image trước/sau là biến | Image digest, package count, CVE theo severity, SBOM trước/sau | Chỉ quy thay đổi cho remediation khi tool version và Trivy DB snapshot giống nhau; nếu DB khác, báo riêng và không quy toàn bộ chênh lệch cho bản vá |

Baseline dùng fixture `baseline` trên commit gốc. Patch D/C/N được áp độc lập
trong runner; không chạy nhiều patch cùng một observation. Mỗi lượt phải lưu run
URL, commit, tool versions, metadata database, cấu hình cache/song song, artifact
thô và timing. Nếu Trivy DB đổi giữa các lượt thì thu lại nhóm với baseline mới
hoặc phân tích thành nhóm snapshot tách biệt. Báo cáo số liệu từ fixture chỉ có
ý nghĩa trong phạm vi các mẫu gieo cài này; không suy rộng thành tỷ lệ lỗ hổng
ngoài thực tế.

## Mục 2. Định nghĩa "Tê liệt" pipeline bằng con số
Pipeline được coi là bị tê liệt khi dính 1 trong các dấu hiệu sau:
1 thay đổi sạch bị chặn (False block).
Pipeline chạy quá 10 phút.
1 PR nhận hơn 20 cảnh báo.

## Mục 3. Trạng thái nguồn dữ liệu đang commit

- Artifact baseline mới nhất đã đọc là [GitHub Actions run ID 43599931890](https://github.com/gialong611/DevSecOps_Project/actions/runs/43599931890/attempts/1), commit `9ca131a678017e89d804033c3d6b75e0f2c0f366`, schema observation v3, fixture `baseline`, event `push`. Bản trích số liệu tái lập nằm ở `tests/results/metrics/ci_baseline_latest.json`; dữ liệu lưu trữ cũ nằm ở `ci_baseline_legacy_history.json`.
- Artifact ghi gate G2 `WARN`, pass, 292 finding chuẩn hóa, 0 blocker, 19 warning. Trivy config có 11 misconfiguration (2 HIGH, 6 MEDIUM, 3 LOW); Checkov có 77 finding. Gate artifact liên kết 19/19 CVE warning với finding nguồn, nhưng policy trong run chưa cảnh báo các finding IaC này.
- E3 có một observation: security-scan 30s, IaC 34s, image 117s; đường găng scan song song 117s, tổng runner 3.017 phút. Đây chỉ là một cold run, không đủ so sánh cache hoặc suy rộng ổn định.
- E4 được bỏ qua; SBOM phát hành ghi GHCR digest `sha256:655ac2d5f891848311013ed9b7e859f8bff78c21af1e2d567146f9df1eff04c9`, trong khi báo cáo image scan gắn tag cục bộ. Không coi đây là so sánh trước/sau.
- Policy G2 sau artifact gom các IaC/K8s control được chọn thành một warning có danh sách ID; report bridge cũng được cập nhật để nối ID về finding nguồn. Kết quả policy mới cần một CI run khác để đo.
- Các số liệu run #13/#14 nêu ở hồ sơ cũ là lịch sử. `findings.csv`, `decisions.csv` và `runs.csv` vẫn là dữ liệu thiết kế/thăm dò; chúng không chứng minh scanner đã phát hiện lỗi theo từng fixture.
- D/C/N live matrix, E3 đủ 5 cold + 5 warm, PR block/pass và branch protection vẫn chưa có bằng chứng hoàn chỉnh.
- E4 T0 KEV/EPSS là mô phỏng. Chỉ được gọi là live khi có hai báo cáo Trivy, hai SBOM Syft, tool version, Python/OS/architecture và snapshot vulnerability DB xác nhận giống nhau; nếu không, báo `limited`/`incomplete` và không quy kết delta.
- Observation schema tại `schemas/scan-observation.schema.json` ghi run URL, commit, phiên bản tool, timing, cache profile, raw report SHA-256, quyết định G0/G1/G2 và trạng thái E4 riêng. Observation E1–E3 không bị đánh `partial` chỉ vì E4 được chủ động bỏ qua.

### Thu thập lại fixture D/C/N và E3

Đẩy workflow/script mới lên GitHub trước; sau đó chạy từ thư mục `Code/DevSecOps`
trên máy đã đăng nhập `gh auth login` và có quyền dispatch workflow, đọc run và
tải artifact. Script tự ghim một SHA cho toàn bộ study, tải artifact nhỏ cho
từng run, ghi URL/run ID/job timing, và hỗ trợ tiếp tục bằng `--resume`.

```bash
# Baseline + 28 D + 10 C + 8 N, sau đó tạo báo cáo live E1/E2.
python tests/run_fixture_matrix.py --ref main --out-dir tests/results/live-study

# Ít nhất 5 lượt mỗi profile; chạy warm-up trước và loại khỏi thống kê.
python tests/run_fixture_matrix.py --ref main --skip-fixtures \
  --e3-cold-repeats 5 --e3-warm-repeats 5 \
  --out-dir tests/results/e3-live

# Tiếp tục sau khi bị ngắt, dùng đúng thư mục và cùng commit.
python tests/run_fixture_matrix.py --ref main --skip-fixtures \
  --e3-cold-repeats 5 --e3-warm-repeats 5 \
  --out-dir tests/results/e3-live --resume
```

Fixture matrix mặc định gồm 47 lượt (baseline + 46 mẫu); E3 thêm 11 lượt
(1 warm-up + 5 cold + 5 warm). Nếu Trivy DB hoặc tool versions khác baseline,
analyzer E1/E2 sẽ báo lỗi và không gộp số liệu. Chạy lại nhóm trong cùng cửa sổ
snapshot rồi mới công bố recall/false-positive/false-block. E3 hiện đo pip cache
trong khi scanner jobs vẫn chạy song song; không diễn giải như so sánh tuần tự.

Sau study, xem `tests/results/live-study/metrics/e1-e2-live/` và
`tests/results/e3-live/`, kiểm tra URL từng case trong `run-index.json`, rồi mới
chuyển kết quả đã xác minh sang DOCX. PPTX không thuộc phạm vi cập nhật.

### Phân tích artifact E4 đã tải

Nếu đã giải nén artifact `report-image` và `report-gate` cùng một run, xác minh
run ID/commit và đối chiếu summary với raw reports bằng:

```bash
python tests/analyze_e4_artifact.py \
  --artifact-dir "<thu_muc_report-image>" \
  --gate-artifact-dir "<thu_muc_report-gate>" \
  --out-json tests/results/metrics/e4_image_remediation.json \
  --out-md tests/results/metrics/e4_image_remediation.md
```

Script kiểm tra lại số lỗ hổng theo severity và số thành phần SBOM từ raw JSON,
lưu SHA-256, image ID/digest, Python/OS/architecture, tool version và DB
snapshot. Nếu thiếu bằng chứng per-scan hoặc có yếu tố khác nhau, kết quả được
đánh `limited` và `causal_attribution_allowed=false`.

Khi thu thập lại, lưu artifact scanner không chuẩn hóa, kết quả gate của G0/G1/G2,
URL run, hash commit, phiên bản tool, thời gian bắt đầu/kết thúc và cấu hình
cache/song song. Không thay dữ liệu fixture bằng số đo CI nếu chưa lưu nguồn.

## Ước tính chi phí runner

Sau khi tải artifact có `e3-ci-run-timing.json`, ước tính runner-minutes bằng
đơn giá và số lượt chạy/tháng do người báo cáo nhập (kèm ngày/nguồn giá):

```bash
python tests/estimate_ci_cost.py \
  --timing reports/e3-ci-run-timing.json \
  --rate-usd-per-runner-minute 0.01 \
  --rate-source "điền URL bảng giá và ngày tra cứu" \
  --runs-per-month 100 \
  --out reports/e3-cost-estimate.json
```

Đây là ước tính lập kế hoạch, không phải hóa đơn; script nêu rõ các khoản chưa
tính như làm tròn phút, quota miễn phí, lưu trữ và truyền dữ liệu. Thay ví dụ đơn
giá bằng số liệu có nguồn tại thời điểm lập báo cáo.
