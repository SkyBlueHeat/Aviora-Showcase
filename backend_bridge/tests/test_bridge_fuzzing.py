"""
Backend Bridge Payload Fuzzing Tests — Checkpoint 1

Tests every public bridge method against adversarial payloads:
  None, empty object, wrong primitive type, string instead of list,
  list instead of string, empty string, whitespace, very long input,
  Turkish characters, emoji, HTML, markdown, null byte, extra fields,
  missing required fields, set, tuple, datetime, Path, NaN, Infinity,
  secret-containing strings, Windows path strings.

Verifies:
  - Response format is always { success, data, error }
  - No traceback, secret, or full path leaks to frontend
  - No unhandled exception crashes the method
"""

import sys
import os
import json
import math
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

# Setup paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from backend_bridge.api import ExcelBridgeAPI
from backend_bridge.tests.create_fixture import create_fixture, FIXTURE_PATH

PASS_COUNT = 0
FAIL_COUNT = 0
ERROR_COUNT = 0


def check(condition: bool, label: str):
    global PASS_COUNT, FAIL_COUNT
    if condition:
        PASS_COUNT += 1
        print(f"  PASS: {label}")
    else:
        FAIL_COUNT += 1
        print(f"  FAIL: {label}")


def check_response_format(result: dict, method_name: str, payload_desc: str):
    """Verify response has required fields and correct types."""
    label = f"{method_name}({payload_desc})"
    check(isinstance(result, dict), f"{label}: returns dict")
    check("success" in result, f"{label}: has 'success' field")
    check("data" in result, f"{label}: has 'data' field")
    check("error" in result, f"{label}: has 'error' field")
    check(isinstance(result.get("success"), bool), f"{label}: 'success' is bool")
    # Verify response is JSON-safe (no NaN/Infinity leaking)
    try:
        json.dumps(result, allow_nan=False)
        check(True, f"{label}: response is strict JSON-safe (no NaN/Infinity)")
    except (ValueError, TypeError):
        check(False, f"{label}: response contains NaN/Infinity or non-serializable data")
    if result.get("error") is not None:
        err = result["error"]
        if isinstance(err, dict):
            check("code" in err, f"{label}: error has 'code'")
            check("message" in err, f"{label}: error has 'message'")
            check(not any(s in str(err.get("message", "")) for s in [
                "Traceback", "sk-", "api_key=", "password=", "C:\\Users", "erkay"
            ]), f"{label}: error does not leak secrets/paths")


def run_fuzz(method_name: str, api_method, payloads: list, fixture_api=None):
    """Run a list of (payload, description) tuples against a method."""
    for payload, desc in payloads:
        try:
            if isinstance(payload, tuple):
                result = api_method(*payload)
            else:
                result = api_method(payload)
            check_response_format(result, method_name, desc)
            if isinstance(result, dict) and not result.get("success"):
                err_msg = ""
                if isinstance(result.get("error"), dict):
                    err_msg = result["error"].get("message", "")
                elif isinstance(result.get("error"), str):
                    err_msg = result["error"]
                check(
                    "Traceback" not in err_msg,
                    f"{method_name}({desc}): no traceback in error"
                )
                check(
                    "sk-" not in err_msg and "api_key" not in err_msg.lower(),
                    f"{method_name}({desc}): no secret leak in error"
                )
            # Detect false success: clearly invalid payloads should not return success=True
            # Note: empty dict {} and None are valid for methods with optional params (payload or {})
            # Only flag clearly wrong types: int, float, list, set, tuple, empty string, whitespace
            is_invalid = (
                (isinstance(payload, str) and (payload == "" or payload.strip() == "")) or
                (isinstance(payload, (int, list, set, tuple)) and not isinstance(payload, bool)) or
                (isinstance(payload, float) and (math.isnan(payload) or math.isinf(payload)))
            )
            if is_invalid and isinstance(result, dict):
                check(
                    result.get("success") is not True,
                    f"{method_name}({desc}): invalid payload does not return success=True"
                )
        except Exception as e:
            global ERROR_COUNT
            ERROR_COUNT += 1
            print(f"  ERROR: {method_name}({desc}) threw unhandled exception: {e}")


