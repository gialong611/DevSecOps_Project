#!/usr/bin/env python3
"""Summarize controlled E3 GitHub Actions runs by cold/warm pip-cache profile."""

import argparse
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path


MIN_RUNS_PER_PROFILE = 5


def parse_time(value):
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def percentile(values, p):
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return None
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * p / 100
    low = math.floor(rank)
    high = math.ceil(rank)
    return ordered[low] + (ordered[high] - ordered[low]) * (rank - low)


def stats(values):
    if not values:
        return {"N": 0, "median": None, "q1": None, "q3": None, "iqr": None, "p90": None}
    q1 = percentile(values, 25)
    q3 = percentile(values, 75)
    return {
        "N": len(values),
        "median": round(percentile(values, 50), 2),
        "q1": round(q1, 2),
        "q3": round(q3, 2),
        "iqr": round(q3 - q1, 2),
        "p90": round(percentile(values, 90), 2),
    }


def load_index(path):
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict) or not isinstance(data.get("runs"), list):
        raise ValueError(f"{path} must contain an object with a runs array")
    return data


def load_observation(run, root):
    candidate = run.get("observation_path")
    if candidate:
        path = Path(candidate)
        if not path.is_absolute():
            path = root / path
        if path.is_file():
            try:
                value = json.loads(path.read_text(encoding="utf-8-sig"))
                return value if isinstance(value, dict) else None
            except (OSError, json.JSONDecodeError):
                return None
    artifact_path = run.get("artifact_path")
    if artifact_path:
        root_path = Path(artifact_path)
        if not root_path.is_absolute():
            root_path = root / root_path
        for path in root_path.rglob("observation.json"):
            try:
                value = json.loads(path.read_text(encoding="utf-8-sig"))
                if isinstance(value, dict):
                    return value
            except (OSError, json.JSONDecodeError):
                continue
    return None


