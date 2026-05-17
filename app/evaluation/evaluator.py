"""RAG 评估模块

使用 Ragas 框架评估检索和生成质量，支持以下指标：
- Faithfulness：生成内容忠实于检索上下文
- Answer Relevancy：回答与问题相关性
- Context Recall：检索上下文召回率
- Context Precision：检索上下文精确率
"""
from typing import List, Dict


class RAGEvaluator:
    """RAG 质量评估"""

    async def evaluate(
        self,
        questions: List[str],
        answers: List[str],
        contexts: List[List[str]],
        ground_truths: List[str] = None,
    ) -> Dict:
        """执行完整评估"""
        from app.config import settings
        if not settings.LLM_API_KEY:
            return self._placeholder_result(len(questions))

        from ragas import evaluate
        from ragas.metrics import (
            faithfulness,
            answer_relevancy,
            context_recall,
            context_precision,
        )
        from datasets import Dataset

        data = {
            "question": questions,
            "answer": answers,
            "contexts": contexts,
        }
        if ground_truths:
            data["ground_truth"] = ground_truths

        dataset = Dataset.from_dict(data)
        result = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
        )
        return result.to_pandas().to_dict(orient="records")

    def _placeholder_result(self, count: int) -> Dict:
        return {
            "status": "skipped",
            "reason": "LLM_API_KEY 未配置，跳过 Ragas 评估",
            "sample_count": count,
        }

    async def evaluate_single(
        self, question: str, answer: str, contexts: List[str]
    ) -> Dict:
        """评估单条问答"""
        results = await self.evaluate([question], [answer], [contexts])
        return results