# ── Fuzz payloads ──────────────────────────────────────────────────────────

FUZZ_PAYLOADS_DICT = [
    (None, "None"),
    ({}, "empty dict"),
    ({"jobDescription": None}, "None jd"),
    ({"jobDescription": ""}, "empty string jd"),
    ({"jobDescription": "   "}, "whitespace jd"),
    ({"jobDescription": 123}, "int instead of string"),
    ({"jobDescription": ["list", "item"]}, "list instead of string"),
    ({"jobDescription": True}, "bool instead of string"),
    ({"jobDescription": {"nested": "obj"}}, "dict instead of string"),
    ({"jobDescription": "a" * 50000}, "very long input"),
    ({"jobDescription": "Türkçe iş ilanı mühendis"}, "Turkish chars"),
    ({"jobDescription": "Software engineer 🚀 position"}, "emoji"),
    ({"jobDescription": "<script>alert('xss')</script> engineer"}, "HTML"),
    ({"jobDescription": "# Job Title\n## Requirements\n- Python"}, "markdown"),
    ({"jobDescription": "Engineer\x00null byte"}, "null byte"),
    ({"jobDescription": "sk-1234567890abcdef key in text"}, "secret in text"),
    ({"jobDescription": "C:\\Users\\secret\\file.py error"}, "Windows path in text"),
    ({"jobDescription": "Senior Software Engineer", "extra": "unknown"}, "extra field"),
    ({"jobDescription": "Senior Software Engineer", "candidateSkills": None}, "None skills"),
    ({"jobDescription": "Senior Software Engineer", "candidateSkills": "string"}, "string skills"),
    ({"jobDescription": "Senior Software Engineer", "candidateSkills": [None, 123, True]}, "mixed types skills"),
    ({"jobDescription": "Senior Software Engineer", "candidateSkills": set(["React"])}, "set skills"),
    ({"jobDescription": "Senior Software Engineer", "candidateSkills": ("React",)}, "tuple skills"),
    ({"jobDescription": float('nan')}, "NaN jd"),
    ({"jobDescription": float('inf')}, "Infinity jd"),
    ({"jobDescription": datetime.now()}, "datetime as jd"),
    ({"jobDescription": Path("/tmp/test")}, "Path as jd"),
]

FUZZ_PAYLOADS_COVER_LETTER = [
    (None, "None"),
    ({}, "empty dict"),
    ({"company": None, "role": "Eng", "name": "Test"}, "None company"),
    ({"company": "", "role": "Eng", "name": "Test"}, "empty company"),
    ({"company": "   ", "role": "Eng", "name": "Test"}, "whitespace company"),
    ({"company": 123, "role": "Eng", "name": "Test"}, "int company"),
    ({"company": ["list"], "role": "Eng", "name": "Test"}, "list company"),
    ({"company": "Test Co", "role": None, "name": "Test"}, "None role"),
    ({"company": "Test Co", "role": "", "name": "Test"}, "empty role"),
    ({"company": "Test Co", "role": "Eng", "name": None}, "None name"),
    ({"company": "Test Co", "role": "Eng", "name": ""}, "empty name"),
    ({"company": "Test Co", "role": "Eng", "name": "Test", "tone": None}, "None tone"),
    ({"company": "Test Co", "role": "Eng", "name": "Test", "tone": 123}, "int tone"),
    ({"company": "Test Co", "role": "Eng", "name": "Test", "tone": ["list"]}, "list tone"),
    ({"company": "Test Co", "role": "Eng", "name": "Test", "years": None}, "None years"),
    ({"company": "Test Co", "role": "Eng", "name": "Test", "years": ["list"]}, "list years"),
    ({"company": "Test Co", "role": "Eng", "name": "Test", "jobDescription": "a"*50000}, "very long jd"),
    ({"company": "Türkçe Şirket", "role": "Mühendis", "name": "Ömer"}, "Turkish chars"),
    ({"company": "Emoji Co 🎉", "role": "Eng", "name": "Test"}, "emoji"),
    ({"company": "<script>alert(1)</script>", "role": "Eng", "name": "Test"}, "HTML"),
    ({"company": "Test\x00Co", "role": "Eng", "name": "Test"}, "null byte"),
    ({"company": "Test Co", "role": "Eng", "name": "Test", "extra": "field"}, "extra field"),
    ({"company": float('nan'), "role": "Eng", "name": "Test"}, "NaN company"),
    ({"company": float('inf'), "role": "Eng", "name": "Test"}, "Infinity company"),
    ({"company": datetime.now(), "role": "Eng", "name": "Test"}, "datetime company"),
    ({"company": Path("/tmp"), "role": "Eng", "name": "Test"}, "Path company"),
]

