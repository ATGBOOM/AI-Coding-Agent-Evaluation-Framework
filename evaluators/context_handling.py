import re
from typing import Dict, Any, List, Tuple

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from utils.retrieval import keyword_retrieve
from utils.context_tasks import ContextTask

from models.llm_response import ContextAnswer


def _normalise(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s\./_-]", "", text)  # remove most punctuation
    text = re.sub(r"\s+", " ", text)
    return text


class ContextHandlingEvaluator:
    """
    Measures:
      - Retrieval quality: recall@k (did we retrieve the gold files?)
      - Utilisation quality: answer accuracy (did the model answer correctly using context?)
    """

    def __init__(self, llm):
        self.llm = llm

    def evaluate(self, task: ContextTask, top_k: int = 3) -> Dict[str, Any]:
        # 1) retrieval
        file_pairs: List[Tuple[str, str]] = [(f.path, f.content) for f in task.files]
        retrieved = keyword_retrieve(task.question, file_pairs, top_k=top_k)
        retrieved_paths = [p for p, _ in retrieved]

        gold = set(task.gold_files)
        hit = sum(1 for p in retrieved_paths if p in gold)
        recall_at_k = hit / max(1, len(gold))

        # 2) build prompt (only retrieved context is shown to the model)
        context_block = "\n\n".join(
            [f"### FILE: {p}\n```python\n{c}\n```" for p, c in retrieved]
        )

        parser = PydanticOutputParser(pydantic_object=ContextAnswer)
        format_instructions = parser.get_format_instructions()

        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You answer questions using ONLY the provided file context. "
             "If the context is insufficient, say 'INSUFFICIENT_CONTEXT'. "
             "Keep the answer short and direct."),
            ("user",
             "Here is the available context:\n\n{context}\n\n"
             "Question: {question}\n\n"
             "{format_instructions}")
        ])

        chain = prompt | self.llm | parser
        result = chain.invoke({
            "context": context_block,
            "question": task.question,
            "format_instructions": format_instructions
        })

        model_answer = result.answer

        # 3) utilisation (answer correctness)
        expected = _normalise(task.expected_answer)
        got = _normalise(model_answer)
        answer_correct = 1.0 if (expected in got or got in expected) else 0.0

        # 4) combined score (simple average for MVP)
        context_score = (recall_at_k + answer_correct) / 2.0

        return {
            "task_id": task.id,
            "task_title": task.title,
            "top_k": top_k,
            "retrieved_files": retrieved_paths,
            "gold_files": task.gold_files,
            "retrieval_recall_at_k": recall_at_k,
            "model_answer": model_answer,
            "expected_answer": task.expected_answer,
            "answer_accuracy": answer_correct,
            "context_handling_score": context_score
        }
