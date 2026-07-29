from pathlib import Path

import yaml

from app.rag.search import search_docs


TEST_FILE = Path("app/rag/test_questions.yaml")


def evaluate():

    tests = yaml.safe_load(TEST_FILE.read_text())

    hit1 = 0
    hit3 = 0
    hit5 = 0

    total = len(tests)

    for test in tests:

        results = search_docs(test["question"], top_k=5)

        sources = [r["source"] for r in results]

        expected = test["expect_source"]

        if len(sources) >= 1 and sources[0] == expected:
            hit1 += 1

        if expected in sources[:3]:
            hit3 += 1

        if expected in sources:
            hit5 += 1

    print(f"Total Questions : {total}")
    print(f"Hit@1 : {hit1}/{total}")
    print(f"Hit@3 : {hit3}/{total}")
    print(f"Hit@5 : {hit5}/{total}")


if __name__ == "__main__":
    evaluate()