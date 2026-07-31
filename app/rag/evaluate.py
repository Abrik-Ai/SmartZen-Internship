from pathlib import Path

import yaml

from app.rag.search import search_docs

TEST_FILE = Path("app/rag/test_questions.yaml")


def evaluate() -> None:

    tests = yaml.safe_load(TEST_FILE.read_text())

    hit1 = 0
    hit3 = 0
    hit5 = 0

    total = len(tests)

    for test in tests:

        results = search_docs(test["question"], top_k=5)

        expected_source = test["expect_source"]
        expected_contains = test["expect_contains"]

        matches = [
            r["source"] == expected_source
            and expected_contains.lower() in r["content"].lower()
            for r in results
        ]

        if len(matches) >= 1 and matches[0]:
            hit1 += 1

        if any(matches[:3]):
            hit3 += 1

        if any(matches[:5]):
            hit5 += 1

    print(f"Total Questions : {total}")
    print(f"Hit@1 : {hit1}/{total}")
    print(f"Hit@3 : {hit3}/{total}")
    print(f"Hit@5 : {hit5}/{total}")


if __name__ == "__main__":
    evaluate()