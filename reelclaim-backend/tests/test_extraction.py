import sys
import os
import json
from pathlib import Path

# Ensure UTF-8 output encoding for Windows terminal
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root directory to python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.extraction import extract_claims

# 5 Realistic Test Cases as specified in prompt requirements:
TEST_CASES = [
    {
        "id": 1,
        "name": "Internship Reel Caption",
        "caption": (
            "🔥 FREE 3-Month AI/ML Internship Opportunity! "
            "Get official Google AI training and a verified certificate of completion. "
            "No prior coding experience required! Open to all college students. "
            "Deadline to register: August 31st. "
            "Apply now at https://google.com/careers"
        )
    },
    {
        "id": 2,
        "name": "Work-From-Home Job Reel Caption",
        "caption": (
            "🚀 Urgent Hiring: Work From Home Data Entry Specialist! "
            "Earn $50/hour with flexible working hours. "
            "No degree required. Full training provided for beginners. "
            "Limited seats available! Check the link in bio or visit bit.ly/wfh-jobs"
        )
    },
    {
        "id": 3,
        "name": "Paid Course Claiming to be Free Reel Caption",
        "caption": (
            "🎓 100% FREE Full-Stack Web Development Bootcamp! "
            "Learn React, Node.js & MongoDB with industry experts. "
            "Includes verified completion certificate & job placement assistance. "
            "Enroll for $0 today on learncode.io"
        )
    },
    {
        "id": 4,
        "name": "AI Tool Reel Caption",
        "caption": (
            "🤯 Stop spending hours on PowerPoint! This revolutionary AI tool creates complete pitch decks in 10 seconds. "
            "Completely free to use with unlimited exports. "
            "Try it right now at slideai.app"
        )
    },
    {
        "id": 5,
        "name": "Discount / Deal Reel Caption",
        "caption": (
            "🎉 Mega Sale Alert! Get 50% OFF on all UI/UX Masterclass courses. "
            "Use promo code SAVE50 at checkout. "
            "Offer valid till midnight only! Don't miss out on skillup.com"
        )
    }
]

def run_tests():
    print("=" * 80)
    print("RUNNING REELCLAIM PHASE 1 - EXTRACTION MODULE VERIFICATION TESTS")
    print("=" * 80)

    results = []
    for test in TEST_CASES:
        print(f"\n--- [TEST {test['id']}] {test['name']} ---")
        print(f"INPUT CAPTION:\n\"{test['caption']}\"\n")
        
        response = extract_claims(test["caption"])
        res_json = response.model_dump()
        
        print("REAL JSON OUTPUT:")
        print(json.dumps(res_json, indent=2))
        results.append({"test_id": test["id"], "name": test["name"], "output": res_json})
    
    return results

if __name__ == "__main__":
    run_tests()
