import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

from app.agent.evaluation_report import (  # noqa: E402
    run_evaluation_dataset,
)


def parse_args() -> argparse.Namespace:
    """解析评测命令行参数。"""

    parser = argparse.ArgumentParser(
        description=(
            "Run ReqFlow Agent evaluation dataset"
        ),
    )

    parser.add_argument(
        "--dataset",
        type=Path,
        default=(
            PROJECT_ROOT
            / "evals"
            / "requirement_cases.jsonl"
        ),
    )
    parser.add_argument(
        "--json-report",
        type=Path,
        default=(
            PROJECT_ROOT
            / "reports"
            / "agent_eval_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-report",
        type=Path,
        default=(
            PROJECT_ROOT
            / "reports"
            / "agent_eval_report.md"
        ),
    )

    return parser.parse_args()


def main() -> None:
    """运行评测并输出核心指标。"""

    args = parse_args()

    summary = run_evaluation_dataset(
        dataset_path=args.dataset,
        json_report_path=args.json_report,
        markdown_report_path=(
            args.markdown_report
        ),
    )

    print("Agent evaluation completed")
    print(f"Total cases: {summary.total_cases}")
    print(
        "Exact match rate: "
        f"{summary.exact_match_rate:.2%}"
    )
    print(
        "Average precision: "
        f"{summary.average_precision:.2%}"
    )
    print(
        "Average recall: "
        f"{summary.average_recall:.2%}"
    )
    print(
        "LLM fallback count: "
        f"{summary.fallback_count}"
    )
    print(
        "Failed case IDs: "
        + (
            ", ".join(summary.failed_case_ids)
            if summary.failed_case_ids
            else "none"
        )
    )
    print(f"JSON report: {args.json_report}")
    print(
        "Markdown report: "
        f"{args.markdown_report}"
    )


if __name__ == "__main__":
    main()