def build_report(index, index_path):
    root = index_path.parent
    included = []
    excluded = []
    for run in index["runs"]:
        if not str(run.get("key", "")).startswith("e3-"):
            continue
        if run.get("fixture_id") != "baseline":
            continue
        if run.get("benchmark_role", "measurement") == "warmup":
            excluded.append({"run_id": run.get("run_id"), "reason": "warm-up run"})
            continue
        if run.get("conclusion") != "success":
            excluded.append({"run_id": run.get("run_id"), "reason": "workflow did not succeed"})
            continue
        observation = load_observation(run, root)
        if not observation or observation.get("evidence_status") != "complete":
            excluded.append({"run_id": run.get("run_id"), "reason": "missing or incomplete observation"})
            continue
        if observation.get("fixture_id") != "baseline":
            excluded.append({"run_id": run.get("run_id"), "reason": "observation is not baseline"})
            continue
        if observation.get("commit") != run.get("head_sha"):
            excluded.append({"run_id": run.get("run_id"), "reason": "index and observation commits differ"})
            continue
        if observation.get("cache_mode") != run.get("cache_mode"):
            excluded.append({"run_id": run.get("run_id"), "reason": "index and observation cache modes differ"})
            continue
        if observation.get("benchmark_role", "measurement") != run.get("benchmark_role", "measurement"):
            excluded.append({"run_id": run.get("run_id"), "reason": "index and observation benchmark roles differ"})
            continue
        if not all(isinstance(run.get(field), (int, float)) for field in (
            "workflow_wall_seconds", "workflow_runner_minutes",
            "scan_stage_wall_seconds", "scan_stage_runner_minutes",
        )):
            excluded.append({"run_id": run.get("run_id"), "reason": "missing complete timing metrics"})
            continue
        required_scan_jobs = {"Security scans (collection mode)", "iac", "image"}
        if not required_scan_jobs.issubset((run.get("job_durations_seconds") or {}).keys()):
            excluded.append({"run_id": run.get("run_id"), "reason": "missing one or more scanner job durations"})
            continue
        run = dict(run)
        run["observation"] = observation
        included.append(run)

    by_profile = defaultdict(list)
    for run in included:
        by_profile[run.get("cache_mode", "cold")].append(run)

    profiles = {}
    for mode in ("cold", "warm"):
        records = by_profile.get(mode, [])
        workflow_wall = [r["workflow_wall_seconds"] for r in records if isinstance(r.get("workflow_wall_seconds"), (int, float))]
        workflow_runner = [r["workflow_runner_minutes"] for r in records if isinstance(r.get("workflow_runner_minutes"), (int, float))]
        scan_wall = [r["scan_stage_wall_seconds"] for r in records if isinstance(r.get("scan_stage_wall_seconds"), (int, float))]
        scan_runner = [r["scan_stage_runner_minutes"] for r in records if isinstance(r.get("scan_stage_runner_minutes"), (int, float))]
        job_names = sorted({name for r in records for name in (r.get("job_durations_seconds") or {})})
        per_job = {}
        for name in job_names:
            values = [
                r["job_durations_seconds"][name]
                for r in records
                if isinstance(r.get("job_durations_seconds"), dict)
                and isinstance(r["job_durations_seconds"].get(name), (int, float))
            ]
            per_job[name] = stats(values)
        commits = sorted({r.get("head_sha") for r in records if r.get("head_sha")})
        version_sets = {
            json.dumps(r["observation"].get("tool_versions_configured", {}), sort_keys=True)
            for r in records
        }
        db_snapshots = sorted({
            json.dumps({
                key: meta.get(key)
                for key in ("version", "updated_at", "next_update")
                if meta.get(key) is not None
            }, sort_keys=True)
            for r in records
            for name, meta in (
                r["observation"].get("trivy_runtime", {})
                .get("security-scan", {}).get("databases", {}).items()
            )
            if "vulnerability" in name.casefold()
            and isinstance(meta, dict) and meta.get("updated_at")
        })
        profiles[mode] = {
            "N": len(records),
            "run_ids": [r.get("run_id") for r in records],
            "commits": commits,
            "tool_version_sets": len(version_sets),
            "tool_version_fingerprints": sorted(version_sets),
            "trivy_db_snapshots": db_snapshots,
            "workflow_wall_seconds": stats(workflow_wall),
            "workflow_runner_minutes": stats(workflow_runner),
            "scan_stage_wall_seconds": stats(scan_wall),
            "scan_stage_runner_minutes": stats(scan_runner),
            "per_job_seconds": per_job,
        }

    same_commit = (
        len(profiles["cold"]["commits"]) == 1
        and profiles["cold"]["commits"] == profiles["warm"]["commits"]
        and len(profiles["warm"]["commits"]) == 1
    )
    versions_match = (
        len(profiles["cold"]["tool_version_fingerprints"]) == 1
        and len(profiles["warm"]["tool_version_fingerprints"]) == 1
        and profiles["cold"]["tool_version_fingerprints"]
        == profiles["warm"]["tool_version_fingerprints"]
    )
    enough_repeats = all(profiles[mode]["N"] >= MIN_RUNS_PER_PROFILE for mode in ("cold", "warm"))
    cold_db = set(profiles["cold"]["trivy_db_snapshots"])
    warm_db = set(profiles["warm"]["trivy_db_snapshots"])
    database_snapshots_match = bool(cold_db) and cold_db == warm_db and len(cold_db) == 1
    complete = same_commit and versions_match and enough_repeats and database_snapshots_match
    cold_median = profiles["cold"]["workflow_wall_seconds"]["median"]
    warm_median = profiles["warm"]["workflow_wall_seconds"]["median"]
    delta = None
    if cold_median is not None and warm_median is not None:
        delta = {
            "warm_minus_cold_seconds": round(warm_median - cold_median, 2),
            "warm_change_percent": round((warm_median - cold_median) / cold_median * 100, 2) if cold_median else None,
            "interpretation": "negative means the warm pip-cache profile was faster by the median wall time",
        }

    return {
        "experiment": "E3 controlled CI duration",
        "evidence_status": "complete" if complete else "partial",
        "measurement_definition": {
            "workflow_wall_seconds": "min(job.started_at) to max(job.completed_at) for one workflow_dispatch run",
            "workflow_runner_minutes": "sum of measured durations for all completed jobs divided by 60",
            "scan_stage_wall_seconds": "first start to last completion among security-scan, iac, and image jobs",
            "scan_stage_runner_minutes": "sum of those three scanner job durations divided by 60",
            "cache_variable": "actions/setup-python pip cache for pytest/runtime dependencies, Semgrep, and Checkov installations",
            "execution_mode": "parallel scanner jobs; this experiment does not claim a serial-mode comparison",
            "warmup": "runs marked benchmark_role=warmup are excluded from all statistics",
        },
        "acceptance": {
            "minimum_runs_per_profile": MIN_RUNS_PER_PROFILE,
            "same_commit_required": True,
            "pinned_tool_versions_required": True,
            "same_trivy_database_snapshot_required": True,
            "same_commit": same_commit,
            "tool_versions_consistent": versions_match,
            "enough_repeats": enough_repeats,
            "trivy_database_snapshot_consistent": database_snapshots_match,
        },
        "profiles": profiles,
        "cache_comparison": delta,
        "excluded_runs": excluded,
        "limitations": [
            "Cache comparison covers pip package downloads for the test job, Semgrep, and Checkov; scanner binaries and Trivy vulnerability databases are not cached by this variable.",
            "GitHub-hosted runner hardware and external network conditions can vary between runs; report the observed spread.",
            "Wall time is the measured workflow job interval for the dispatch run; release and kind deploy-smoke are skipped on workflow_dispatch.",
            "A complete cache comparison requires one shared Trivy vulnerability DB snapshot across both profiles; repeat the study if the DB changes during collection.",
        ],
    }