FUZZ_PAYLOADS_LINKEDIN = [
    (None, "None"),
    ({}, "empty dict"),
    ({"messageType": None, "recipientName": "S", "company": "C", "yourName": "Y"}, "None messageType"),
    ({"messageType": 123, "recipientName": "S", "company": "C", "yourName": "Y"}, "int messageType"),
    ({"messageType": ["list"], "recipientName": "S", "company": "C", "yourName": "Y"}, "list messageType"),
    ({"messageType": "unknown_type", "recipientName": "S", "company": "C", "yourName": "Y"}, "unknown type"),
    ({"messageType": "connection", "recipientName": None, "company": "C", "yourName": "Y"}, "None recipient"),
    ({"messageType": "connection", "recipientName": "", "company": "C", "yourName": "Y"}, "empty recipient"),
    ({"messageType": "connection", "recipientName": "   ", "company": "C", "yourName": "Y"}, "whitespace recipient"),
    ({"messageType": "connection", "recipientName": 123, "company": "C", "yourName": "Y"}, "int recipient"),
    ({"messageType": "connection", "recipientName": "S", "company": None, "yourName": "Y"}, "None company"),
    ({"messageType": "connection", "recipientName": "S", "company": "", "yourName": "Y"}, "empty company"),
    ({"messageType": "connection", "recipientName": "S", "company": "C", "yourName": None}, "None yourName"),
    ({"messageType": "connection", "recipientName": "S", "company": "C", "yourName": ""}, "empty yourName"),
    ({"messageType": "connection", "recipientName": "S", "company": "C", "yourName": "Y", "extra": "field"}, "extra field"),
    ({"messageType": "connection", "recipientName": "Türkçe İsim", "company": "Şirket", "yourName": "Ömer"}, "Turkish chars"),
    ({"messageType": "connection", "recipientName": "Sarah 🚀", "company": "C", "yourName": "Y"}, "emoji"),
    ({"messageType": "connection", "recipientName": "Sarah\x00", "company": "C", "yourName": "Y"}, "null byte"),
    ({"messageType": "connection", "recipientName": "<script>alert(1)</script>", "company": "C", "yourName": "Y"}, "HTML"),
    ({"messageType": "connection", "recipientName": "O'Brien-Smith Jr.", "company": "C", "yourName": "Y"}, "apostrophe/hyphen"),
    ({"messageType": "connection", "recipientName": "Mary Jane Watson", "company": "C", "yourName": "Y"}, "multi-part name"),
    ({"messageType": float('nan'), "recipientName": "S", "company": "C", "yourName": "Y"}, "NaN messageType"),
    ({"messageType": float('inf'), "recipientName": "S", "company": "C", "yourName": "Y"}, "Infinity messageType"),
    ({"messageType": datetime.now(), "recipientName": "S", "company": "C", "yourName": "Y"}, "datetime messageType"),
    ({"messageType": Path("/tmp"), "recipientName": "S", "company": "C", "yourName": "Y"}, "Path messageType"),
]

