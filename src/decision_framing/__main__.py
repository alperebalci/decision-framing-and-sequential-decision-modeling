from __future__ import annotations

import argparse

from .audit import audit_frame
from .io import load_frame


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a decision-framing JSON file.")
    parser.add_argument("frame", help="Path to a framing JSON file")
    args = parser.parse_args()

    frame = load_frame(args.frame)
    report = audit_frame(frame)
    print(f"Problem: {frame.problem_name}")
    print(f"Metrics: {len(frame.metrics)} | Decisions: {len(frame.decisions)} | Uncertainties: {len(frame.uncertainties)}")
    if not report.findings:
        print("Framing audit: no findings")
        return 0
    for finding in report.findings:
        print(f"{finding.severity.upper():7} {finding.code}: {finding.message}")
    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
