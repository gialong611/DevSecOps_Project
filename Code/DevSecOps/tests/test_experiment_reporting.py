"""Regression tests for live observation aggregation and evidence labeling."""

import json
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).parent
sys.path.insert(0, str(TESTS_DIR))

import analyze_fixture_observations as fixtures  # noqa: E402
import analyze_e4_artifact as e4_artifact  # noqa: E402
import e1_detection_effectiveness as e1  # noqa: E402
import e4_image_remediation as e4  # noqa: E402
import record_scan_observation as observation  # noqa: E402
import run_fixture_matrix as matrix  # noqa: E402
import summarize_e3_live as e3  # noqa: E402


def test_static_policy_decisions_are_not_labeled_as_live_scanner_metrics():
    metrics = e1.compute_metrics(
        {"D01": {"severity": "CRITICAL"}},
        {"C01"},
        {},
        "g2",
        {"g2": {"D01": "BLOCK", "C01": "PASS"}},
    )
    assert metrics["evidence_status"] == "exploratory-policy-replay"
    assert metrics["empirical_scanner_metric"] is False


def test_e3_stats_report_median_and_iqr():
    result = e3.stats([100, 110, 120, 130, 140])
    assert result == {
        "N": 5,
        "median": 120.0,
        "q1": 110.0,
        "q3": 130.0,
        "iqr": 20.0,
        "p90": 136.0,
    }


def test_e3_excludes_warmups_and_incomplete_observations(tmp_path):
    warmup = {
        "key": "e3-warmup",
        "fixture_id": "baseline",
        "cache_mode": "warm",
        "benchmark_role": "warmup",
        "conclusion": "success",
        "observation_status": "complete",
    }
    incomplete = {
        "key": "e3-incomplete",
        "fixture_id": "baseline",
        "cache_mode": "cold",
        "benchmark_role": "measurement",
        "conclusion": "success",
        "artifact_path": str(tmp_path / "incomplete"),
    }
    obs_dir = tmp_path / "incomplete"
    obs_dir.mkdir()
    (obs_dir / "observation.json").write_text(
        json.dumps({"fixture_id": "baseline", "evidence_status": "partial"}),
        encoding="utf-8",
    )
    report = e3.build_report({"runs": [warmup, incomplete]}, tmp_path / "run-index.json")
    assert report["profiles"]["cold"]["N"] == 0
    assert report["profiles"]["warm"]["N"] == 0
    assert len(report["excluded_runs"]) == 2
    assert report["evidence_status"] == "partial"


def test_e3_requires_five_runs_per_cache_with_one_commit_and_db_snapshot(tmp_path):
    runs = []
    for mode in ("cold", "warm"):
        for number in range(5):
            run_id = f"{mode}-{number}"
            obs_dir = tmp_path / run_id
            obs_dir.mkdir()
            observation = {
                "evidence_status": "complete",
                "fixture_id": "baseline",
                "commit": "abc123",
                "cache_mode": mode,
                "benchmark_role": "measurement",
                "tool_versions_configured": {"trivy": "0.76.1"},
                "trivy_runtime": {
                    "security-scan": {
                        "databases": {"Vulnerability DB": {"updated_at": "2026-11-01T00:00:00Z"}}
                    }
                },
            }
            (obs_dir / "observation.json").write_text(json.dumps(observation), encoding="utf-8")
            runs.append({
                "key": f"e3-{mode}-{number}",
                "run_id": run_id,
                "fixture_id": "baseline",
                "cache_mode": mode,
                "benchmark_role": "measurement",
                "conclusion": "success",
                "head_sha": "abc123",
                "observation_status": "complete",
                "artifact_path": str(obs_dir),
                "workflow_wall_seconds": 90 + number,
                "workflow_runner_minutes": 2.0,
                "scan_stage_wall_seconds": 60 + number,
                "scan_stage_runner_minutes": 1.0,
                "job_durations_seconds": {
                    "Security scans (collection mode)": 20,
                    "iac": 25,
                    "image": 60,
                },
            })
    report = e3.build_report({"runs": runs}, tmp_path / "run-index.json")
    assert report["evidence_status"] == "complete"
    assert report["acceptance"]["same_commit"] is True
    assert report["acceptance"]["trivy_database_snapshot_consistent"] is True

    runs[-1]["head_sha"] = "different-commit"
    observation = json.loads((tmp_path / "warm-4" / "observation.json").read_text(encoding="utf-8"))
    observation["commit"] = "different-commit"
    (tmp_path / "warm-4" / "observation.json").write_text(json.dumps(observation), encoding="utf-8")
    report = e3.build_report({"runs": runs}, tmp_path / "run-index.json")
    assert report["evidence_status"] == "partial"
    assert report["acceptance"]["same_commit"] is False


def test_fixture_comparison_requires_target_rule_and_file():
    assert fixtures.path_matches("Code/DevSecOps/src/app/main.py", "src/app/main.py")
    assert fixtures.finding_matches_rule(
        {"rule_id": "semgrep.sql-injection", "resource": ""},
        ["sql-injection"],
    )
    assert not fixtures.finding_matches_rule(
        {"rule_id": "semgrep.other", "resource": ""},
        ["sql-injection"],
    )