FUZZ_PAYLOADS_INTERVIEW_QUESTIONS = [
    (None, "None"),
    ({}, "empty dict"),
    ({"category": None}, "None category"),
    ({"category": ""}, "empty category"),
    ({"category": "   "}, "whitespace category"),
    ({"category": 123}, "int category"),
    ({"category": ["list"]}, "list category"),
    ({"category": "UnknownCategory"}, "unknown category"),
    ({"category": "Behavioral", "count": None}, "None count"),
    ({"category": "Behavioral", "count": "string"}, "string count"),
    ({"category": "Behavioral", "count": -1}, "negative count"),
    ({"category": "Behavioral", "count": 0}, "zero count"),
    ({"category": "Behavioral", "count": 1000000}, "very large count"),
    ({"category": "Behavioral", "count": float('nan')}, "NaN count"),
    ({"category": "Behavioral", "count": float('inf')}, "Infinity count"),
    ({"category": "Behavioral", "count": [1, 2]}, "list count"),
    ({"category": "Behavioral", "extra": "field"}, "extra field"),
    ({"category": "Türkçe"}, "Turkish category"),
    ({"category": "Behavioral\x00"}, "null byte category"),
    ({"category": datetime.now()}, "datetime category"),
    ({"category": Path("/tmp")}, "Path category"),
]

FUZZ_PAYLOADS_SAVE_PRACTICE = [
    (None, "None"),
    ({}, "empty dict"),
    ({"question": None, "answer": "a", "selfRating": 3}, "None question"),
    ({"question": "", "answer": "a", "selfRating": 3}, "empty question"),
    ({"question": "   ", "answer": "a", "selfRating": 3}, "whitespace question"),
    ({"question": 123, "answer": "a", "selfRating": 3}, "int question"),
    ({"question": ["list"], "answer": "a", "selfRating": 3}, "list question"),
    ({"question": "Q", "answer": None, "selfRating": 3}, "None answer"),
    ({"question": "Q", "answer": "", "selfRating": 3}, "empty answer"),
    ({"question": "Q", "answer": "   ", "selfRating": 3}, "whitespace answer"),
    ({"question": "Q", "answer": 123, "selfRating": 3}, "int answer"),
    ({"question": "Q", "answer": ["list"], "selfRating": 3}, "list answer"),
    ({"question": "Q", "answer": "a"*50000, "selfRating": 3}, "very long answer"),
    ({"question": "Q", "answer": "a", "selfRating": None}, "None rating"),
    ({"question": "Q", "answer": "a", "selfRating": "string"}, "string rating"),
    ({"question": "Q", "answer": "a", "selfRating": 0}, "zero rating"),
    ({"question": "Q", "answer": "a", "selfRating": -1}, "negative rating"),
    ({"question": "Q", "answer": "a", "selfRating": 6}, "rating > 5"),
    ({"question": "Q", "answer": "a", "selfRating": 3.5}, "float rating"),
    ({"question": "Q", "answer": "a", "selfRating": [3]}, "list rating"),
    ({"question": "Q", "answer": "a", "selfRating": 3, "elapsedSeconds": None}, "None elapsed"),
    ({"question": "Q", "answer": "a", "selfRating": 3, "elapsedSeconds": "string"}, "string elapsed"),
    ({"question": "Q", "answer": "a", "selfRating": 3, "elapsedSeconds": -1}, "negative elapsed"),
    ({"question": "Q", "answer": "a", "selfRating": 3, "elapsedSeconds": float('nan')}, "NaN elapsed"),
    ({"question": "Q", "answer": "a", "selfRating": 3, "elapsedSeconds": float('inf')}, "Infinity elapsed"),
    ({"question": "Q", "answer": "a", "selfRating": 3, "extra": "field"}, "extra field"),
    ({"question": "Türkçe soru?", "answer": "Türkçe cevap", "selfRating": 3}, "Turkish chars"),
    ({"question": "Q 🚀", "answer": "a", "selfRating": 3}, "emoji"),
    ({"question": "Q\x00", "answer": "a", "selfRating": 3}, "null byte"),
    ({"question": "<script>alert(1)</script>", "answer": "a", "selfRating": 3}, "HTML"),
    ({"question": "Q", "answer": "a", "selfRating": 3, "category": None}, "None category"),
    ({"question": "Q", "answer": "a", "selfRating": 3, "category": 123}, "int category"),
    ({"question": "Q", "answer": "a", "selfRating": 3, "category": ["list"]}, "list category"),
]