def markdown(report):
    lines = [
        "# E3 – Thời gian CI theo cache profile",
        "",
        f"**Trạng thái bằng chứng:** `{report['evidence_status']}`",
        "",
        "| Cache pip | N hợp lệ | Wall median (s) | Wall IQR (s) | Wall p90 (s) | Scan stage median (s) | Scan runner-minutes median |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for mode in ("cold", "warm"):
        profile = report["profiles"][mode]
        wall = profile["workflow_wall_seconds"]
        scan = profile["scan_stage_wall_seconds"]
        minutes = profile["scan_stage_runner_minutes"]
        fmt = lambda value, suffix="": "chưa đo" if value is None else f"{value}{suffix}"
        lines.append(
            f"| {mode} | {profile['N']} | {fmt(wall['median'])} | {fmt(wall['iqr'])} | "
            f"{fmt(wall['p90'])} | {fmt(scan['median'])} | {fmt(minutes['median'])} |"
        )
    lines.extend(["", "## Thời gian từng job", "", "| Cache | Job | N | Median (s) | IQR (s) | p90 (s) |", "|---|---|---:|---:|---:|---:|"])
    for mode in ("cold", "warm"):
        for name, value in report["profiles"][mode]["per_job_seconds"].items():
            lines.append(f"| {mode} | {name} | {value['N']} | {value['median']} | {value['iqr']} | {value['p90']} |")
    comparison = report.get("cache_comparison")
    lines.extend(["", "## So sánh cache", ""])
    if comparison:
        lines.append(
            f"- Chênh lệch median wall warm − cold: **{comparison['warm_minus_cold_seconds']} giây** "
            f"({comparison['warm_change_percent']}%). {comparison['interpretation']}."
        )
    else:
        lines.append("Chưa đủ lượt đo ở cả hai profile để tính chênh lệch.")
    lines.extend(["", "## Điều kiện và giới hạn", ""])
    for item in report["limitations"]:
        lines.append(f"- {item}")
    if report["excluded_runs"]:
        lines.extend(["", f"Số run bị loại: **{len(report['excluded_runs'])}**."])
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-index", required=True, type=Path, help="run-index.json from run_fixture_matrix.py")
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        index = load_index(args.run_index)
        report = build_report(index, args.run_index)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        parser.error(str(error))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "e3_live_cache_comparison.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (args.out_dir / "e3_live_cache_comparison.md").write_text(markdown(report), encoding="utf-8")
    print(markdown(report))
    return 0 if report["evidence_status"] == "complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
