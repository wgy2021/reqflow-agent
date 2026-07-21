import math

import pytest

from app.agent.embeddings import (
    LocalHashEmbeddingClient,
    cosine_similarity,
)


def test_embedding_has_expected_dimension() -> None:
    client = LocalHashEmbeddingClient(
        dimension=64,
    )

    embedding = client.embed_texts(
        [
            "用户登录安全规范",
        ]
    )[0]

    assert len(embedding) == 64
    assert math.sqrt(
        sum(
            value * value
            for value in embedding
        )
    ) == pytest.approx(1.0)


def test_same_text_has_identical_embedding() -> None:
    client = LocalHashEmbeddingClient()

    first, second = client.embed_texts(
        [
            "密码必须使用哈希算法保存",
            "密码必须使用哈希算法保存",
        ]
    )

    assert first == second
    assert cosine_similarity(
        first,
        second,
    ) == pytest.approx(1.0)


def test_similar_text_scores_higher() -> None:
    client = LocalHashEmbeddingClient()

    query, related, unrelated = client.embed_texts(
        [
            "用户登录需要密码安全校验",
            "登录接口必须校验用户名和密码",
            "商品库存不足时发送补货提醒",
        ]
    )

    related_score = cosine_similarity(
        query,
        related,
    )

    unrelated_score = cosine_similarity(
        query,
        unrelated,
    )

    assert related_score > unrelated_score


def test_empty_text_returns_zero_vector() -> None:
    client = LocalHashEmbeddingClient(
        dimension=32,
    )

    embedding = client.embed_texts(
        [
            "   ",
        ]
    )[0]

    assert embedding == [
        0.0
        for _ in range(32)
    ]


def test_cosine_similarity_rejects_different_dimensions() -> None:
    with pytest.raises(
        ValueError,
        match="维度",
    ):
        cosine_similarity(
            [1.0, 0.0],
            [1.0],
        )