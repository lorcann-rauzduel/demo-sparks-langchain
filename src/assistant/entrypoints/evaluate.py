"""Évaluer l'assistant dans LangSmith : uv run --env-file .env assistant-evaluate

Le dataset est créé une seule fois depuis evaluation/cases.json ; chaque lancement devient une expérience,
comparable aux précédentes dans LangSmith.
"""

import json
import os
from itertools import count
from pathlib import Path
from typing import Any

from langsmith import Client

from assistant.bootstrap import build_assistant
from assistant.domain.answer import ActionToApprove

DEFAULT_CASES_FILE = "evaluation/cases.json"
DEFAULT_DATASET = "company-assistant"


def contains_expected(outputs: dict[str, Any], reference_outputs: dict[str, Any]) -> bool:
    """L'évaluateur : la réponse contient le texte attendu, sans tenir compte de la casse."""
    return str(reference_outputs["expected"]).lower() in str(outputs["answer"]).lower()


def main() -> None:
    assistant = build_assistant(os.environ)
    client = Client()
    dataset = os.environ.get("EVALUATION_DATASET", DEFAULT_DATASET)

    if not client.has_dataset(dataset_name=dataset):
        cases = json.loads(Path(os.environ.get("EVALUATION_CASES", DEFAULT_CASES_FILE)).read_text("utf-8"))
        created = client.create_dataset(dataset_name=dataset)
        client.create_examples(
            dataset_id=created.id,
            examples=[
                {"inputs": {"question": c["question"]}, "outputs": {"expected": c["expected"]}} for c in cases
            ],
        )

    # Un utilisateur neuf par cas : aucune conversation ni mémoire ne passe d'un cas à l'autre
    case_numbers = count(1)

    def target(inputs: dict[str, Any]) -> dict[str, str]:
        result = assistant.answer(f"evaluation:{next(case_numbers)}", inputs["question"])
        if isinstance(result, ActionToApprove):
            return {"answer": "; ".join(result.actions)}
        return {"answer": result.text}

    # Un évaluateur qui renvoie un booléen est accepté par LangSmith, que ses annotations de type ignorent
    evaluators: list[Any] = [contains_expected]
    results = client.evaluate(target, data=dataset, evaluators=evaluators, experiment_prefix=dataset)
    print(f"Expérience : {results.experiment_name}")


if __name__ == "__main__":
    main()
