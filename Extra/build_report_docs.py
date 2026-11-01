#!/usr/bin/env python3
"""Sinh báo cáo DOCX và slide PPTX nộp bài từ số liệu thực nghiệm trong repo.

Số liệu đọc từ:
    tests/results/metrics/e1_g{0,1,2}_metrics.json
    tests/results/metrics/e2_policy_comparison.json
    tests/results/metrics/e3_pipeline_duration.json
    tests/results/metrics/e4_image_remediation.json
    tests/results/metrics/policy_test_results.json

Đầu ra:
    DOCX/bao_cao_do_an_DevSecOps.docx
    PPTX/slide_thuyet_trinh_DevSecOps.pptx

Chạy: python Extra/build_report_docs.py
"""

import json
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor
from pptx import Presentation
from pptx.util import Inches, Pt as PPt

REPO = Path(__file__).resolve().parents[1]
METRICS = REPO / "Code" / "DevSecOps" / "tests" / "results" / "metrics"


def load(name):
    path = METRICS / name
    if not path.is_file():
        raise SystemExit(f"Thiếu số liệu: {path}. Chạy E1-E4 trước.")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def pct(x):
    return f"{x * 100:.2f}%"


e1 = {p: load(f"e1_{p}_metrics.json") for p in ("g0", "g1", "g2")}
e2 = load("e2_policy_comparison.json")
e3 = load("e3_pipeline_duration.json")
e4 = load("e4_image_remediation.json")

# policy_test_results.json có thể mang nhiều khuôn dạng theo run_policy_tests.ps1
try:
    policy_tests = load("policy_test_results.json")
except SystemExit:
    policy_tests = None

MEMBERS = [
    ("1", "Trần Hữu Tài", "089205009200", "tranhuultai",
     "Hạ tầng, container, chuỗi cung ứng",
     "Terraform, Kubernetes, Dockerfile an toàn; job quét IaC/image, SBOM, "
     "ký image Cosign, triển khai thử kind",
     "E4: so sánh image trước và sau khi sửa"),
    ("2", "Đỗ Ngọc Duy", "054206000955", "duy13-computer",
     "Ứng dụng, quét mã, workflow",
     "Ứng dụng FastAPI và test; gieo lỗi mã và workflow; ci.yml, job test, "
     "SAST, secret, SCA; chuẩn hóa kết quả quét, tóm tắt PR",
     "E3: đo thời gian pipeline"),
    ("3", "Hoàng Gia Long", "075206023464", "gialong611",
     "Chính sách gate, thí nghiệm, báo cáo",
     "Giả thuyết, bộ đáp án; luật G0, G1, G2 và ngoại lệ; chạy thí nghiệm, "
     "phân tích số liệu; ghép báo cáo cuối",
     "E1, E2: phát hiện lỗi; so sánh G0, G1, G2"),
]

G2_MISSED = ", ".join(e1["g2"].get("missed_defects", [])) or "không có"
E3_OVERALL = e3["overall"]