def test_run_matrix_timing_counts_wall_and_runner_time_separately():
    details = {
        "jobs": [
            {"name": "Security scans (collection mode)", "startedAt": "2026-01-01T00:00:00Z", "completedAt": "2026-01-01T00:00:20Z"},
            {"name": "iac", "startedAt": "2026-01-01T00:00:02Z", "completedAt": "2026-01-01T00:00:22Z"},
            {"name": "image", "startedAt": "2026-01-01T00:00:01Z", "completedAt": "2026-01-01T00:01:01Z"},
            {"name": "gate (Conftest Rego)", "startedAt": "2026-01-01T00:01:02Z", "completedAt": "2026-01-01T00:01:20Z"},
        ]
    }
    result = matrix.job_timing(details)
    assert result["scan_stage_wall_seconds"] == 61.0
    assert result["scan_stage_runner_minutes"] == 1.667
    assert result["workflow_wall_seconds"] == 80.0
    assert result["workflow_runner_minutes"] == 1.967


def test_run_matrix_ignores_old_runs_with_the_same_display_title():
    run = {
        "databaseId": 99,
        "event": "workflow_dispatch",
        "headSha": "abc123",
        "displayTitle": "DevSecOps CI | baseline | cold | measurement | abc123 | study001",
    }
    assert matrix.matching_runs(
        [run], "baseline", "cold", "measurement", "abc123", "study001",
        known_run_ids={99},
    ) == []
    assert matrix.matching_runs(
        [run], "baseline", "cold", "measurement", "abc123", "study001",
    ) == [run]


def test_run_matrix_requests_created_at_before_selecting_latest_run(monkeypatch):
    suffix = "| baseline | cold | measurement | abc123 | study001"
    runs = [
        {
            "databaseId": 100,
            "event": "workflow_dispatch",
            "headSha": "abc123",
            "displayTitle": f"DevSecOps CI {suffix}",
            "createdAt": "2026-01-01T00:00:00Z",
        },
        {
            "databaseId": 101,
            "event": "workflow_dispatch",
            "headSha": "abc123",
            "displayTitle": f"DevSecOps CI {suffix}",
            "createdAt": "2026-01-02T00:00:00Z",
        },
    ]
    requested = {}

    def fake_gh_json(args):
        requested["args"] = args
        return runs

    monkeypatch.setattr(matrix, "gh_json", fake_gh_json)
    latest = matrix.list_matching_run(
        "owner/repo", "main", "baseline", "cold", "measurement",
        "abc123", "study001",
    )

    assert latest["databaseId"] == 101
    json_fields = requested["args"][requested["args"].index("--json") + 1].split(",")
    assert "createdAt" in json_fields


def test_run_matrix_normalizes_baseline_and_fixture_ids():
    assert matrix.normalize_fixture_id("baseline") == "baseline"
    assert matrix.normalize_fixture_id("BASELINE") == "baseline"
    assert matrix.normalize_fixture_id("d04") == "D04"


def test_e4_database_snapshot_must_be_present_and_normalized():
    valid = {
        "databases": {
            "Vulnerability DB": {
                "version": "2",
                "updated_at": "2026-11-01T00:00:00Z",
                "next_update": "2026-11-02T00:00:00Z",
            }
        }
    }
    assert e4.normalized_vulnerability_db(valid) == {
        "version": "2",
        "updated_at": "2026-11-01T00:00:00Z",
        "next_update": "2026-11-02T00:00:00Z",
    }
    assert e4.normalized_vulnerability_db({"databases": {}}) is None


