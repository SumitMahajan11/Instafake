import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any

# Ensure app module can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models import Claim, SiteFact
from app.checker import verify_single_claim

BENCHMARK_FILE = Path(__file__).parent / "benchmark_cases.json"
ACCURACY_THRESHOLD = 80.0  # Minimum required overall accuracy percentage for CI gate

VERDICTS = ["confirmed", "contradicted", "partial", "not_found"]


def run_benchmark():
    if not BENCHMARK_FILE.exists():
        print(f"Error: Benchmark cases file not found at {BENCHMARK_FILE}")
        sys.exit(1)

    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        cases = json.load(f)

    total_cases = len(cases)
    print(f"==========================================================================")
    print(f" REELCLAIM PHASE 3 VERIFICATION PIPELINE BENCHMARK")
    print(f" Loaded {total_cases} labeled test cases from {BENCHMARK_FILE.name}")
    print(f"==========================================================================\n")

    start_time = time.time()
    results = []
    correct_count = 0

    # Metrics accumulators per category
    tp = {v: 0 for v in VERDICTS}
    fp = {v: 0 for v in VERDICTS}
    fn = {v: 0 for v in VERDICTS}
    gt_count = {v: 0 for v in VERDICTS}
    pred_count = {v: 0 for v in VERDICTS}

    for idx, case in enumerate(cases, 1):
        case_id = case["id"]
        expected = case["expected_verdict"]
        gt_count[expected] += 1

        claim = Claim(**case["claim"])
        site_facts = [SiteFact(**f) for f in case["site_facts"]]

        # Run Phase 3 verification with automatic 429 rate-limit backoff retry
        verdict_obj = None
        max_retries = 5
        for retry in range(max_retries):
            verdict_obj = verify_single_claim(claim, site_facts)
            if verdict_obj.reasoning and "Verification service unavailable" in verdict_obj.reasoning and "429" in verdict_obj.reasoning:
                print(f"   [Rate Limit 429 hit on {case_id}] Pausing 15s before retry ({retry + 1}/{max_retries})...")
                time.sleep(15.0)
            else:
                break

        predicted = verdict_obj.verdict
        pred_count[predicted] = pred_count.get(predicted, 0) + 1

        is_correct = (predicted == expected)
        if is_correct:
            correct_count += 1
            tp[expected] += 1
        else:
            fp[predicted] = fp.get(predicted, 0) + 1
            fn[expected] += 1

        results.append({
            "id": case_id,
            "claim_text": claim.text,
            "expected": expected,
            "predicted": predicted,
            "is_correct": is_correct,
            "reasoning": verdict_obj.reasoning,
            "evidence_text": verdict_obj.evidence_text
        })

        status_symbol = "PASS" if is_correct else "FAIL"
        print(f"[{idx:02d}/{total_cases}] {case_id} | Expected: {expected:12s} | Pred: {predicted:12s} | [{status_symbol}]")

        # Pacing: 4 seconds pause per request to stay under Gemini free tier limit (15 RPM)
        time.sleep(4.1)

    elapsed_time = time.time() - start_time
    overall_accuracy = (correct_count / total_cases) * 100.0

    print(f"\n==========================================================================")
    print(f" BENCHMARK RESULTS SUMMARY (Time: {elapsed_time:.1f}s)")
    print(f"==========================================================================\n")

    print(f"{'Category':<15} | {'GT Count':<8} | {'Pred Count':<10} | {'TP':<4} | {'FP':<4} | {'FN':<4} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10}")
    print("-" * 95)

    category_metrics = {}
    macro_f1_sum = 0.0

    for v in VERDICTS:
        c_tp = tp[v]
        c_fp = fp[v]
        c_fn = fn[v]

        precision = (c_tp / (c_tp + c_fp)) * 100.0 if (c_tp + c_fp) > 0 else 0.0
        recall = (c_tp / (c_tp + c_fn)) * 100.0 if (c_tp + c_fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        macro_f1_sum += f1
        category_metrics[v] = {
            "gt": gt_count[v],
            "pred": pred_count.get(v, 0),
            "tp": c_tp,
            "fp": c_fp,
            "fn": c_fn,
            "precision": precision,
            "recall": recall,
            "f1": f1
        }

        print(f"{v:<15} | {gt_count[v]:<8} | {pred_count.get(v, 0):<10} | {c_tp:<4} | {c_fp:<4} | {c_fn:<4} | {precision:8.2f}% | {recall:8.2f}% | {f1:8.2f}%")

    macro_f1 = macro_f1_sum / len(VERDICTS)
    print("-" * 95)
    print(f"{'OVERALL':<15} | {total_cases:<8} | {total_cases:<10} | {correct_count:<4} | {total_cases - correct_count:<4} | {total_cases - correct_count:<4} | {overall_accuracy:8.2f}% | {overall_accuracy:8.2f}% | {macro_f1:8.2f}% (Macro)")

    print(f"\n==========================================================================")
    print(f" OVERALL ACCURACY: {overall_accuracy:.2f}% ({correct_count}/{total_cases})")
    print(f" MACRO F1 SCORE  : {macro_f1:.2f}%")
    print(f" TARGET THRESHOLD: {ACCURACY_THRESHOLD:.2f}%")
    print(f"==========================================================================\n")

    # Print failures list if any exist
    failures = [r for r in results if not r["is_correct"]]
    if failures:
        print("MISCLASSIFIED CASES:")
        print("--------------------")
        for f in failures:
            print(f"Case ID  : {f['id']}")
            print(f"Claim    : \"{f['claim_text']}\"")
            print(f"Expected : {f['expected']}")
            print(f"Predicted: {f['predicted']}")
            print(f"Reasoning: {f['reasoning']}")
            print("-" * 50)

    if overall_accuracy < ACCURACY_THRESHOLD:
        print(f"\n[FAIL]: Overall accuracy ({overall_accuracy:.2f}%) is below target threshold ({ACCURACY_THRESHOLD:.2f}%).")
        sys.exit(1)
    else:
        print(f"\n[PASS]: Overall accuracy ({overall_accuracy:.2f}%) meets or exceeds target threshold ({ACCURACY_THRESHOLD:.2f}%).")
        sys.exit(0)


if __name__ == "__main__":
    run_benchmark()
