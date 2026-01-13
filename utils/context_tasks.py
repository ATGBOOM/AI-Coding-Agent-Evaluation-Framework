import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any


@dataclass
class ContextTaskFile:
    path: str
    content: str


@dataclass
class ContextTask:
    id: str
    title: str
    question: str
    expected_answer: str
    gold_files: List[str]
    files: List[ContextTaskFile]


def load_context_tasks() -> List[ContextTask]:
    """
    Loads context-handling tasks from datasets/context_tasks.json.

    This dataset is intentionally small and self-contained (files included inline)
    so we can test retrieval + utilisation without cloning real repos yet.
    """
    dataset_path = Path(__file__).resolve().parents[1] / "datasets" / "context_tasks.json"
    raw = json.loads(dataset_path.read_text(encoding="utf-8"))

    tasks: List[ContextTask] = []
    for item in raw:
        files = [ContextTaskFile(**f) for f in item["files"]]
        tasks.append(
            ContextTask(
                id=item["id"],
                title=item["title"],
                question=item["question"],
                expected_answer=item["expected_answer"],
                gold_files=item["gold_files"],
                files=files,
            )
        )
    return tasks