def test_e4_artifact_ingestion_checks_raw_totals_and_limits_causal_claim(tmp_path):
    def write_json(relative, value):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")

    for side, image_id, python_version, severity in (
        ("before", "sha256:before", "3.12.15", "HIGH"),
        ("after", "sha256:after", "3.12.16", "LOW"),
    ):
        write_json(f"raw/e4/trivy-image-{side}.json", {
            "Metadata": {
                "ImageID": image_id,
                "RepoTags": [f"image-{side}:test"],
                "RepoDigests": [],
                "OS": {"Family": "debian", "Name": "13.7"},
                "ImageConfig": {
                    "architecture": "amd64",
                    "config": {"Env": [f"PYTHON_VERSION={python_version}"]},
                },
            },
            "Results": [{"Vulnerabilities": [{"Severity": severity}]}],
        })
        write_json(f"raw/e4/sbom-{side}.cdx.json", {
            "serialNumber": f"urn:{side}",
            "metadata": {"timestamp": "2026-11-01T00:00:00Z"},
            "components": [{"name": "example"}],
        })

    write_json("experiment/trivy-runtime-image.json", {
        "trivy_version": "0.76.1",
        "databases": {"Vulnerability DB": {"version": "2", "updated_at": "2026-11-01T00:00:00Z"}},
        "error": None,
    })
    write_json("timing/image.json", {
        "run_id": "123",
        "run_attempt": "1",
        "run_url": "https://github.com/example/project/actions/runs/123",
        "commit": "abc123",
        "fixture_id": "baseline",
    })
    write_json("e4/e4_image_remediation.json", {
        "experiment": "E4",
        "structural": {
            "before": {"non_root_user": False, "no_add_remote": False, "no_sshd_or_port22": False, "multi_stage": False},
            "after": {"non_root_user": True, "no_add_remote": True, "no_sshd_or_port22": True, "multi_stage": True},
            "remediated_count": 4,
            "total_controls": 4,
        },
        "db_drift": {"description": "simulated", "rows": [], "changed_count": 0, "changed_decisions": []},
        "live": {
            "before": {"vulnerabilities": {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}, "sbom_packages": 1},
            "after": {"vulnerabilities": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 1, "UNKNOWN": 0}, "sbom_packages": 1},
            "delta": {"vulnerabilities_total": 0, "sbom_packages": 0},
        },
    })

    result = e4_artifact.analyze(tmp_path)
    assert result["live"]["before"]["vulnerabilities_total"] == 1
    assert result["live"]["after"]["vulnerabilities_total"] == 1
    assert result["evidence_status"] == "limited"
    assert result["causal_attribution_allowed"] is False
    assert result["live"]["comparability"]["same_python_version"] is False
    assert result["live"]["comparability"]["job_level_trivy_snapshot_recorded"] is True
    assert result["live"]["raw_artifact_sha256"]["trivy_before"]


def test_e1_e3_observation_does_not_require_optional_e4_artifacts(monkeypatch, tmp_path):
    reports = tmp_path / "reports"
    experiment = reports / "experiment"
    experiment.mkdir(parents=True)
    for name in observation.RAW_REPORTS:
        path = reports / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("[]\n", encoding="utf-8")
    (reports / "grype-image.json").write_text(json.dumps({
        "descriptor": {
            "version": "0.120.1",
            "db": {"status": {
                "schemaVersion": "v6.1.10",
                "built": "2026-11-01T00:00:00Z",
                "from": "https://example.invalid/grype-db.tar.zst",
                "valid": True,
            }},
        },
        "matches": [],
    }), encoding="utf-8")
    (reports / "normalized_findings.json").write_text("[]\n", encoding="utf-8")
    (experiment / "trivy-runtime-security-scan.json").write_text(
        json.dumps({
            "trivy_version": "0.76.1",
            "databases": {"Vulnerability DB": {"updated_at": "2026-11-01T00:00:00Z"}},
            "error": None,
        }),
        encoding="utf-8",
    )
    gate = tmp_path / "gate.json"
    gate.write_text(json.dumps({"decision": "PASS", "policy_profile": "g2", "summary": {}}), encoding="utf-8")
    timing = tmp_path / "timing.json"
    timing.write_text(json.dumps({
        "fixture_id": "baseline",
        "run_id": "123",
        "run_attempt": "1",
        "commit": "abc123",
        "cache_mode": "cold",
        "benchmark_role": "measurement",
        "scan_execution_mode": "parallel",
        "scan_stage_started_at": "2026-11-01T00:00:00Z",
        "scan_stage_ended_at": "2026-11-01T00:01:00Z",
    }), encoding="utf-8")
    out = experiment / "observation.json"
    monkeypatch.setenv("GITHUB_EVENT_NAME", "workflow_dispatch")
    monkeypatch.setenv("GITHUB_RUN_ID", "123")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "1")
    monkeypatch.setenv("GITHUB_REPOSITORY", "example/project")
    monkeypatch.setenv("GITHUB_SHA", "abc123")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    monkeypatch.setenv("TRIVY_VERSION", "0.76.1")
    monkeypatch.setenv("GRYPE_VERSION", "0.120.1")
    monkeypatch.setenv("FIXTURE_ID", "baseline")
    monkeypatch.setenv("RUN_E4", "false")
    monkeypatch.setenv("CACHE_MODE", "cold")
    monkeypatch.setenv("BENCHMARK_ROLE", "measurement")
    monkeypatch.setenv("SCAN_EXECUTION_MODE", "parallel")
    monkeypatch.setenv("CONTEST_POLICY", "g2")
    monkeypatch.setattr(sys, "argv", [
        "record_scan_observation.py",
        "--reports-dir", str(reports),
        "--gate-report", str(gate),
        "--timing-summary", str(timing),
        "--out", str(out),
    ])

    assert observation.main() == 0
    result = json.loads(out.read_text(encoding="utf-8"))
    assert result["evidence_status"] == "complete"
    assert result["schema_version"] == 4
    assert result["e4_evidence_status"] == "not_requested"
    assert result["e4_requested"] is False
    assert all(not value["present"] for value in result["e4_raw_reports"].values())
    assert result["grype_runtime"]["grype_version"] == "0.120.1"
    assert result["grype_runtime"]["db"]["built"] == "2026-11-01T00:00:00Z"
    assert result["issues"] == []
