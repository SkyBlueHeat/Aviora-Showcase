"""Tests for Phase 2B bridge methods in api.py.

Verifies:
- analyze_job_description: valid input, short input, missing input
- generate_cover_letter: valid input, missing required fields
- generate_linkedin_message: valid input, missing required fields
- get_interview_questions: default, category filter
- save_interview_practice: valid save, validation errors
- get_interview_practice_history: returns entries + stats
- get_streak_data: returns structured data
- get_next_actions: returns list (may be empty without workbook)
- export_report: returns content + filename
- _sanitize_error: removes file paths
- _ok / _err: response format consistency
"""
import os
import sys
import json
import tempfile
import shutil

# Ensure project root is on sys.path
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from backend_bridge.api import ExcelBridgeAPI

PASS_COUNT = 0
ERROR_COUNT = 0


def check(condition: bool, label: str):
    global PASS_COUNT, ERROR_COUNT
    if condition:
        PASS_COUNT += 1
        print(f"  PASS: {label}")
    else:
        ERROR_COUNT += 1
        print(f"  FAIL: {label}")


def run_tests():
    # Use the fixture workbook for testing
    fixture_path = os.path.join(
        _project_root, "backend_bridge", "tests", "test_fixture_workbook.xlsx"
    )

    # Use temp directory for JSON file isolation — no backup/restore of real files
    import hashlib
    tmpdir = tempfile.TemporaryDirectory(prefix="bridge_methods_")
    data_dir = tmpdir.name
    scores_file = os.path.join(data_dir, "interview_scores.json")

    # SHA256 hash of real JSON files before tests
    real_files = [
        os.path.join(_project_root, "interview_scores.json"),
        os.path.join(_project_root, "streak_data.json"),
        os.path.join(_project_root, "settings.json"),
    ]
    hashes_before = {}
    for f in real_files:
        if os.path.exists(f):
            with open(f, "rb") as fh:
                hashes_before[f] = hashlib.sha256(fh.read()).hexdigest()

    api = ExcelBridgeAPI(fixture_path, data_dir=data_dir)

    # === Test 1: _ok response format ===
    print("\n=== Response Format ===")
    result = api._ok({"test": True})
    check(result["success"] is True, "_ok returns success=True")
    check(result["data"] == {"test": True}, "_ok returns correct data")
    check(result.get("error") is None, "_ok has no error")

    # === Test 2: _err response format ===
    result = api._err("TEST_CODE", "Something went wrong")
    check(result["success"] is False, "_err returns success=False")
    check(result.get("data") is None, "_err has no data")
    check(result["error"] is not None, "_err has error object")
    check(result["error"]["code"] == "TEST_CODE", "_err has correct error code")
    check("Something went wrong" in result["error"]["message"], "_err has correct error message")

    # === Test 3: _sanitize_error ===
    print("\n=== Error Sanitization ===")
    sanitized = ExcelBridgeAPI._sanitize_error(Exception("Error at C:\\Users\\secret\\file.py line 42"))
    check("C:\\Users" not in sanitized, "_sanitize_error removes Windows paths")
    check("[path]" in sanitized or "file.py" not in sanitized, "_sanitize_error replaces paths")

    sanitized2 = ExcelBridgeAPI._sanitize_error(Exception("sk-1234567890abcdefghijklmnopqrstuvwxyz key leaked"))
    check("sk-1234567890abcdefghijklmnopqrstuvwxyz" not in sanitized2, "_sanitize_error removes API keys")

    # === Test 4: analyze_job_description ===
    print("\n=== analyze_job_description ===")
    jd_text = """
    We are looking for a Senior Python Developer with 5+ years of experience.
    Required skills: Python, Django, PostgreSQL, AWS, Docker.
    You will be building scalable APIs and working with microservices.
    Competitive salary $120k-$160k. Remote-friendly. Great benefits.
    """
    result = api.analyze_job_description({"jobDescription": jd_text, "candidateSkills": ["Python", "AWS"]})
    check(result["success"] is True, "analyze_job_description succeeds with valid input")
    if result["success"]:
        data = result["data"]
        check("fitScore" in data, "result has fitScore")
        check("seniority" in data, "result has seniority")
        check("salaryEstimate" in data, "result has salaryEstimate")
        check("techStack" in data, "result has techStack")
        check("greenFlags" in data, "result has greenFlags")
        check("redFlags" in data, "result has redFlags")
        check("matchedKeywords" in data, "result has matchedKeywords")
        check("missingKeywords" in data, "result has missingKeywords")
        check("summary" in data, "result has summary")
        check(isinstance(data["techStack"], list), "techStack is a list")
        check(isinstance(data["fitScore"], int), "fitScore is an int")

    # Short input
    result = api.analyze_job_description({"jobDescription": "short"})
    check(result["success"] is False, "analyze_job_description rejects short input")
    check(result["error"]["code"] == "VALIDATION_ERROR", "short input returns VALIDATION_ERROR")

    # Empty input
    result = api.analyze_job_description({"jobDescription": ""})
    check(result["success"] is False, "analyze_job_description rejects empty input")

    # === Test 5: generate_cover_letter ===
    print("\n=== generate_cover_letter ===")
    result = api.generate_cover_letter({
        "company": "Tech Corp",
        "role": "Senior Python Developer",
        "name": "Test User",
        "years": "5",
        "tone": "professional",
        "achievement": "Built scalable APIs serving 1M requests/day",
    })
    check(result["success"] is True, "generate_cover_letter succeeds with valid input")
    if result["success"]:
        data = result["data"]
        check("content" in data, "result has content")
        check("mode" in data, "result has mode")
        check("wordCount" in data, "result has wordCount")
        check(isinstance(data["content"], str) and len(data["content"]) > 0, "content is non-empty string")
        check(data["mode"] in ("ai", "offline"), "mode is ai or offline")
        check(data["wordCount"] > 0, "wordCount is positive")

    # Missing company
    result = api.generate_cover_letter({"role": "Dev", "name": "User"})
    check(result["success"] is False, "generate_cover_letter rejects missing company")
    check(result["error"]["code"] == "VALIDATION_ERROR", "missing company returns VALIDATION_ERROR")

    # Missing role
    result = api.generate_cover_letter({"company": "Corp", "name": "User"})
    check(result["success"] is False, "generate_cover_letter rejects missing role")

    # Missing name
    result = api.generate_cover_letter({"company": "Corp", "role": "Dev"})
    check(result["success"] is False, "generate_cover_letter rejects missing name")

    # === Test 6: generate_linkedin_message ===
    print("\n=== generate_linkedin_message ===")
    result = api.generate_linkedin_message({
        "messageType": "connection",
        "recipientName": "Jane Smith",
        "company": "Tech Corp",
        "yourName": "Test User",
        "yourRole": "Software Engineer",
    })
    check(result["success"] is True, "generate_linkedin_message succeeds with valid input")
    if result["success"]:
        data = result["data"]
        check("content" in data, "result has content")
        check("messageType" in data, "result has messageType")
        check("characterCount" in data, "result has characterCount")
        check("characterLimit" in data, "result has characterLimit")
        check(isinstance(data["content"], str) and len(data["content"]) > 0, "content is non-empty string")
        check(data["characterCount"] == len(data["content"]), "characterCount matches content length")

    # Missing recipient
    result = api.generate_linkedin_message({
        "messageType": "connection",
        "company": "Tech Corp",
        "yourName": "Test User",
    })
    check(result["success"] is False, "generate_linkedin_message rejects missing recipient name")

    # Missing company
    result = api.generate_linkedin_message({
        "messageType": "connection",
        "recipientName": "Jane",
        "yourName": "Test User",
    })
    check(result["success"] is False, "generate_linkedin_message rejects missing company")

    # === Test 7: get_interview_questions ===
    print("\n=== get_interview_questions ===")
    result = api.get_interview_questions({})
    check(result["success"] is True, "get_interview_questions succeeds")
    if result["success"]:
        data = result["data"]
        check(isinstance(data, list), "result is a list")
        check(len(data) > 0, "returns at least one question")
        if data:
            q = data[0]
            check("id" in q, "question has id")
            check("category" in q, "question has category")
            check("difficulty" in q, "question has difficulty")
            check("question" in q, "question has question text")
            check("tips" in q, "question has tips")
            check("starRelevant" in q, "question has starRelevant")
            check(q["category"] in ("Behavioral", "Technical"), "category is Behavioral or Technical")
            check(q["difficulty"] in ("Easy", "Medium", "Hard"), "difficulty is valid")

    # Category filter
    result = api.get_interview_questions({"category": "Behavioral"})
    check(result["success"] is True, "get_interview_questions with category filter succeeds")
    if result["success"] and result["data"]:
        check(all(q["category"] == "Behavioral" for q in result["data"]), "all questions are Behavioral")

    # === Test 8: save_interview_practice ===
    print("\n=== save_interview_practice ===")
    result = api.save_interview_practice({
        "questionId": "test-1",
        "question": "Tell me about a challenge you faced.",
        "category": "Behavioral",
        "answer": "I faced a challenge with legacy code and refactored it successfully.",
        "elapsedSeconds": 120,
        "selfRating": 4,
        "notes": "Felt good about this one.",
    })
    check(result["success"] is True, "save_interview_practice succeeds with valid input")
    if result["success"]:
        check(result["data"]["saved"] is True, "result confirms saved=True")

    # Verify it was actually saved to JSON
    check(os.path.exists(scores_file), "interview_scores.json exists after save")
    with open(scores_file, "r", encoding="utf-8") as f:
        entries = json.load(f)
    check(isinstance(entries, list), "JSON file contains a list")
    check(len(entries) > 0, "JSON file has at least one entry")
    last_entry = entries[-1]
    check(last_entry["question"] == "Tell me about a challenge you faced.", "saved question matches")
    check(last_entry["self_rating"] == 4, "saved selfRating matches")
    check(last_entry["word_count"] > 0, "saved wordCount is positive")

    # Missing question
    result = api.save_interview_practice({
        "answer": "Some answer",
        "selfRating": 3,
    })
    check(result["success"] is False, "save_interview_practice rejects missing question")

    # Missing answer
    result = api.save_interview_practice({
        "question": "Test question",
        "selfRating": 3,
    })
    check(result["success"] is False, "save_interview_practice rejects missing answer")

    # Invalid selfRating
    result = api.save_interview_practice({
        "question": "Test question",
        "answer": "Test answer",
        "selfRating": 10,
    })
    check(result["success"] is False, "save_interview_practice rejects selfRating > 5")

    # === Test 9: get_interview_practice_history ===
    print("\n=== get_interview_practice_history ===")
    result = api.get_interview_practice_history()
    check(result["success"] is True, "get_interview_practice_history succeeds")
    if result["success"]:
        data = result["data"]
        check("entries" in data, "result has entries")
        check("stats" in data, "result has stats")
        check("totalAnswers" in data["stats"], "stats has totalAnswers")
        check("avgScore" in data["stats"], "stats has avgScore")
        check("byCategory" in data["stats"], "stats has byCategory")
        check(isinstance(data["entries"], list), "entries is a list")
        check(data["stats"]["totalAnswers"] >= 1, "totalAnswers >= 1 (we just saved one)")
        if data["entries"]:
            entry = data["entries"][-1]
            check("id" in entry, "entry has id")
            check("question" in entry, "entry has question")
            check("category" in entry, "entry has category")
            check("selfRating" in entry, "entry has selfRating")
            check("elapsedSeconds" in entry, "entry has elapsedSeconds")
            check("wordCount" in entry, "entry has wordCount")

    # === Test 10: get_streak_data ===
    print("\n=== get_streak_data ===")
    result = api.get_streak_data()
    check(result["success"] is True, "get_streak_data succeeds")
    if result["success"]:
        data = result["data"]
        check("todayCount" in data, "result has todayCount")
        check("weekCount" in data, "result has weekCount")
        check("dailyGoal" in data, "result has dailyGoal")
        check("weeklyGoal" in data, "result has weeklyGoal")
        check("currentStreak" in data, "result has currentStreak")
        check("longestStreak" in data, "result has longestStreak")
        check("lastActiveDate" in data, "result has lastActiveDate")
        check(isinstance(data["todayCount"], int), "todayCount is int")
        check(isinstance(data["dailyGoal"], int), "dailyGoal is int")
        check(data["dailyGoal"] > 0, "dailyGoal is positive")

    # === Test 11: get_next_actions ===
    print("\n=== get_next_actions ===")
    result = api.get_next_actions()
    check(result["success"] is True, "get_next_actions succeeds")
    if result["success"]:
        data = result["data"]
        check(isinstance(data, list), "result is a list")
        # With the fixture workbook, there should be some actions
        if data:
            action = data[0]
            check("id" in action, "action has id")
            check("type" in action, "action has type")
            check("title" in action, "action has title")
            check("description" in action, "action has description")

    # === Test 12: export_report ===
    print("\n=== export_report ===")
    result = api.export_report({"type": "monthly"})
    check(result["success"] is True, "export_report succeeds with monthly type")
    if result["success"]:
        data = result["data"]
        check("content" in data, "result has content")
        check("filename" in data, "result has filename")
        check(isinstance(data["content"], str), "content is a string")
        check(len(data["filename"]) > 0, "filename is non-empty")

    # === Test 13: Response format consistency ===
    print("\n=== Response Format Consistency ===")
    methods_to_check = [
        ("analyze_job_description", {"jobDescription": "x" * 50}),
        ("generate_cover_letter", {"company": "C", "role": "R", "name": "N"}),
        ("generate_linkedin_message", {"messageType": "connection", "recipientName": "J", "company": "C", "yourName": "T"}),
        ("get_interview_questions", {}),
        ("get_streak_data", None),
        ("get_next_actions", None),
        ("get_interview_practice_history", None),
        ("export_report", {"type": "monthly"}),
    ]
    for method_name, payload in methods_to_check:
        method = getattr(api, method_name)
        if payload is None:
            result = method()
        else:
            result = method(payload)
        check("success" in result, f"{method_name} returns success field")
        check("error" in result or result.get("success") is True, f"{method_name} has error or success=True")

    # ================================================================
    # DEEP BEHAVIORAL TESTS
    # ================================================================

    # === Test 14: Job Analysis — real analyzer called, deterministic, JSON-safe ===
    print("\n=== Job Analysis Deep Tests ===")
    jd_text_2 = """
    We are looking for a Senior Python Developer with 5+ years of experience.
    Required skills: Python, Django, PostgreSQL, AWS, Docker, Kubernetes, Redis.
    You will be building scalable APIs and working with microservices.
    Competitive salary $120k-$160k. Remote-friendly. Great benefits.
    We value test-driven development and CI/CD practices.
    """
    result1 = api.analyze_job_description({"jobDescription": jd_text_2, "candidateSkills": ["Python", "AWS"]})
    result2 = api.analyze_job_description({"jobDescription": jd_text_2, "candidateSkills": ["Python", "AWS"]})
    check(result1["success"] is True, "job analysis succeeds")
    if result1["success"] and result2["success"]:
        d1, d2 = result1["data"], result2["data"]
        check(d1["fitScore"] == d2["fitScore"], "deterministic: same fitScore for same input")
        check(d1["seniority"] == d2["seniority"], "deterministic: same seniority")
        check(d1["salaryEstimate"] == d2["salaryEstimate"], "deterministic: same salaryEstimate")
        # salaryEstimate must be a string (JSON-safe), not a tuple
        check(isinstance(d1["salaryEstimate"], str), "salaryEstimate is string (JSON-safe, not tuple)")
        # Candidate skill matching
        matched = d1.get("matchedKeywords", [])
        check("Python" in matched or "python" in [m.lower() for m in matched], "candidate skill Python is matched")
        check("AWS" in matched or "aws" in [m.lower() for m in matched], "candidate skill AWS is matched")
        # Tech stack should contain real keywords from JD
        tech_lower = [t.lower() for t in d1.get("techStack", [])]
        check("python" in tech_lower, "techStack contains Python from JD")
        check("django" in tech_lower or "postgresql" in tech_lower, "techStack contains Django or PostgreSQL from JD")

    # Analyzer exception sanitization — pass a payload that won't crash but verify error format
    result = api.analyze_job_description({"jobDescription": "x" * 50, "candidateSkills": []})
    check(result["success"] is True, "analysis with no candidate skills still succeeds")

    # === Test 15: Cover Letter — no API key leak, offline mode, fallback mode ===
    print("\n=== Cover Letter Deep Tests ===")
    result = api.generate_cover_letter({
        "company": "TestCorp",
        "role": "Backend Engineer",
        "name": "Test User",
        "years": "5",
        "tone": "professional",
        "achievement": "Built scalable APIs",
    })
    check(result["success"] is True, "cover letter generation succeeds")
    if result["success"]:
        data = result["data"]
        content = data["content"]
        # API key must never appear in response
        check("sk-" not in content, "no API key in cover letter content")
        check("api_key" not in content.lower(), "no 'api_key' string in content")
        check("openai" not in content.lower(), "no 'openai' reference in content")
        # Without API key configured in test env, mode should be offline
        check(data["mode"] == "offline", "mode is offline when no API key configured")
        # Verify offline generator was actually used (content should contain company name)
        check("TestCorp" in content, "offline content contains company name")
        check("Test User" in content, "offline content contains user name")
        check("Backend Engineer" in content, "offline content contains role")
        # Word count should match content
        expected_wc = len(content.split())
        check(data["wordCount"] == expected_wc, "wordCount matches actual word count")

    # Verify mode is NOT 'ai' when no API key
    result2 = api.generate_cover_letter({
        "company": "Corp2",
        "role": "Dev2",
        "name": "User2",
        "tone": "concise",
    })
    if result2["success"]:
        check(result2["data"]["mode"] != "ai", "mode is not 'ai' without API key")
        check(result2["data"]["mode"] == "offline", "mode is explicitly 'offline'")

    # === Test 16: LinkedIn — type mapping, char limits, no truncation ===
    print("\n=== LinkedIn Deep Tests ===")
    type_map = api._LINKEDIN_TYPE_MAP
    # Verify all 5 frontend types are mapped
    check("connection" in type_map, "connection type in map")
    check("referral" in type_map, "referral type in map")
    check("recruiter" in type_map, "recruiter type in map")
    check("follow-up" in type_map, "follow-up type in map")
    check("informational" in type_map, "informational type in map")

    # Verify each type maps to a real Python template
    import linkedin_message_generator as lmg
    for fe_type, py_type in type_map.items():
        check(py_type in lmg.TEMPLATES, f"frontend type '{fe_type}' maps to valid Python template '{py_type}'")

    # Test each frontend type generates valid content
    for fe_type in type_map:
        result = api.generate_linkedin_message({
            "messageType": fe_type,
            "recipientName": "Jane Smith",
            "company": "TechCorp",
            "yourName": "Test User",
            "yourRole": "Engineer",
            "targetRole": "Senior Engineer",
            "highlight": "Built great things",
        })
        check(result["success"] is True, f"LinkedIn type '{fe_type}' generates successfully")
        if result["success"]:
            data = result["data"]
            check(data["messageType"] == fe_type, f"returned messageType matches '{fe_type}'")
            check(data["characterCount"] == len(data["content"]), f"characterCount matches content length for '{fe_type}'")
            # Character limit should match the Python template's limit
            py_type = type_map[fe_type]
            expected_limit = lmg.get_char_limit(py_type)
            check(data["characterLimit"] == expected_limit, f"characterLimit matches Python template for '{fe_type}'")
            # Content should not be truncated (should fit or be within reasonable length)
            check(len(data["content"]) <= data["characterLimit"] + 100, f"content not excessively long for '{fe_type}'")
            # Content should contain recipient first name
            check("Jane" in data["content"], f"content contains recipient first name for '{fe_type}'")

    # recruiter maps to Cold Connection — verify it doesn't use referral template
    result_recruiter = api.generate_linkedin_message({
        "messageType": "recruiter",
        "recipientName": "John Doe",
        "company": "Corp",
        "yourName": "Me",
        "targetRole": "Dev",
    })
    result_connection = api.generate_linkedin_message({
        "messageType": "connection",
        "recipientName": "John Doe",
        "company": "Corp",
        "yourName": "Me",
        "targetRole": "Dev",
    })
    if result_recruiter["success"] and result_connection["success"]:
        # Both use Cold Connection template so content should be similar
        check("John" in result_recruiter["data"]["content"], "recruiter content has recipient name")

    # === Test 17: Interview Practice — atomic write, temp isolation, corrupt JSON ===
    print("\n=== Interview Practice Deep Tests ===")
    # Test uses temp directory for interview_scores.json
    # Verify the test file is actually being used (not the real one)
    check(os.path.exists(scores_file), "interview_scores.json exists")
    with open(scores_file, "r", encoding="utf-8") as f:
        before_count = len(json.load(f))

    # Save a practice entry
    result = api.save_interview_practice({
        "questionId": "deep-test-1",
        "question": "Tell me about a time you led a team.",
        "category": "Behavioral",
        "answer": "I led a team of 5 engineers to deliver a critical project on time.",
        "elapsedSeconds": 95,
        "selfRating": 4,
        "notes": "Felt confident",
    })
    check(result["success"] is True, "save_interview_practice succeeds")
    with open(scores_file, "r", encoding="utf-8") as f:
        after_count = len(json.load(f))
    check(after_count == before_count + 1, "entry count incremented by exactly 1 (atomic write)")

    # Verify saved entry has correct fields
    with open(scores_file, "r", encoding="utf-8") as f:
        entries = json.load(f)
    last = entries[-1]
    check(last["self_rating"] == 4, "saved self_rating is correct")
    check(last["word_count"] == len("I led a team of 5 engineers to deliver a critical project on time.".split()), "saved word_count is accurate")
    check(last["question"] == "Tell me about a time you led a team.", "saved question matches")
    check("session_id" in last, "saved entry has session_id")
    check("date" in last, "saved entry has date")

    # Test corrupt JSON handling
    with open(scores_file, "w", encoding="utf-8") as f:
        f.write("{corrupt json content!!!")
    result = api.save_interview_practice({
        "questionId": "corrupt-test",
        "question": "Test corrupt",
        "category": "Technical",
        "answer": "Test answer",
        "selfRating": 3,
    })
    check(result["success"] is True, "save succeeds even with corrupt JSON (backup + start fresh)")
    # Verify corrupt backup was created
    check(os.path.exists(scores_file + ".corrupt_backup"), "corrupt JSON was backed up")
    # Clean up corrupt backup
    if os.path.exists(scores_file + ".corrupt_backup"):
        os.remove(scores_file + ".corrupt_backup")

    # === Test 18: Interview History — avg from real self_rating only ===
    print("\n=== Interview History Deep Tests ===")
    # Restore the file with known data for deterministic test
    test_entries = [
        {"question": "Q1", "category": "Behavioral (STAR)", "score": 4, "self_rating": 4, "elapsed_s": 60, "word_count": 50, "date": "2025-01-01T10:00:00", "note": "", "session_id": "s1"},
        {"question": "Q2", "category": "Technical / Problem Solving", "score": 3, "self_rating": 3, "elapsed_s": 90, "word_count": 80, "date": "2025-01-02T10:00:00", "note": "", "session_id": "s2"},
        {"question": "Q3", "category": "Behavioral (STAR)", "score": 5, "self_rating": 5, "elapsed_s": 45, "word_count": 30, "date": "2025-01-03T10:00:00", "note": "", "session_id": "s3"},
    ]
    with open(scores_file, "w", encoding="utf-8") as f:
        json.dump(test_entries, f)

    result = api.get_interview_practice_history()
    check(result["success"] is True, "history succeeds with known data")
    if result["success"]:
        data = result["data"]
        check(data["stats"]["totalAnswers"] == 3, "totalAnswers is 3")
        # avg should be (4+3+5)/3 = 4.0
        check(data["stats"]["avgScore"] == 4.0, "avgScore is (4+3+5)/3 = 4.0")
        # byCategory should have Behavioral avg (4+5)/2=4.5 and Technical avg 3.0
        check("Behavioral" in data["stats"]["byCategory"], "byCategory has Behavioral")
        check("Technical" in data["stats"]["byCategory"], "byCategory has Technical")
        check(data["stats"]["byCategory"]["Behavioral"] == 4.5, "Behavioral avg is (4+5)/2=4.5")
        check(data["stats"]["byCategory"]["Technical"] == 3.0, "Technical avg is 3.0")
        # Verify entries are normalized correctly
        check(len(data["entries"]) == 3, "3 entries returned")
        check(data["entries"][0]["selfRating"] == 4, "entry 0 selfRating is 4")
        check(data["entries"][1]["selfRating"] == 3, "entry 1 selfRating is 3")
        check(data["entries"][2]["selfRating"] == 5, "entry 2 selfRating is 5")
        # Verify no fake word count scores
        check(data["entries"][0]["wordCount"] == 50, "entry 0 wordCount is real (50)")
        check(data["entries"][1]["wordCount"] == 80, "entry 1 wordCount is real (80)")

    # === Test 19: Streak — date gap breaks streak, future dates ignored ===
    print("\n=== Streak Deep Tests ===")
    from datetime import date, timedelta
    from backend_bridge.services.streak_service import compute_streak_data, extract_app_dates

    today = date.today()
    yesterday = today - timedelta(days=1)
    two_days_ago = today - timedelta(days=2)
    future = today + timedelta(days=5)

    # Test: 3 consecutive days meeting daily_goal=1 -> streak=3 (yesterday back)
    dates = [two_days_ago, yesterday, today]
    result = compute_streak_data(app_dates=dates, daily_goal=1, weekly_goal=7)
    check(result["currentStreak"] == 3, "3 consecutive days -> streak=3")
    check(result["todayCount"] == 1, "todayCount=1")
    check(result["longestStreak"] == 3, "longestStreak=3")

    # Test: gap breaks streak
    dates_gap = [today - timedelta(days=10), yesterday, today]
    result_gap = compute_streak_data(app_dates=dates_gap, daily_goal=1, weekly_goal=7)
    check(result_gap["currentStreak"] == 2, "gap breaks streak -> currentStreak=2 (only yesterday+today)")
    check(result_gap["longestStreak"] == 2, "longestStreak=2 with gap")

    # Test: future dates are ignored
    dates_future = [yesterday, today, future]
    result_future = compute_streak_data(app_dates=dates_future, daily_goal=1, weekly_goal=7)
    check(result_future["todayCount"] == 1, "future dates don't inflate todayCount")
    check(result_future["currentStreak"] == 2, "future dates don't affect streak")

    # Test: same day multiple applications -> streak increments by 1 day only
    dates_same_day = [today, today, today]
    result_same = compute_streak_data(app_dates=dates_same_day, daily_goal=1, weekly_goal=7)
    check(result_same["currentStreak"] == 1, "same day multiple apps -> streak=1 (not 3)")
    check(result_same["todayCount"] == 3, "todayCount=3 for 3 apps same day")

    # Test: empty dates -> fallback to JSON
    result_empty = compute_streak_data(app_dates=[], daily_goal=5, weekly_goal=20, streak_json_path=None)
    check(result_empty["todayCount"] == 0, "empty dates -> todayCount=0")
    check(result_empty["currentStreak"] == 0, "empty dates -> currentStreak=0")

    # Test: extract_app_dates with various formats
    from datetime import datetime as _dt
    headers = ["Date Applied", "Company"]
    rows = [
        [today, "Corp1"],           # date object
        [_dt.combine(yesterday, _dt.min.time()), "Corp2"],  # datetime
        [today.isoformat(), "Corp3"],  # ISO string
        ["invalid date", "Corp4"],  # invalid string
        [None, "Corp5"],            # None
    ]
    extracted = extract_app_dates(headers, rows)
    check(len(extracted) == 3, "extract_app_dates gets 3 valid dates (date, datetime, ISO string)")
    check(today in extracted, "extracted includes today (date object)")
    check(yesterday in extracted, "extracted includes yesterday (datetime)")

    # === Test 20: Next Actions — duplicates, priority, excluded statuses ===
    print("\n=== Next Actions Deep Tests ===")
    from backend_bridge.services.action_service import generate_next_actions

    # Build test applications with known data
    test_apps = [
        {
            "id": "app-1", "company": "Alpha", "role": "Dev", "status": "Applied",
            "followUpDate": (today - timedelta(days=5)).isoformat(), "fitScore": 50,
            "appliedDate": (today - timedelta(days=20)).isoformat(), "salary": "", "notes": "",
        },
        {
            "id": "app-2", "company": "Beta", "role": "Eng", "status": "Offer",
            "followUpDate": "", "fitScore": 90, "appliedDate": today.isoformat(),
            "salary": "", "notes": "",
        },
        {
            "id": "app-3", "company": "Gamma", "role": "Lead", "status": "Rejected",
            "followUpDate": (today - timedelta(days=10)).isoformat(), "fitScore": 80,
            "appliedDate": (today - timedelta(days=30)).isoformat(), "salary": "100k", "notes": "good",
        },
        {
            "id": "app-4", "company": "Delta", "role": "Arch", "status": "Saved",
            "followUpDate": "", "fitScore": 85, "appliedDate": "",
            "salary": "", "notes": "",
        },
    ]
    test_rows = [
        ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "https://app1.com", "", "", ""],  # app-1 has URL
        ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],  # app-2 no URL
        ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],  # app-3
        ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],  # app-4
    ]
    test_headers = ["ID", "Company", "Role", "Status", "Date Applied", "Follow-up Date", "Fit Score",
                    "Salary", "Notes", "Application URL", "Interview Date"] + [""] * 10

    actions = generate_next_actions(test_apps, test_rows, test_headers)

    # Rejected (app-3) should NOT produce actions
    action_ids = [a["id"] for a in actions]
    check(not any("app-3" in aid for aid in action_ids), "Rejected app produces no actions")

    # app-1: overdue follow-up (Applied, followUp 5 days ago) + stale (20 days)
    check(any("app-1-overdue-fu" in aid for aid in action_ids), "app-1 has overdue follow-up action")
    check(any("app-1-stale" in aid for aid in action_ids), "app-1 has stale action")

    # app-2: Offer missing salary+notes
    check(any("app-2-offer-incomplete" in aid for aid in action_ids), "app-2 has offer-incomplete action")

    # app-4: Saved with high fit score
    check(any("app-4-saved-high-fit" in aid for aid in action_ids), "app-4 has saved-high-fit action")

    # No duplicate action IDs
    check(len(action_ids) == len(set(action_ids)), "no duplicate action IDs")

    # Priority ordering: high before medium before low
    priorities = [a["priority"] for a in actions]
    check(priorities == sorted(priorities, key=lambda p: {"high": 0, "medium": 1, "low": 2}[p]),
          "actions sorted by priority (high -> medium -> low)")

    # Max 10 actions
    check(len(actions) <= 10, "at most 10 actions returned")

    # === Test 21: Next Actions — missing/corrupt dates don't crash ===
    print("\n=== Next Actions Edge Cases ===")
    edge_apps = [
        {
            "id": "edge-1", "company": "Edge", "role": "Dev", "status": "Applied",
            "followUpDate": "not-a-date", "fitScore": 50,
            "appliedDate": "also-not-a-date", "salary": "", "notes": "",
        },
        {
            "id": "edge-2", "company": "Edge2", "role": "Dev2", "status": "Applied",
            "followUpDate": "", "fitScore": 0,
            "appliedDate": "", "salary": "", "notes": "",
        },
    ]
    edge_rows = [[""], [""]]
    edge_headers = ["ID", "Company"]
    try:
        edge_actions = generate_next_actions(edge_apps, edge_rows, edge_headers)
        check(True, "corrupt dates don't crash generate_next_actions")
        check(isinstance(edge_actions, list), "returns a list even with corrupt dates")
    except Exception as e:
        check(False, f"corrupt dates crash: {e}")

    # === Test 22: Export Report — real data, no path leak ===
    print("\n=== Export Report Deep Tests ===")
    result = api.export_report({"type": "monthly"})
    check(result["success"] is True, "export_report succeeds")
    if result["success"]:
        data = result["data"]
        content = data["content"]
        # No local file paths in content
        check("C:\\" not in content, "no Windows path in report content")
        check(_project_root not in content, "no project root path in report content")
        # Should contain real stats
        check("Total Applications:" in content, "report has Total Applications")
        check("Active:" in content, "report has Active count")
        check("Response Rate:" in content, "report has Response Rate")
        # Filename should be descriptive
        check("report_monthly_" in data["filename"], "filename contains 'report_monthly_'")
        check(data["filename"].endswith(".txt"), "filename ends with .txt")

    # === Regression: Error sanitization in read/write methods (BUG 1) ===
    print("\n=== Error Sanitization Regression (BUG 1) ===")
    # Point API to a non-existent workbook to force exceptions in read methods
    bad_api = ExcelBridgeAPI(workbook_path=os.path.join(tempfile.gettempdir(), "nonexistent_bad_path.xlsx"))
    # get_applications should return sanitized error, not raw path
    res = bad_api.get_applications()
    check("nonexistent_bad_path" not in str(res.get("error", "")),
          "get_applications error does not leak file path")
    check(res.get("error") is not None, "get_applications returns error for missing workbook")
    # get_dashboard
    res = bad_api.get_dashboard()
    check("nonexistent_bad_path" not in str(res.get("error", "")),
          "get_dashboard error does not leak file path")
    # get_kpis
    res = bad_api.get_kpis()
    check("nonexistent_bad_path" not in str(res.get("error", "")),
          "get_kpis error does not leak file path")
    # get_pipeline
    res = bad_api.get_pipeline()
    check("nonexistent_bad_path" not in str(res.get("error", "")),
          "get_pipeline error does not leak file path")
    # get_salary_data
    res = bad_api.get_salary_data()
    check("nonexistent_bad_path" not in str(res.get("error", "")),
          "get_salary_data error does not leak file path")
    # get_write_mode
    res = bad_api.get_write_mode()
    check("nonexistent_bad_path" not in str(res.get("reason", "")),
          "get_write_mode reason does not leak file path")

    # === Regression: interview_prep.py save_score atomic write (BUG 2) ===
    print("\n=== Atomic save_score Regression (BUG 2) ===")
    import interview_prep as ip
    # Monkeypatch SCORES_FILE to temp dir for isolation
    orig_scores_file = ip.SCORES_FILE
    ip.SCORES_FILE = os.path.join(data_dir, "interview_scores_ip.json")
    test_entry = {
        "question": "Test question?",
        "category": "Behavioral (STAR)",
        "score": 4,
        "elapsed_s": 30.0,
        "session_id": "test_regression",
        "date": "2026-01-01T00:00:00",
        "word_count": 50,
        "self_rating": 4,
    }
    try:
        ip.save_score(test_entry)
        reloaded = ip.load_scores()
        check(isinstance(reloaded, list), "save_score produces valid JSON list")
        check(len(reloaded) == 1, "save_score appends exactly one entry")
        check(reloaded[-1].get("question") == "Test question?", "saved entry has correct question")
    finally:
        ip.SCORES_FILE = orig_scores_file

    # === Cleanup ===
    print("\n=== Cleanup ===")

    # Verify real JSON files were not modified
    print("\n=== JSON Isolation Verification ===")
    for f, hash_before in hashes_before.items():
        if os.path.exists(f):
            with open(f, "rb") as fh:
                hash_after = hashlib.sha256(fh.read()).hexdigest()
            check(hash_before == hash_after, f"{os.path.basename(f)} SHA256 unchanged")

    tmpdir.cleanup()

    # Print summary
    print(f"\n{'='*50}")
    print(f"Results: {PASS_COUNT} passed, {ERROR_COUNT} failed")
    print(f"{'='*50}")
    return ERROR_COUNT == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