def build_docx(out_path: Path):
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(13)

    title = doc.add_heading("ĐỒ ÁN DEVSECOPS – ĐỀ TÀI 21", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub = doc.add_paragraph(
        "Xây dựng đường ống DevSecOps phát hiện cấu hình sai và lỗ hổng "
        "trước triển khai"
    )
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph(
        "Nhóm thực hiện: Trần Hữu Tài, Đỗ Ngọc Duy, Hoàng Gia Long"
    )
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # ── Phân công ──
    doc.add_heading("Bảng phân công thành viên", level=1)
    table = doc.add_table(rows=1, cols=5)
    table.style = "Light Grid Accent 1"
    hdr = table.rows[0].cells
    for i, text in enumerate(["STT", "Họ tên / MSSV / GitHub", "Vai trò",
                              "Công việc chính", "Thí nghiệm"]):
        hdr[i].text = text
    for row in MEMBERS:
        cells = table.add_row().cells
        cells[0].text = row[0]
        cells[1].text = f"{row[1]}\n{row[2]}\n{row[3]}"
        cells[2].text = row[4]
        cells[3].text = row[5]
        cells[4].text = row[6]

    # ── Chương 1 ──
    doc.add_heading("Chương 1. Nền tảng chung", level=1)
    doc.add_heading("1.1 DevSecOps", level=2)
    doc.add_paragraph(
        "DevSecOps đưa kiểm tra bảo mật tự động vào quy trình build, kiểm thử "
        "và triển khai thay vì quét một lần cuối kỳ. Trong đồ án này, toàn bộ "
        "kiểm tra bảo mật chạy trong pipeline GitHub Actions trên mỗi pull "
        "request và mỗi lần push vào nhánh chính."
    )
    doc.add_heading("1.2 Shift-left", level=2)
    doc.add_paragraph(
        "Phát hiện lỗi sớm ngay khi viết code hoặc mở pull request: năm lớp "
        "quét chạy trước khi image được ký và triển khai thử, nên lỗi bị chặn "
        "ở giai đoạn rẻ nhất để sửa."
    )
    doc.add_heading("1.3 Defense in depth", level=2)
    doc.add_paragraph(
        "Năm lớp kiểm soát độc lập (SAST, secret, SCA, IaC/K8s, image/SBOM): "
        "lớp này sót thì lớp khác bắt. Một lỗi SQL injection vẫn bị bắt bởi "
        "SAST dù SCA không thấy gì, và ngược lại một CVE thư viện vẫn bị bắt "
        "dù mã nguồn sạch."
    )
    doc.add_heading("1.4 GitHub Actions", level=2)
    doc.add_paragraph(
        "Workflow gồm job và step chạy trên runner; mã thoát khác 0 làm job "
        "đỏ. Job gate là điểm chặn duy nhất: các job quét chạy ở chế độ thu "
        "thập (thoát 0) để không mất báo cáo, còn quyết định chặn nằm ở luật "
        "Rego có kiểm thử."
    )
    doc.add_heading("1.5 Bảo vệ nhánh và CODEOWNERS", level=2)
    doc.add_paragraph(
        "Chặn merge khi gate đỏ; CODEOWNERS bắt người phụ trách duyệt thư mục "
        "nhạy cảm (policy/, security/, ground_truth/), mỗi đường dẫn khai báo "
        "hai chủ sở hữu. Việc GitHub bắt buộc review phải được bật trong branch "
        "protection rules; file CODEOWNERS một mình không đảm bảo enforcement."
    )

    # ── Chương 2 ──
    doc.add_heading("Chương 2. Lỗ hổng và rủi ro", level=1)
    doc.add_heading("2.1 CWE, CVE", level=2)
    doc.add_paragraph(
        "CWE là loại điểm yếu (ví dụ CWE-89 SQL injection); CVE là một lỗ hổng "
        "cụ thể trong một sản phẩm. Bộ đáp án ánh xạ mỗi lỗi gieo cài sang CWE "
        "và CVE tương ứng (xem Code/DevSecOps/ground_truth/README.md)."
    )
    doc.add_heading("2.2 CVSS và phân tầng BLOCK/WARN", level=2)
    doc.add_paragraph(
        "CVSS chấm mức nghiêm trọng kỹ thuật trên thang 0-10 nhưng không cho "
        "biết lỗ hổng đã bị khai thác chưa. Đồ án dùng CVSS làm trục chính "
        "(G1 chặn từ MEDIUM) và bổ sung ngữ cảnh khai thác ở G2."
    )
    doc.add_heading("2.3 EPSS, KEV", level=2)
    doc.add_paragraph(
        "EPSS là xác suất bị khai thác trong 30 ngày tới; KEV là danh mục CVE "
        "đã bị khai thác thật. G2 được cấu hình chặn CVE khớp tập KEV hoặc có "
        "EPSS >= 0.10 bất kể CVSS. Hiện EPSS snapshot chưa có nguồn và các mẫu "
        "CVE trong ground truth không khớp KEV subset đã commit; đây là thiết kế policy, chưa phải kết quả đo khai thác."
    )
    doc.add_heading("2.4 Báo nhầm, bỏ sót và mẫu đối chứng", level=2)
    doc.add_paragraph(
        "Báo nhầm (false positive) là báo lỗi khi không có lỗi; bỏ sót (false "
        "negative) là có lỗi mà không báo. Bộ đáp án gồm 8 mẫu đối chứng "
        "(N01-N08) có dạng gần giống lỗi nhưng an toàn để đo báo nhầm, và 10 "
        "thay đổi sạch (C01-C10) để đo chặn nhầm."
    )
    doc.add_heading("2.5 Bộ đáp án thực nghiệm", level=2)
    table = doc.add_table(rows=1, cols=3)
    table.style = "Light Grid Accent 1"
    hdr = table.rows[0].cells
    hdr[0].text = "Nhóm mẫu"
    hdr[1].text = "Số lượng"
    hdr[2].text = "Mục đích đo"
    for name, count, purpose in (
        ("Lỗi gieo cài D01-D28", "28", "recall, precision, F1 của gate"),
        ("Mẫu đối chứng N01-N08", "8", "nguy cơ báo nhầm của máy quét"),
        ("Thay đổi sạch C01-C10", "10", "tỷ lệ chặn nhầm của chính sách"),
    ):
        cells = table.add_row().cells
        cells[0].text = name
        cells[1].text = count
        cells[2].text = purpose

    # ── Chương 3 ──
    doc.add_heading("Chương 3. Năm lớp quét", level=1)
    scan_rows = [
        ("3.1 SAST", "Semgrep (luật auto + luật tùy chỉnh rules/semgrep)",
         "Đọc mã nguồn tìm đường đi dữ liệu tới điểm nguy hiểm", "D01-D06"),
        ("3.2 SCA", "Trivy (filesystem)",
         "Liệt kê thư viện đã khai báo và tra CVE từng thư viện", "D09-D11"),
        ("3.3 Quét secret", "Gitleaks",
         "Tìm khóa, mật khẩu trong mã và lịch sử commit bằng mẫu và entropy",
         "D07, D08"),
        ("3.4 Quét IaC", "Checkov + Trivy config",
         "So Terraform, Dockerfile, manifest với luật cấu hình an toàn",
         "D12-D25"),
        ("3.5 Image, SBOM", "Trivy image + Syft + Grype",
         "Mở từng layer image tra CVE; SBOM liệt kê thành phần image",
         "D12-D15 (image)"),
    ]
    table = doc.add_table(rows=1, cols=4)
    table.style = "Light Grid Accent 1"
    hdr = table.rows[0].cells
    for i, text in enumerate(["Lớp", "Công cụ", "Cách hoạt động", "Lỗi phủ"]):
        hdr[i].text = text
    for row in scan_rows:
        cells = table.add_row().cells
        for i, text in enumerate(row):
            cells[i].text = text

    # ── Chương 4 ──
    doc.add_heading("Chương 4. Gate và chuỗi cung ứng", level=1)
    doc.add_heading("4.1 Security gate", level=2)
    doc.add_paragraph(
        "Máy quét chỉ báo cáo; gate quyết định chặn (BLOCK), cảnh báo (WARN) "
        "hay ghi nhận (INFO). Ba hồ sơ chính sách G0, G1, G2 cùng đọc một đầu "
        "vào chuẩn hóa để so sánh được với nhau."
    )
    doc.add_heading("4.2 Policy as code", level=2)
    doc.add_paragraph(
        "Luật chặn viết bằng Rego chạy bởi Conftest, mỗi hồ sơ có tệp kiểm thử "
        "gate_test.rego chạy bằng conftest verify. Đổi luật mà không đổi test "
        "sẽ bị phát hiện ngay trong pipeline."
    )
    doc.add_heading("4.3 Fail-closed", level=2)
    doc.add_paragraph(
        "Thiếu hoặc hỏng dữ liệu đầu vào thì chặn, không cho qua: thiếu ngày "
        "hiện tại, thiếu mảng findings, finding thiếu severity đều sinh deny. "
        "Validate JSON Schema trước khi chạy gate cũng là một chốt fail-closed."
    )
    doc.add_heading("4.4 Ngoại lệ có hạn", level=2)
    doc.add_paragraph(
        "Ngoại lệ chấp nhận rủi ro có chủ sở hữu, người duyệt, lý do và ngày "
        "hết hạn; hết hạn hoặc tự duyệt thì mất hiệu lực; secret không được "
        "ngoại lệ; ngoại lệ không che được mức nghiêm trọng cao hơn nó khai."
    )
    doc.add_heading("4.5 Ghim SHA và quyền token tối thiểu", level=2)
    doc.add_paragraph(
        "Mọi action ghim commit SHA 40 ký tự (xem Extra/TOOL_VERSIONS.md); "
        "binary tải về được kiểm checksum; workflow xin quyền contents: read "
        "toàn cục, chỉ job release xin packages: write và id-token: write để "
        "ký image."
    )
    doc.add_heading("4.6 Ký image keyless", level=2)
    doc.add_paragraph(
        "Image push theo digest, ký bằng Cosign với danh tính workflow (không "
        "giữ khóa); job deploy-smoke xác minh chữ ký trước khi triển khai thử "
        "lên kind và gọi /health."
    )
    doc.add_heading("4.7 SBOM và provenance", level=2)
    doc.add_paragraph(
        "Pipeline tạo SBOM CycloneDX và ký/attest SBOM bằng Cosign keyless. "
        "Release job tạo thêm GitHub artifact attestation theo SLSA build "
        "provenance cho image digest. Cần xác nhận action thành công trên run "
        "release và kiểm tra attestation từ phía người tiêu thụ artifact."
    )

    # ── Chương 5: thí nghiệm ──
    doc.add_heading("Chương 5. Hạ tầng và thực nghiệm", level=1)
    doc.add_heading("5.1-5.3 Hạ tầng", level=2)
    doc.add_paragraph(
        "Container chạy không root, ghim digest base image, multi-stage; "
        "Terraform mô tả hạ tầng chỉ để quét không apply; Kubernetes manifest "
        "kèm ServiceAccount và RBAC tối thiểu."
    )
    doc.add_heading("5.4 Thí nghiệm E1 - phát hiện lỗi", level=2)
    table = doc.add_table(rows=1, cols=7)
    table.style = "Light Grid Accent 1"
    hdr = table.rows[0].cells
    for i, text in enumerate(["Chính sách", "Recall", "Precision", "F1",
                              "Chặn nhầm", "TP/FN", "FP/TN"]):
        hdr[i].text = text
    for policy in ("g0", "g1", "g2"):
        m = e1[policy]
        cells = table.add_row().cells
        cells[0].text = policy.upper()
        cells[1].text = pct(m["recall"])
        cells[2].text = pct(m["precision"])
        cells[3].text = f"{m['f1']:.4f}"
        cells[4].text = pct(m["false_block_rate"])
        cells[5].text = f"{m['TP']}/{m['FN']}"
        cells[6].text = f"{m['FP']}/{m['TN']}"
    doc.add_paragraph(
        f"Bảng này tính từ decisions.csv của bộ mẫu, chưa phải kết quả scanner "
        f"được tái thu thập trong lần dựng báo cáo. Theo fixture, G2 để WARN "
        f"{G2_MISSED}; cần đối chiếu với báo cáo thô và run CI trước khi xem "
        "các tỷ lệ là số đo hiệu quả phát hiện."
    )
    doc.add_heading("5.5 Thí nghiệm E3 - thời gian pipeline", level=2)
    table = doc.add_table(rows=1, cols=6)
    table.style = "Light Grid Accent 1"
    hdr = table.rows[0].cells
    for i, text in enumerate(["N", "Trung vị p50", "p90", "p95", "Max",
                              "Ngưỡng tê liệt"]):
        hdr[i].text = text
    cells = table.add_row().cells
    cells[0].text = str(E3_OVERALL["N"])
    cells[1].text = f"{E3_OVERALL['median_p50']}s"
    cells[2].text = f"{E3_OVERALL['p90']}s"
    cells[3].text = f"{E3_OVERALL['p95']}s"
    cells[4].text = f"{E3_OVERALL['max']}s"
    cells[5].text = "600s (10 phút)"
    doc.add_paragraph(
        f"{e3.get('evidence_note', 'Nguồn dữ liệu thời gian chưa được xác thực.') } "
        "Các dòng hiện có chưa so sánh cache hoặc cấu hình song song."
    )
    doc.add_heading("5.6 Thí nghiệm E4 - ảnh hưởng khắc phục", level=2)
    s = e4["structural"]
    doc.add_paragraph(
        f"Phân tích tĩnh Dockerfile cho thấy {s['remediated_count']}/"
        f"{s['total_controls']} chiều kiểm soát được khắc phục (USER không "
        "root, không ADD từ URL, không sshd/cổng 22, multi-stage). Phân tích "
        "KEV/EPSS T0 là tín hiệu mô phỏng có chủ đích, không phải snapshot lịch sử. "
        + ("Đã có số liệu Trivy và SBOM live trước/sau." if e4.get("live") and "error" not in e4["live"] else "Chưa có số liệu Trivy và SBOM live trước/sau.")
    )
    doc.add_heading("5.7 Thí nghiệm E2 - so sánh chính sách", level=2)
    doc.add_paragraph(
        f"Khuyến nghị tự động từ E2: {e2.get('recommended_policy', 'G1')}. Trên bộ "
        "decision fixture, G1 đạt recall tuyệt đối với 0 chặn nhầm; G2 cho "
        "WARN tám mẫu (D04, D06, D09, D10, D20, D22, D23, D28) và BLOCK 20/28 mẫu lỗi; "
        "G0 để 28/28 lỗi lọt. "
        "Đây là quyết định policy đã ghi, chưa phải số đo phát hiện scanner."
    )

    # ── Chương 6: kiểm chứng ──
    doc.add_heading("Chương 6. Kiểm chứng và kết luận", level=1)
    doc.add_heading("6.1 Bằng chứng kiểm nghiệm", level=2)
    bullets = [
        "Repo có unit tests cho ứng dụng, parser findings, policy Rego, luật workflow và helper E1-E4; trạng thái pass cần xác nhận bằng CI run mới.",
        "Luật workflow có fixture an toàn và fixture lỗi để kiểm tra các deny; cần giữ riêng kết quả test luật với kết quả scanner trên workflow thật.",
        "Các patch D/C/N được lưu để tái lập; bộ tổng hợp đối chiếu scanner/gate với baseline cùng commit, tool versions và Trivy DB metadata.",
        "E1/E2 hiện dùng quyết định đã ghi trong fixture; chưa có liên kết đến báo cáo scanner cho từng mẫu.",
        "E4 xác nhận cấu trúc Dockerfile; kết quả lỗ hổng/SBOM chỉ được kết luận sau khi có live output cho cả hai image.",
    ]
    for b in bullets:
        doc.add_paragraph(b, style="List Bullet")
    doc.add_heading("6.2 Kết luận", level=2)
    doc.add_paragraph(
        "Repo đã hiện thực pipeline nhiều lớp, policy-as-code, ký image và "
        "smoke test triển khai. Tuy nhiên, bộ số liệu E1-E3 hiện chưa đủ dấu "
        "vết chạy để chứng minh hiệu quả scanner, thời gian CI hoặc ảnh hưởng "
        "cache/song song; E4 cần live report trước/sau. Vì vậy kết quả hiện tại "
        "là prototype có khả năng tái lập, chưa phải đánh giá thực nghiệm hoàn tất."
    )
    doc.add_heading("6.3 Hạn chế và hướng mở", level=2)
    for b in [
        "KEV/EPSS: KEV là tập con đã đối chiếu; EPSS chưa có snapshot nguồn. T0 trong E4 là tín hiệu mô phỏng, không phải snapshot lịch sử.",
        "Chưa thu đủ phép đo CI có run URL, số lần lặp, chế độ cache bật/tắt và chạy tuần tự/song song.",
        "Chưa ước tính chi phí runner; Terraform chỉ được quét, không apply nên chưa phát sinh tài nguyên cloud từ pipeline.",
        "Chưa ánh xạ từng rule của project vào control ID cụ thể của CSA CCM/CIS; xem phần tài liệu tham khảo để xác định phạm vi chuẩn.",
    ]:
        doc.add_paragraph(b, style="List Bullet")
    doc.add_heading("Tài liệu tham khảo", level=2)
    for ref in [
        "Cloud Security Alliance, Cloud Controls Matrix v4.1: https://cloudsecurityalliance.org/artifacts/cloud-controls-matrix-v4-1",
        "Center for Internet Security, CIS Benchmarks: https://www.cisecurity.org/cis-benchmarks",
        "CIS Kubernetes Benchmark: https://www.cisecurity.org/benchmark/kubernetes",
        "SLSA, Build requirements and provenance: https://slsa.dev/spec/v1.2/build-requirements",
        "NIST, CVSS v3.1 Specification: https://www.first.org/cvss/v3.1/specification-document",
        "FIRST, Exploit Prediction Scoring System (EPSS): https://www.first.org/epss/",
        "CISA, Known Exploited Vulnerabilities Catalog: https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
    ]:
        doc.add_paragraph(ref, style="List Bullet")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out_path)
    print(f"DOCX: {out_path}")


