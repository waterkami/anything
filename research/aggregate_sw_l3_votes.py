#!/usr/bin/env python3
"""Aggregate subagent vote CSVs against data/sw_l3_master.csv."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path


def load_master(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def validate_vote_rows(master: list[dict[str, str]], rows: list[dict[str, str]], src: Path) -> None:
    if len(rows) != len(master):
        raise ValueError(f"{src}: expected {len(master)} rows, got {len(rows)}")
    for i, (m, r) in enumerate(zip(master, rows, strict=True)):
        if r.get("idx", "") != str(m["idx"]):
            raise ValueError(f"{src}: idx mismatch at line {i}: master={m['idx']} vote={r.get('idx')}")
        if (r.get("行业代码") or "") != m["行业代码"]:
            raise ValueError(f"{src}: 行业代码 mismatch at idx {m['idx']}")
        if (r.get("行业名称") or "") != m["行业名称"]:
            raise ValueError(f"{src}: 行业名称 mismatch at idx {m['idx']}")
        v = r.get("vote", "")
        if v not in ("0", "1"):
            raise ValueError(f"{src}: invalid vote {v!r} at idx {m['idx']}")


def read_vote_file(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--master",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data" / "sw_l3_master.csv",
    )
    p.add_argument(
        "--votes-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "votes",
        help="Directory containing vote CSV files (*.csv)",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent / "votes" / "aggregated_vote_sums.csv",
    )
    args = p.parse_args()

    master = load_master(args.master)
    sums: dict[str, int] = defaultdict(int)

    vote_files = sorted(args.votes_dir.glob("*.csv"))
    vote_files = [p for p in vote_files if p.name != "aggregated_vote_sums.csv"]
    if not vote_files:
        print(f"No CSV files in {args.votes_dir}", file=sys.stderr)
        return 1

    for vf in vote_files:
        rows = read_vote_file(vf)
        validate_vote_rows(master, rows, vf)
        for r in rows:
            code = r["行业代码"]
            sums[code] += int(r["vote"])

    agent_count = len(vote_files)

    ranked = sorted(master, key=lambda m: (-sums[m["行业代码"]], m["行业代码"]))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["行业代码", "行业名称", "vote_sum", "agent_count"])
        for m in ranked:
            code = m["行业代码"]
            w.writerow([code, m["行业名称"], sums[code], agent_count])

    print(f"Wrote {args.out} from {agent_count} agent file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
