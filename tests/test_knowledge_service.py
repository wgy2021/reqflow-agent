import pytest

from app.services.knowledge import (
    normalize_text,
    split_text,
)


def test_normalize_text_removes_blank_lines() -> None:
    text = """
        第一段内容

        第二段内容
    """

    result = normalize_text(text)

    assert result == "第一段内容\n第二段内容"


def test_split_short_text_returns_one_chunk() -> None:
    result = split_text(
        "这是一段较短的知识库内容。",
        chunk_size=100,
        overlap=10,
    )

    assert result == [
        "这是一段较短的知识库内容。",
    ]


def test_split_text_keeps_overlap() -> None:
    result = split_text(
        "ABCDEFGHIJ",
        chunk_size=6,
        overlap=2,
    )

    assert result == [
        "ABCDEF",
        "EFGHIJ",
    ]


def test_split_text_rejects_invalid_parameters() -> None:
    with pytest.raises(
        ValueError,
        match="chunk_size",
    ):
        split_text(
            "测试内容",
            chunk_size=0,
        )

    with pytest.raises(
        ValueError,
        match="overlap",
    ):
        split_text(
            "测试内容",
            chunk_size=10,
            overlap=10,
        )