def build_pptx(out_path: Path):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[5]  # Title Only
    title_layout = prs.slide_layouts[0]

    def add_slide(title_text):
        slide = prs.slides.add_slide(blank)
        slide.shapes.title.text = title_text
        slide.shapes.title.text_frame.paragraphs[0].font.size = PPt(32)
        return slide

    def add_body(slide, lines, size=20):
        box = slide.shapes.add_textbox(Inches(0.6), Inches(1.5),
                                       Inches(12.1), Inches(5.4))
        tf = box.text_frame
        tf.word_wrap = True
        for i, line in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = line
            p.font.size = PPt(size)
            p.space_after = PPt(8)

    def add_table(slide, rows, left=0.6, top=1.6, width=12.1, height=3.0):
        shape = slide.shapes.add_table(len(rows), len(rows[0]),
                                       Inches(left), Inches(top),
                                       Inches(width), Inches(height))
        table = shape.table
        for r, row in enumerate(rows):
            for c, value in enumerate(row):
                table.cell(r, c).text = str(value)
                for para in table.cell(r, c).text_frame.paragraphs:
                    for run in para.runs:
                        run.font.size = PPt(16)
        return table

    # 1. Bìa
    slide = prs.slides.add_slide(title_layout)
    slide.shapes.title.text = "Đồ án DevSecOps - Đề tài 21"
    slide.placeholders[1].text = (
        "Xây dựng đường ống DevSecOps phát hiện cấu hình sai và lỗ hổng "
        "trước triển khai\nTrần Hữu Tài - Đỗ Ngọc Duy - Hoàng Gia Long"
    )

    # 2. Vấn đề và mục tiêu
    slide = add_slide("Vấn đề và mục tiêu")
    add_body(slide, [
        "Vấn đề: lỗ hổng và cấu hình sai thường bị phát hiện muộn, sau khi đã triển khai.",
        "Mục tiêu: chặn lỗi trước triển khai bằng pipeline tự động trên mọi PR.",
        "Cách tiếp cận: shift-left, defense in depth 5 lớp, gate policy-as-code.",
        "Đo lường được: bộ đáp án 28 lỗi + 8 đối chứng + 10 sạch; 4 thí nghiệm E1-E4.",
    ])

    # 3. Phân công
    slide = add_slide("Phân công nhóm")
    add_table(slide, [
        ["Thành viên", "Vai trò", "Thí nghiệm"],
        ["Trần Hữu Tài", "Hạ tầng, container, chuỗi cung ứng", "E4"],
        ["Đỗ Ngọc Duy", "Ứng dụng, quét mã, workflow", "E3"],
        ["Hoàng Gia Long", "Chính sách gate, thí nghiệm, báo cáo", "E1, E2"],
    ])

    # 4. Kiến trúc
    slide = add_slide("Kiến trúc đường ống")
    add_body(slide, [
        "5 lớp quét: SAST (Semgrep) - Secret (Gitleaks) - SCA (Trivy) - IaC/K8s (Checkov, Trivy config) - Image/SBOM (Trivy, Syft, Grype).",
        "Chuẩn hóa + làm giàu: một khuôn finding, bổ sung KEV/EPSS/bản vá/độ tin cậy.",
        "Gate: Rego + Conftest, ba hồ sơ G0/G1/G2, fail-closed, ngoại lệ có hạn.",
        "Chuỗi cung ứng: push theo digest, tạo SLSA provenance, ký Cosign keyless, verify trước deploy kind.",
    ])

    # 5. Luồng gate
    slide = add_slide("Luồng quyết định gate")
    add_body(slide, [
        "reports/*.json -> normalize_findings.py (validate schema, fail-closed)",
        "-> enrich_findings.py (KEV, EPSS, fix_available, match_confidence)",
        "-> gate_input.py (ghép ngoại lệ security/exceptions.yaml)",
        "-> run_gate.sh (Conftest + policy/gN) -> gate_report + tóm tắt PR",
        "Quyết định: BLOCK chặn merge - WARN cho qua kèm cảnh báo - PASS sạch.",
    ])

    # 6. Bộ đáp án
    slide = add_slide("Bộ đáp án thực nghiệm")
    add_table(slide, [
        ["Nhóm", "Số mẫu", "Đo gì"],
        ["D01-D28 lỗi gieo cài", "28", "recall, precision, F1"],
        ["N01-N08 đối chứng", "8", "báo nhầm của máy quét"],
        ["C01-C10 thay đổi sạch", "10", "chặn nhầm của chính sách"],
    ])
    add_body(slide, [
        "Phủ 5 lớp: SAST D01-D06, secret D07-D08, SCA D09-D11, IaC/image/K8s D12-D25, workflow D26-D28.",
    ], size=16)

    # 7. Chính sách
    slide = add_slide("Ba hồ sơ chính sách gate")
    add_table(slide, [
        ["Hồ sơ", "Luật chặn", "Ý nghĩa"],
        ["G0", "Không chặn gì", "đo nhiễu nền: 28/28 lỗi lọt"],
        ["G1", "Mọi MEDIUM+", "máy móc theo CVSS"],
        ["G2", "KEV, EPSS>=0.10, secret, bản vá, khóa kiểm soát cao", "ngữ cảnh rủi ro"],
    ])

    # 8. E1
    slide = add_slide("E1 - Hiệu quả phát hiện lỗi")
    rows = [["Chính sách", "Recall", "Precision", "F1", "Chặn nhầm"]]
    for policy in ("g0", "g1", "g2"):
        m = e1[policy]
        rows.append([policy.upper(), pct(m["recall"]), pct(m["precision"]),
                     f"{m['f1']:.4f}", pct(m["false_block_rate"])])
    add_table(slide, rows)
    add_body(slide, [
        f"Quyết định fixture ghi G2 WARN {G2_MISSED}; chưa đối chiếu đủ với raw scanner reports.",
    ], size=16)

    # 9. E2
    slide = add_slide("E2 - Chọn chính sách")
    add_body(slide, [
        f"Khuyến nghị tự động: {str(e2.get('recommended_policy', 'G1')).upper()} theo decision fixture, không phải phép đo scanner.",
        "Đây là kết quả trên decision fixture, không phải tối ưu có trọng số ma sát.",
        "10 clean có decision fixture; 8 negative controls chưa có kết quả scan độc lập.",
    ])

    # 10. E3
    slide = add_slide("E3 - Thời gian pipeline")
    add_table(slide, [
        ["N", "p50", "p90", "p95", "Max", "Ngưỡng"],
        [E3_OVERALL["N"], f"{E3_OVERALL['median_p50']}s",
         f"{E3_OVERALL['p90']}s", f"{E3_OVERALL['p95']}s",
         f"{E3_OVERALL['max']}s", "600s"],
    ])
    add_body(slide, [
        e3.get("evidence_note", "Nguồn thời gian CI chưa được xác thực."),
        "Chưa có so sánh bật/tắt cache hoặc tuần tự/song song.",
    ], size=16)

    # 11. E4
    slide = add_slide("E4 - Khắc phục image")
    s = e4["structural"]
    add_body(slide, [
        f"Dockerfile: khắc phục {s['remediated_count']}/{s['total_controls']} chiều "
        "(không root, không ADD URL, không sshd/22, multi-stage).",
        f"Độ nhạy mô phỏng: {e4['db_drift']['changed_count']} quyết định G2 đổi "
        "khi tín hiệu KEV/EPSS thay đổi; T0 không phải dữ liệu lịch sử.",
        "Kết quả live trước/sau chỉ được kết luận khi artifact report-image có đủ 2 scan Trivy và 2 SBOM Syft.",
    ])

    # 12. Kiểm chứng
    slide = add_slide("Bằng chứng kiểm nghiệm")
    add_body(slide, [
        "Repo có test ứng dụng, parser và policy; trạng thái pass phải xác nhận bằng CI run mới.",
        "Workflow quét .github/workflows bằng Checkov; luật Rego workflow có fixture riêng.",
        "Patch có thể tái lập nhưng apply sạch không đồng nghĩa scanner đã phát hiện.",
        "E1/E2 là kết quả fixture; cần raw scanner reports và URL run cho số đo detection.",
    ])

    # 13. Kết luận
    slide = add_slide("Kết luận")
    add_body(slide, [
        "Repo hiện có prototype pipeline nhiều lớp, policy-as-code, image signing và deploy smoke test.",
        "Bằng chứng E1-E3 chưa đủ để kết luận hiệu quả detection hoặc thời gian CI đại diện.",
        "E4 cần artifact live Trivy/Syft trước-sau; SLSA provenance cần được xác nhận trên release run.",
        "Kết luận thực nghiệm cần cập nhật sau khi thu thập các run có thể truy vết.",
    ])

    out_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(out_path)
    print(f"PPTX: {out_path}")


def main():
    build_docx(REPO / "DOCX" / "bao_cao_do_an_DevSecOps.docx")
    build_pptx(REPO / "PPTX" / "slide_thuyet_trinh_DevSecOps.pptx")
    return 0


if __name__ == "__main__":
    sys.exit(main())
