import subprocess
import time

import numpy as np

from app.ollama_client import call_ollama
from app.ollama_errors import (
    OllamaClientError,
    OllamaInvalidJSONError,
    OllamaModelNotFoundError,
    OllamaTimeoutError,
    OllamaUnreachableError,
)

vram_log = "vram_log.csv"

PROMPTS = [
    "What is the capital of Japan?",
    "Who wrote Romeo and Juliet?",
    "What is the tallest mountain in the world?",
    "In what year did World War II end?",
    "What is 15% of 200?",
    "If a train travels 60 km/s for 2.5 hours, how far does it go?",
    "What is the square root of 144?",
    "How many days are there in a leap year?",
    "What is photosynthesis?",
    "Explain what an API is in simple terms.",
    "What causes seasons to change?",
    "What is the difference between weather and climate?",
    "How do I boil an egg?",
    "What's the best way to remove a red wine stain?",
    "How do I back up files on a computer?",
    "What are some tips for staying focused while studying?",
    "What's a good book for a beginner programmer?",
    "Should I learn Python or JavaScript first?",
    "What's a healthy breakfast option?",
    "What's the best way to learn a new language?",
]

latencies = []
success = 0
failure = 0

if __name__ == "__main__":
    with open(vram_log, "w") as f:
        vram_process = subprocess.Popen(
             ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits", "-l", "1"],
        stdout=f,
        )

    for prompt in PROMPTS:
        for _repeat in range(10): # _repeat underscore to match ruff's condition
            start = time.perf_counter()
            try:
                result = call_ollama([("human", prompt)])
                latencies.append(time.perf_counter() - start)
                success += 1
                print(f"[{success + failure}/200] Success for prompt: {prompt}")
            except OllamaInvalidJSONError as e:
                print(f"[{success + failure}/200] Invalid JSON for '{prompt}': {e}")
                latencies.append(time.perf_counter() - start)
                failure += 1
            except OllamaTimeoutError as e:
                print(f"[{success + failure}/200] Timeout for '{prompt}': {e}")
                latencies.append(time.perf_counter() - start)
                failure += 1
            except OllamaUnreachableError as e:
                print(f"Ollama unreachable, stopping: {e}")
                raise
            except OllamaModelNotFoundError as e:
                print(f"Model not found, stopping: {e}")
                raise
            except OllamaClientError as e:
                print(f"Unexpected Ollama error, stopping: {e}")
                raise

            vram_process.terminate()
            vram_process.wait()

            with open(vram_log) as f:
                vram_readings = [int(line.strip()) for line in f if line.strip()]

                if vram_readings:
                    print(f"Peak VRAM: {max(vram_readings)} MiB")
                    print(f"Average VRAM: {sum(vram_readings) / len(vram_readings):.1f} MiB")
                else:
                    print("No VRAM readings recorded.")

    print(f"\nDone. Success: {success}, Failure: {failure}, Total: {success + failure}")

    if success + failure > 0:
        valid_json_rate = success / (success + failure)
        print(f"Valid JSON Rate: {valid_json_rate:.1%}")
    else:
        print("No requests were made, cannot calculate valid JSON rate.")

    p95 = np.percentile(latencies, 95)
    print(f"P95 Latency: {p95:.4f} seconds")