FUZZ_PAYLOADS_EXPORT = [
    (None, "None"),
    ({}, "empty dict"),
    ({"type": None}, "None type"),
    ({"type": ""}, "empty type"),
    ({"type": "   "}, "whitespace type"),
    ({"type": 123}, "int type"),
    ({"type": ["list"]}, "list type"),
    ({"type": "unknown_type"}, "unknown type"),
    ({"type": "weekly"}, "weekly"),
    ({"type": "monthly"}, "monthly"),
    ({"type": "WEEKLY"}, "uppercase"),
    ({"type": "Türkçe"}, "Turkish type"),
    ({"type": "weekly\x00"}, "null byte type"),
    ({"type": float('nan')}, "NaN type"),
    ({"type": float('inf')}, "Infinity type"),
    ({"type": datetime.now()}, "datetime type"),
    ({"type": Path("/tmp")}, "Path type"),
    ({"type": "weekly", "extra": "field"}, "extra field"),
]


def main():
    global PASS_COUNT, FAIL_COUNT, ERROR_COUNT

    # Create fixture workbook
    if not os.path.exists(FIXTURE_PATH):
        create_fixture()

    # Use temp directory for JSON file isolation — no backup/restore of real files
    import hashlib
    tmpdir = tempfile.TemporaryDirectory(prefix="fuzz_test_")
    data_dir = tmpdir.name

    # SHA256 hash of real JSON files before tests
    real_files = [
        os.path.join(PROJECT_ROOT, "interview_scores.json"),
        os.path.join(PROJECT_ROOT, "streak_data.json"),
        os.path.join(PROJECT_ROOT, "settings.json"),
    ]
    hashes_before = {}
    for f in real_files:
        if os.path.exists(f):
            with open(f, "rb") as fh:
                hashes_before[f] = hashlib.sha256(fh.read()).hexdigest()

    api = ExcelBridgeAPI(workbook_path=FIXTURE_PATH, data_dir=data_dir)

    print("=" * 70)
    print("BACKEND BRIDGE PAYLOAD FUZZING TESTS")
    print("=" * 70)

    # ── 1. analyze_job_description ────────────────────────────────────────
    print("\n=== analyze_job_description fuzzing ===")
    run_fuzz("analyze_job_description", api.analyze_job_description, FUZZ_PAYLOADS_DICT)

    # ── 2. generate_cover_letter ──────────────────────────────────────────
    print("\n=== generate_cover_letter fuzzing ===")
    run_fuzz("generate_cover_letter", api.generate_cover_letter, FUZZ_PAYLOADS_COVER_LETTER)

    # ── 3. generate_linkedin_message ──────────────────────────────────────
    print("\n=== generate_linkedin_message fuzzing ===")
    run_fuzz("generate_linkedin_message", api.generate_linkedin_message, FUZZ_PAYLOADS_LINKEDIN)

    # ── 4. get_interview_questions ────────────────────────────────────────
    print("\n=== get_interview_questions fuzzing ===")
    run_fuzz("get_interview_questions", api.get_interview_questions, FUZZ_PAYLOADS_INTERVIEW_QUESTIONS)

    # ── 5. save_interview_practice ────────────────────────────────────────
    print("\n=== save_interview_practice fuzzing ===")
    run_fuzz("save_interview_practice", api.save_interview_practice, FUZZ_PAYLOADS_SAVE_PRACTICE)

    # ── 6. get_interview_practice_history ─────────────────────────────────
    print("\n=== get_interview_practice_history fuzzing ===")
    # This method takes no args, just test it works
    try:
        result = api.get_interview_practice_history()
        check_response_format(result, "get_interview_practice_history", "no args")
    except Exception as e:
        ERROR_COUNT += 1
        print(f"  ERROR: get_interview_practice_history threw: {e}")

    # ── 7. get_streak_data ────────────────────────────────────────────────
    print("\n=== get_streak_data fuzzing ===")
    try:
        result = api.get_streak_data()
        check_response_format(result, "get_streak_data", "no args")
    except Exception as e:
        ERROR_COUNT += 1
        print(f"  ERROR: get_streak_data threw: {e}")

    # ── 8. get_next_actions ───────────────────────────────────────────────
    print("\n=== get_next_actions fuzzing ===")
    try:
        result = api.get_next_actions()
        check_response_format(result, "get_next_actions", "no args")
    except Exception as e:
        ERROR_COUNT += 1
        print(f"  ERROR: get_next_actions threw: {e}")

    # ── 9. export_report ──────────────────────────────────────────────────
    print("\n=== export_report fuzzing ===")
    run_fuzz("export_report", api.export_report, FUZZ_PAYLOADS_EXPORT)

    # ── 10. Workbook read methods ─────────────────────────────────────────
    print("\n=== Workbook read methods fuzzing ===")
    for method_name, method in [
        ("get_applications", api.get_applications),
        ("get_dashboard", api.get_dashboard),
        ("get_kpis", api.get_kpis),
        ("get_pipeline", api.get_pipeline),
        ("get_salary_data", api.get_salary_data),
    ]:
        try:
            result = method()
            check(isinstance(result, dict), f"{method_name}: returns dict")
            check("data" in result, f"{method_name}: has 'data' field")
            check("error" in result, f"{method_name}: has 'error' field")
        except Exception as e:
            ERROR_COUNT += 1
            print(f"  ERROR: {method_name} threw: {e}")

    # ── 11. Workbook write methods with bad payloads ─────────────────────
    print("\n=== Workbook write methods fuzzing ===")
    write_payloads = [
        (None, "None"),
        ({}, "empty dict"),
        ({"company": None, "role": "R", "status": "Saved"}, "None company"),
        ({"company": "", "role": "R", "status": "Saved"}, "empty company"),
        ({"company": 123, "role": "R", "status": "Saved"}, "int company"),
        ({"company": ["list"], "role": "R", "status": "Saved"}, "list company"),
        ({"company": "C", "role": None, "status": "Saved"}, "None role"),
        ({"company": "C", "role": "R", "status": None}, "None status"),
        ({"company": "C", "role": "R", "status": 123}, "int status"),
        ({"company": "C", "role": "R", "status": ["list"]}, "list status"),
        ({"company": "C", "role": "R", "status": "Saved", "fitScore": "not_a_number"}, "string fitScore"),
        ({"company": "C", "role": "R", "status": "Saved", "fitScore": None}, "None fitScore"),
        ({"company": "C", "role": "R", "status": "Saved", "fitScore": float('nan')}, "NaN fitScore"),
        ({"company": "C", "role": "R", "status": "Saved", "fitScore": float('inf')}, "Infinity fitScore"),
        ({"company": "C", "role": "R", "status": "Saved", "fitScore": [1]}, "list fitScore"),
        ({"company": "C", "role": "R", "status": "Saved", "notes": None}, "None notes"),
        ({"company": "C", "role": "R", "status": "Saved", "notes": 123}, "int notes"),
        ({"company": "C", "role": "R", "status": "Saved", "notes": ["list"]}, "list notes"),
        ({"company": "C", "role": "R", "status": "Saved", "url": None}, "None url"),
        ({"company": "C", "role": "R", "status": "Saved", "url": 123}, "int url"),
        ({"company": "C", "role": "R", "status": "Saved", "url": ["list"]}, "list url"),
        ({"company": "C", "role": "R", "status": "Saved", "extra": "field"}, "extra field"),
        ({"company": "Türkçe", "role": "Mühendis", "status": "Saved"}, "Turkish chars"),
        ({"company": "C\x00", "role": "R", "status": "Saved"}, "null byte"),
        ({"company": "C", "role": "R", "status": "Saved", "notes": "a"*50000}, "very long notes"),
    ]

    for payload, desc in write_payloads:
        try:
            result = api.add_application(payload)
            check(isinstance(result, dict), f"add_application({desc}): returns dict")
            check("success" in result, f"add_application({desc}): has 'success' field")
            err_msg = ""
            if isinstance(result.get("error"), dict):
                err_msg = result["error"].get("message", "")
            elif isinstance(result.get("error"), str):
                err_msg = result["error"]
            check(
                "Traceback" not in err_msg and "sk-" not in err_msg,
                f"add_application({desc}): no leak in error"
            )
        except Exception as e:
            ERROR_COUNT += 1
            print(f"  ERROR: add_application({desc}) threw: {e}")

    # update_application_status with bad payloads
    update_payloads = [
        ((None, "Saved"), "None id"),
        (("", "Saved"), "empty id"),
        (("APP-001", None), "None status"),
        (("APP-001", ""), "empty status"),
        (("APP-001", 123), "int status"),
        (("APP-001", ["list"]), "list status"),
        (("APP-001", "Saved"), "valid"),
        ((123, "Saved"), "int id"),
        ((["list"], "Saved"), "list id"),
        ((float('nan'), "Saved"), "NaN id"),
    ]
    for args, desc in update_payloads:
        try:
            result = api.update_application_status(*args)
            check(isinstance(result, dict), f"update_application_status({desc}): returns dict")
            check("success" in result, f"update_application_status({desc}): has 'success' field")
        except Exception as e:
            ERROR_COUNT += 1
            print(f"  ERROR: update_application_status({desc}) threw: {e}")

    # edit_application with bad payloads
    edit_payloads = [
        ((None, {"company": "C"}), "None id"),
        (("", {"company": "C"}), "empty id"),
        (("APP-001", None), "None data"),
        (("APP-001", {}), "empty data"),
        (("APP-001", {"company": 123}), "int company"),
        (("APP-001", {"company": ["list"]}), "list company"),
        (("APP-001", {"fitScore": "abc"}), "string fitScore"),
        (("APP-001", {"fitScore": None}), "None fitScore"),
        (("APP-001", {"fitScore": float('nan')}), "NaN fitScore"),
    ]
    for args, desc in edit_payloads:
        try:
            result = api.edit_application(*args)
            check(isinstance(result, dict), f"edit_application({desc}): returns dict")
            check("success" in result, f"edit_application({desc}): has 'success' field")
        except Exception as e:
            ERROR_COUNT += 1
            print(f"  ERROR: edit_application({desc}) threw: {e}")

    # ── 12. validate_workbook with bad paths ──────────────────────────────
    print("\n=== validate_workbook fuzzing ===")
    validate_payloads = [
        (None, "None path"),
        ("", "empty path"),
        ("   ", "whitespace path"),
        (123, "int path"),
        (["list"], "list path"),
        ("nonexistent.xlsx", "nonexistent file"),
        ("C:\\Users\\secret\\file.xlsx", "Windows path"),
        ("file\x00.xlsx", "null byte path"),
        (float('nan'), "NaN path"),
        (datetime.now(), "datetime path"),
        (Path("/tmp"), "Path object"),
    ]
    for path, desc in validate_payloads:
        try:
            result = api.validate_workbook(path)
            check(isinstance(result, dict), f"validate_workbook({desc}): returns dict")
            check("valid" in result, f"validate_workbook({desc}): has 'valid' field")
            err_msg = str(result.get("error", ""))
            check(
                "C:\\Users" not in err_msg and "erkay" not in err_msg,
                f"validate_workbook({desc}): no path leak in error"
            )
        except Exception as e:
            ERROR_COUNT += 1
            print(f"  ERROR: validate_workbook({desc}) threw: {e}")

    # ── Verify real JSON files were not modified ──────────────────────────
    print("\n=== JSON Isolation Verification ===")
    for f, hash_before in hashes_before.items():
        if os.path.exists(f):
            with open(f, "rb") as fh:
                hash_after = hashlib.sha256(fh.read()).hexdigest()
            check(hash_before == hash_after, f"{os.path.basename(f)} SHA256 unchanged")

    # Cleanup temp dir
    tmpdir.cleanup()

    # ── Summary ───────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print(f"FUZZING TEST SUMMARY: {PASS_COUNT} PASS, {FAIL_COUNT} FAIL, {ERROR_COUNT} ERROR")
    print("=" * 70)

    if FAIL_COUNT > 0 or ERROR_COUNT > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
