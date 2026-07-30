import json
from pathlib import Path

from pydantic import ValidationError

from app.agent.evaluation import (
    RequirementEvaluationCase,
    RequirementEvaluationSummary,
    evaluate_requirement_cases,
)
from app.agent.llm import LLMClient


def load_evaluation_cases(
    dataset_path: Path,
) -> list[RequirementEvaluationCase]:
    """从 JSONL 文件读取人工标注的评测案例。"""

    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Evaluation dataset not found: "
            f"{dataset_path}"
        )

    cases: list[RequirementEvaluationCase] = []

    with dataset_path.open(
        "r",
        encoding="utf-8",
    ) as dataset_file:
        for line_number, raw_line in enumerate(
            dataset_file,
            start=1,
        ):
            line = raw_line.strip()

            if not line:
                continue

            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    "Invalid JSON in evaluation dataset "
                    f"at line {line_number}"
                ) from exc

            try:
                case = (
                    RequirementEvaluationCase
                    .model_validate(payload)
                )
            except ValidationError as exc:
                raise ValueError(
                    "Invalid evaluation case "
                    f"at line {line_number}"
                ) from exc

            cases.append(case)

    if not cases:
        raise ValueError(
            "Evaluation dataset is empty"
        )

    return cases


def build_markdown_report(
    summary: RequirementEvaluationSummary,
) -> str:
    """将聚合指标转换为便于阅读的 Markdown。"""

    failed_case_text = (
        ", ".join(summary.failed_case_ids)
        if summary.failed_case_ids
        else "无"
    )

    return (
        "# ReqFlow Agent Evaluation Report\n\n"
        "## Summary\n\n"
        f"- Total cases: {summary.total_cases}\n"
        "- Tool selection exact matches: "
        f"{summary.exact_match_count}\n"
        "- Exact match rate: "
        f"{summary.exact_match_rate:.2%}\n"
        "- Average precision: "
        f"{summary.average_precision:.2%}\n"
        "- Average recall: "
        f"{summary.average_recall:.2%}\n"
        f"- LLM fallback count: "
        f"{summary.fallback_count}\n"
        f"- Failed case IDs: "
        f"{failed_case_text}\n"
    )


def write_evaluation_report(
    *,
    summary: RequirementEvaluationSummary,
    json_report_path: Path,
    markdown_report_path: Path,
) -> None:
    """写入 JSON 和 Markdown 两种评测报告。"""

    json_report_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    markdown_report_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_report_path.write_text(
        json.dumps(
            summary.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    markdown_report_path.write_text(
        build_markdown_report(summary),
        encoding="utf-8",
    )


def run_evaluation_dataset(
    *,
    dataset_path: Path,
    json_report_path: Path,
    markdown_report_path: Path,
    llm_client: LLMClient | None = None,
) -> RequirementEvaluationSummary:
    """运行完整 JSONL 数据集并生成评测报告。"""

    cases = load_evaluation_cases(
        dataset_path
    )

    summary = evaluate_requirement_cases(
        cases=cases,
        llm_client=llm_client,
    )

    write_evaluation_report(
        summary=summary,
        json_report_path=json_report_path,
        markdown_report_path=(
            markdown_report_path
        ),
    )

    return summary
