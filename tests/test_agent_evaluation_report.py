import json
from pathlib import Path

import pytest

from app.agent.evaluation_report import (
    load_evaluation_cases,
    run_evaluation_dataset,
)


def test_load_evaluation_cases_reads_jsonl(
    tmp_path: Path,
) -> None:
    dataset_path = tmp_path / "cases.jsonl"

    dataset_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "case_id": "case-001",
                        "title": "修改按钮文案",
                        "content": (
                            "将首页按钮文字修改为提交"
                        ),
                        "priority": 3,
                        "expected_tools": [
                            "completeness_check"
                        ],
                    },
                    ensure_ascii=False,
                ),
                "",
                json.dumps(
                    {
                        "case_id": "case-002",
                        "title": "提示信息优化",
                        "content": (
                            "系统应尽快返回提示信息"
                        ),
                        "priority": 3,
                        "expected_tools": [
                            "completeness_check",
                            "ambiguity_check",
                        ],
                    },
                    ensure_ascii=False,
                ),
            ]
        ),
        encoding="utf-8",
    )

    cases = load_evaluation_cases(
        dataset_path
    )

    assert len(cases) == 2
    assert cases[0].case_id == "case-001"
    assert cases[1].case_id == "case-002"


def test_load_evaluation_cases_reports_line_number(
    tmp_path: Path,
) -> None:
    dataset_path = tmp_path / "invalid.jsonl"

    valid_first_line = json.dumps(
        {
            "case_id": "case-001",
            "title": "修改按钮文案",
            "content": "将首页按钮文字修改为提交",
            "priority": 3,
            "expected_tools": [
                "completeness_check"
            ],
        },
        ensure_ascii=False,
    )

    dataset_path.write_text(
        valid_first_line
        + "\n"
        + '{"case_id":',
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="line 2",
    ):
        load_evaluation_cases(
            dataset_path
        )


def test_run_evaluation_dataset_writes_reports(
    tmp_path: Path,
) -> None:
    dataset_path = tmp_path / "cases.jsonl"
    json_report_path = (
        tmp_path / "reports" / "report.json"
    )
    markdown_report_path = (
        tmp_path / "reports" / "report.md"
    )

    dataset_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "case_id": "plain-001",
                        "title": "修改按钮文案",
                        "content": (
                            "将首页按钮文字修改为提交"
                        ),
                        "priority": 3,
                        "expected_tools": [
                            "completeness_check"
                        ],
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "case_id": "security-001",
                        "title": "登录安全校验",
                        "content": (
                            "用户登录时必须校验密码"
                        ),
                        "priority": 1,
                        "expected_tools": [
                            "completeness_check",
                            "priority_suggestion",
                        ],
                    },
                    ensure_ascii=False,
                ),
            ]
        ),
        encoding="utf-8",
    )

    summary = run_evaluation_dataset(
        dataset_path=dataset_path,
        json_report_path=json_report_path,
        markdown_report_path=(
            markdown_report_path
        ),
    )

    assert summary.total_cases == 2
    assert summary.exact_match_rate == 1.0
    assert summary.average_precision == 1.0
    assert summary.average_recall == 1.0

    assert json_report_path.exists()
    assert markdown_report_path.exists()

    json_report = json.loads(
        json_report_path.read_text(
            encoding="utf-8",
        )
    )

    assert json_report["total_cases"] == 2
    assert (
        json_report["failed_case_ids"]
        == []
    )

    markdown_report = (
        markdown_report_path.read_text(
            encoding="utf-8",
        )
    )

    assert "Exact match rate: 100.00%" in (
        markdown_report
    )
