# Trạng thái hoàn thiện đề tài 21

Cập nhật: 2026-11-01. Tài liệu này đối chiếu tiêu chí chấm với mã nguồn và
bằng chứng CI hiện có; điểm dưới đây chỉ là ước tính tự đánh giá, không phải
điểm của giảng viên.

## Trạng thái hiện tại

- Workflow `DevSecOps CI` chạy thành công trên commit
  `00e4f40f7488c6407e99c0076f03c0c0ba344d3c` ở
  [run #11](https://github.com/gialong611/DevSecOps_Project/actions/runs/41283884525).
  Các job test Python, quét bảo mật, IaC, image/SBOM, chuẩn hóa và gate,
  phát hành image, kiểm tra chữ ký và deploy smoke đều kết thúc thành công.
- Gate không sạch: quyết định là `WARN`, có 275 findings, 0 blockers và 30
  warnings (15 HIGH, 15 MEDIUM). Ngưỡng hơn 20 warnings được đặt cho một PR;
  đây là run `push`, nên chưa phải phép đo PR bị tê liệt, nhưng là tín hiệu nền
  vượt ngân sách nhiễu. Cần xử lý finding dựa trên raw reports, không tắt cảnh
  báo chỉ để giảm số đếm.
- Báo cáo gate đã được cải tiến tại local: cảnh báo CVE/GHSA được liên kết với
  finding nguồn, package, phiên bản hiện tại/phiên bản vá, scanner và vị trí;
  severity HIGH/MEDIUM đọc từ policy. Thay đổi này chưa có CI run mới xác nhận
  và không tự giảm số warning.
- Run này đã lưu các artifact `report-scan`, `report-iac`, `report-image`,
  `report-gate` và `sbom`. Đây là bằng chứng cho một lần chạy baseline; chưa
  phải bộ kết quả của toàn bộ fixture D/C/N.
- Run lỗi trước đó
  [#10](https://github.com/gialong611/DevSecOps_Project/actions/runs/41282982591)
  xảy ra trước khi cập nhật image Python. Log người dùng đã gửi ở thời điểm đó
  có G2 chặn `CVE-2026-115557`; run #11 sau cập nhật đã thành công. Không dùng
  cảnh báo của log cũ để mô tả trạng thái hiện tại.
- E4 chạy live trong workflow. Job log ghi nhận sau khắc phục giảm 4,533 bản ghi
  lỗ hổng Trivy và 20,061 thành phần SBOM; artifact raw chưa được mở để kiểm tra
  số tuyệt đối trước/sau, severity và image digest. Các delta này được giữ là
  kết quả log, chưa đồng bộ vào metrics E4 chuẩn.
- E1/E2 chưa có đủ quan sát cho D01–D28, C01–C10 và N01–N08. E3 hiện có một lần
  đo truy vết được cho ba job scan: 23s (security-scan), 32s (IaC), 148s (image);
  đường găng scan ước tính là 148s, không phải thời gian toàn workflow. Chưa có
  tối thiểu năm lần lặp cho từng cấu hình cache/song song. Vì vậy chưa thể kết
  luận recall, false-positive rate hay thời gian pipeline đại diện.
- DOCX/PPTX hiện có thể chưa khớp với trạng thái CI và số liệu mới; chỉ cập nhật
  sau khi đã trích xuất và kiểm tra artifact thật.

## Tự đánh giá theo tiêu chí

| Thành phần | Điểm tối đa | Ước tính | Bằng chứng còn thiếu để đạt tối đa |
|---|---:|---:|---|
| Cơ sở lý thuyết và câu hỏi nghiên cứu | 15 | 14 | Mở rộng ánh xạ chuẩn cho toàn bộ nhóm IaC và kiểm tra lại mã CIS theo phiên bản mới nhất. |
| Thiết kế kiến trúc và phương pháp | 15 | 14 | Sơ đồ pipeline và bảng biến/metric đã có; cần bổ sung sơ đồ cụ thể đường đi dữ liệu của từng finding. |
| Mức hoàn thiện thực nghiệm | 25 | 17 | Chạy và lưu đủ bộ D/C/N; xử lý baseline vượt ngân sách cảnh báo 20; minh họa một ca lỗi bị chặn và bản vá vượt gate. |
| Dữ liệu đo và phân tích | 20 | 11 | Trích kết quả raw artifact; lặp E3 theo cache/song song; kiểm tra số tuyệt đối và severity E4. |
| An toàn bảo mật và quản trị chi phí | 10 | 8 | Xác minh provenance độc lập; ghi chủ sở hữu/thời hạn ngoại lệ và đơn giá runner có nguồn. |
| Mã nguồn, tài liệu và khả năng tái lập | 10 | 7 | Cập nhật DOCX/PPTX, hướng dẫn chạy theo đúng workflow và lưu bằng chứng có thể tái lập. |
| Báo cáo trình bày và phản biện | 5 | 3 | Chuẩn bị demo lỗi/bản vá và câu trả lời dựa trên metric đo được. |
| **Tổng tự đánh giá** | **100** | **74** | **Ước tính nội bộ; chưa phải điểm chính thức.** |

## Việc cần hoàn thành tiếp

- [x] Có một lần chạy baseline end-to-end thành công, lưu artifact và liên kết
  run; gate ra `WARN` với 30 cảnh báo.
- [x] Pipeline chạy các lớp quét, gate, ký image và deploy smoke trên CI.
- [x] Có log G2 chặn lỗi trước khi vá và một run xanh sau khi cập nhật image.
- [ ] Chạy CI với liên kết cảnh báo mới để xác định dependency/package cho 15 MEDIUM đã có bản vá;
  khắc phục an toàn ít nhất 10 finding để xuống ≤20 warnings, rồi quét lại. Giữ
  15 HIGH chưa có bản vá ở mức WARN nếu policy chưa có căn cứ nâng thành BLOCK.
- [ ] Tải artifact của run #11; giải nén, kiểm tra nội dung và trích số liệu E4
  (hai báo cáo Trivy, hai SBOM Syft, digest trước/sau).
- [ ] Chạy baseline cùng D01–D28, C01–C10 và N01–N08. Các run phải cùng commit,
  phiên bản công cụ và metadata Trivy DB; tổng hợp từ artifact bằng
  `tests/analyze_fixture_observations.py`.
- [ ] Chạy tối thiểu năm lượt cho mỗi chế độ cache và song song được so sánh;
  báo thời gian tổng job và thời gian đường găng riêng.
- [ ] Xác minh chữ ký image và provenance/SLSA, lưu lệnh, digest và đầu ra xác minh.
- [ ] Ghi đơn giá runner kèm nguồn và ngày tra cứu; hoàn tất phép ước tính chi phí.
- [ ] Mở rộng đối chiếu CIS/CSA cho các fixture S3, RDS, Kubernetes và container;
  ghi rõ phiên bản framework và rule scanner tương ứng.
- [ ] Đồng bộ báo cáo DOCX/PPTX với số liệu đã kiểm tra, rồi render để rà soát bố cục.
- [ ] Chạy lại rubric sau khi các artifact và tài liệu trên được cập nhật.

## Vị trí mã nguồn và bằng chứng

- Fixture và ground truth: `Code/DevSecOps/ground_truth/`
- Workflow CI: `.github/workflows/ci.yml`
- Schema và script thu observation: `Code/DevSecOps/schemas/`,
  `Code/DevSecOps/tests/record_*`
- Script tổng hợp fixture: `Code/DevSecOps/tests/analyze_fixture_observations.py`
- Metrics hiện tại và giới hạn: `Code/DevSecOps/tests/results/metrics/`
- Hướng dẫn thu thập: `Code/DevSecOps/tests/README.md`
