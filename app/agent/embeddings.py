"""文本向量生成与相似度计算。"""

import hashlib
import math
import re
from abc import ABC, abstractmethod


DEFAULT_EMBEDDING_DIMENSION = 256


class EmbeddingClient(ABC):
    """Embedding 客户端统一接口。"""

    @abstractmethod
    def embed_texts(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """将多段文本转换为向量。"""


class LocalHashEmbeddingClient(EmbeddingClient):
    """本地字符 n-gram 哈希向量客户端。

    不调用外部 API，适合开发、测试和降级场景。
    """

    def __init__(
        self,
        dimension: int = DEFAULT_EMBEDDING_DIMENSION,
    ) -> None:
        if dimension <= 0:
            raise ValueError("dimension 必须大于 0")

        self.dimension = dimension

    def embed_texts(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        return [
            self._embed_text(text)
            for text in texts
        ]

    def _embed_text(
        self,
        text: str,
    ) -> list[float]:
        vector = [
            0.0
            for _ in range(self.dimension)
        ]

        tokens = self._tokenize(text)

        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.sha256(
                token.encode("utf-8")
            ).digest()

            index = int.from_bytes(
                digest[:4],
                byteorder="big",
            ) % self.dimension

            sign = (
                1.0
                if digest[4] % 2 == 0
                else -1.0
            )

            vector[index] += sign

        return normalize_vector(vector)

    @staticmethod
    def _tokenize(
        text: str,
    ) -> list[str]:
        normalized = re.sub(
            r"[^\w\u4e00-\u9fff]+",
            "",
            text.lower(),
        )

        if not normalized:
            return []

        tokens: list[str] = []

        for ngram_size in (1, 2, 3):
            if len(normalized) < ngram_size:
                continue

            for index in range(
                len(normalized) - ngram_size + 1
            ):
                tokens.append(
                    normalized[
                        index:index + ngram_size
                    ]
                )

        return tokens


def normalize_vector(
    vector: list[float],
) -> list[float]:
    """把向量转换为单位向量。"""

    magnitude = math.sqrt(
        sum(
            value * value
            for value in vector
        )
    )

    if magnitude == 0:
        return vector.copy()

    return [
        value / magnitude
        for value in vector
    ]


def cosine_similarity(
    left: list[float],
    right: list[float],
) -> float:
    """计算两个向量的余弦相似度。"""

    if len(left) != len(right):
        raise ValueError("向量维度必须一致")

    left_magnitude = math.sqrt(
        sum(
            value * value
            for value in left
        )
    )

    right_magnitude = math.sqrt(
        sum(
            value * value
            for value in right
        )
    )

    if (
        left_magnitude == 0
        or right_magnitude == 0
    ):
        return 0.0

    dot_product = sum(
        left_value * right_value
        for left_value, right_value in zip(
            left,
            right,
            strict=True,
        )
    )

    return dot_product / (
        left_magnitude * right_magnitude
    )
