from pathlib import Path


README_PATH = Path("README.md")


def replace_required(
    text: str,
    old: str,
    new: str,
    label: str,
) -> str:
    if old not in text:
        raise RuntimeError(
            f"README update failed: missing marker for {label}"
        )
    return text.replace(old, new, 1)


def main() -> None:
    if not README_PATH.exists():
        raise FileNotFoundError(
            "README.md not found. Run this script from "
            "the reqflow-agent project root."
        )

    text = README_PATH.read_text(
        encoding="utf-8",
    )

    text = replace_required(
        text,
        (
            "集成 LangGraph 工作流、LLM 工具规划、"
            "RAG 知识库、分析历史、缓存、异常降级、"
            "自动化测试和容器化部署。"
        ),
        (
            "集成 LangGraph 工作流、LLM 工具规划、"
            "RAG 知识库、Agent Evaluation、分析历史、"
            "缓存、异常降级、自动化测试和容器化部署。"
        ),
        "project summary",
    )

    text = replace_required(
        text,
        "系统围绕四条主线展开：",
        "系统围绕五条主线展开：",
        "main lines count",
    )

    text = replace_required(
        text,
        (
            "4. **RAG 知识库**：管理知识文档，自动完成"
            "文本分块、向量生成和语义检索，并将检索结果"
            "作为需求分析上下文。\n"
        ),
        (
            "4. **RAG 知识库**：管理知识文档，自动完成"
            "文本分块、向量生成和语义检索，并将检索结果"
            "作为需求分析上下文。\n"
            "5. **Agent Evaluation**：使用人工标注 JSONL "
            "数据集评估 Planner 工具选择，统计 Exact Match、"
            "Precision、Recall、失败案例和 LLM 降级次数。\n"
        ),
        "evaluation main line",
    )

    evaluation_feature_section = """### Agent Evaluation

- 使用 JSONL 保存人工标注的需求评测案例
- 评测时执行真实的 `execute_langgraph_analysis()` 链路
- 对比预期工具与 Planner 实际选择工具
- 统计 Exact Match、Precision、Recall、漏选工具和误选工具
- 聚合总案例数、失败案例 ID 和 LLM 降级次数
- 自动生成 JSON 与 Markdown 两种评测报告
- 当前提供 10 条 FakeLLM 确定性基线案例

> 当前 100% 结果仅表示 FakeLLM 在这 10 条规则型基线案例上的表现，不代表真实模型或生产环境准确率。

"""

    if "### Agent Evaluation\n" not in text:
        text = replace_required(
            text,
            "### 前端页面\n",
            evaluation_feature_section
            + "### 前端页面\n",
            "evaluation feature section",
        )

    text = text.replace(
        "当前共 **140 个自动化测试**",
        "当前共 **152 个自动化测试**",
    )
    text = text.replace(
        "140 passed, 1 warning",
        "152 passed, 1 warning",
    )
    text = text.replace(
        "- 140 个自动化测试",
        "- 152 个自动化测试",
    )

    text = replace_required(
        text,
        "- 余弦相似度检索\n",
        (
            "- 余弦相似度检索\n"
            "- JSONL 人工标注评测数据集\n"
            "- Exact Match / Precision / Recall\n"
            "- JSON / Markdown 评测报告\n"
        ),
        "evaluation tech stack",
    )

    text = replace_required(
        text,
        (
            "│   │   ├── analyzer.py\n"
            "│   │   ├── embeddings.py\n"
            "│   │   ├── langgraph_runtime.py\n"
        ),
        (
            "│   │   ├── analyzer.py\n"
            "│   │   ├── embeddings.py\n"
            "│   │   ├── evaluation.py\n"
            "│   │   ├── evaluation_report.py\n"
            "│   │   ├── langgraph_runtime.py\n"
        ),
        "evaluation project files",
    )

    text = replace_required(
        text,
        (
            "├── migrations/\n"
            "├── scripts/\n"
            "├── tests/\n"
        ),
        (
            "├── evals/\n"
            "├── migrations/\n"
            "├── reports/\n"
            "├── scripts/\n"
            "├── tests/\n"
        ),
        "evaluation project directories",
    )

    text = replace_required(
        text,
        (
            "- `app/agent/langgraph_runtime.py`：构建和执行 "
            "LangGraph 工作流。\n"
        ),
        (
            "- `app/agent/langgraph_runtime.py`：构建和执行 "
            "LangGraph 工作流。\n"
            "- `app/agent/evaluation.py`：定义单案例和批量"
            "工具选择评测指标。\n"
            "- `app/agent/evaluation_report.py`：读取 JSONL "
            "数据集并生成 JSON、Markdown 报告。\n"
        ),
        "evaluation directory responsibilities",
    )

    text = replace_required(
        text,
        (
            "- `tests`：保存单元测试、接口测试和持久化测试。\n"
        ),
        (
            "- `evals`：保存人工标注的 Agent Evaluation 数据集。\n"
            "- `reports`：保存可展示的评测结果。\n"
            "- `tests`：保存单元测试、接口测试、持久化测试和"
            "评测测试。\n"
        ),
        "evaluation directory list",
    )

    text = replace_required(
        text,
        (
            "- LangGraph Planner、Tool 和 Final Report 节点\n"
        ),
        (
            "- LangGraph Planner、Tool 和 Final Report 节点\n"
            "- Agent 工具选择 Exact Match、Precision、Recall\n"
            "- JSONL 评测数据读取、批量汇总和报告生成\n"
        ),
        "evaluation test coverage",
    )

    evaluation_run_section = """## Agent Evaluation

默认评测使用 FakeLLM，结果稳定、可重复，不调用真实模型接口。

运行 10 条人工标注基线案例：

```powershell
cd D:\\projects\\reqflow-agent
python scripts/run_agent_eval.py
```

当前基线结果：

```text
Total cases: 10
Exact match rate: 100.00%
Average precision: 100.00%
Average recall: 100.00%
LLM fallback count: 0
Failed case IDs: none
```

生成文件：

```text
reports/agent_eval_report.json
reports/agent_eval_report.md
```

评测链路：

```text
JSONL 人工标注案例
→ execute_langgraph_analysis()
→ 获取 Planner 实际工具
→ 对比预期工具
→ 计算 Exact Match / Precision / Recall
→ 输出失败案例和评测报告
```

该结果是 FakeLLM 规则基线，用于验证评测框架和回归能力；后续将扩充边界案例并增加真实 DeepSeek Planner 对比实验。

"""

    if "## Agent Evaluation\n" not in text:
        text = replace_required(
            text,
            "## 前端构建\n",
            evaluation_run_section
            + "## 前端构建\n",
            "evaluation usage section",
        )

    text = replace_required(
        text,
        (
            "- 使用 FakeLLM 保证测试稳定、可重复且不产生真实 "
            "API 费用。\n"
        ),
        (
            "- 使用 FakeLLM 保证测试稳定、可重复且不产生真实 "
            "API 费用。\n"
            "- 使用人工标注 JSONL 数据集量化评估 Planner 的"
            "工具选择，并输出可回归的失败案例。\n"
        ),
        "evaluation project highlight",
    )

    text = replace_required(
        text,
        "- GitHub Actions 完整 CI\n",
        (
            "- GitHub Actions 完整 CI\n"
            "- Agent Evaluation 数据集、聚合指标与报告生成\n"
        ),
        "evaluation current status",
    )

    README_PATH.write_text(
        text,
        encoding="utf-8",
    )

    print("README.md updated successfully.")


if __name__ == "__main__":
    main()
