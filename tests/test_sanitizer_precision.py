"""
Error Sanitizer Precision Tests — Checkpoint 1 Final Validation

Tests _sanitize_error() for:
  - Correct removal of secrets, paths, tracebacks
  - Preservation of normal user messages containing "password", "secret", "token"
  - Multiline traceback cleanup
  - All secret patterns: API key, password=, secret=, token=, apikey=, Bearer, URL query
"""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend_bridge.api import ExcelBridgeAPI

PASS_COUNT = 0
FAIL_COUNT = 0


def check(condition: bool, label: str):
    global PASS_COUNT, FAIL_COUNT
    if condition:
        PASS_COUNT += 1
        print(f"  PASS: {label}")
    else:
        FAIL_COUNT += 1
        print(f"  FAIL: {label}")


def sanitize(msg: str) -> str:
    return ExcelBridgeAPI._sanitize_error(Exception(msg))


def main():
    global PASS_COUNT, FAIL_COUNT

    print("=" * 70)
    print("ERROR SANITIZER PRECISION TESTS")
    print("=" * 70)

    # ── Secret removal tests ──────────────────────────────────────────────
    print("\n=== Secret Removal ===")

    # Windows path
    r = sanitize("Error reading C:\\Users\\erkay\\Desktop\\file.xlsx")
    check("C:\\Users" not in r, f"Windows path removed: {r}")
    check("erkay" not in r, f"Username not leaked: {r}")

    # Unix path
    r = sanitize("Error reading /home/user/secret/config.json")
    check("/home/user" not in r, f"Unix path removed: {r}")

    # API key (20+ chars)
    r = sanitize("Request failed with sk-1234567890abcdefghijklmnopqrstuv")
    check("sk-1234567890" not in r, f"API key removed: {r}")
    check("[redacted]" in r, f"API key replaced: {r}")

    # password=value
    r = sanitize("Connection failed: password=secret123")
    check("secret123" not in r, f"password= value removed: {r}")
    check("password=[redacted]" in r, f"password= replaced: {r}")

    # secret=value
    r = sanitize("Config error: secret=my_super_secret_value")
    check("my_super_secret_value" not in r, f"secret= value removed: {r}")

    # token=value
    r = sanitize("Auth failed: token=abc123def456")
    check("abc123def456" not in r, f"token= value removed: {r}")

    # apikey=value
    r = sanitize("API error: apikey=xyz789")
    check("xyz789" not in r, f"apikey= value removed: {r}")

    # api_key=value
    r = sanitize("Error: api_key=AKIAIOSFODNN7EXAMPLE")
    check("AKIAIOSFODNN7EXAMPLE" not in r, f"api_key= value removed: {r}")

    # Authorization: Bearer
    r = sanitize("Request rejected: Authorization: Bearer eyJhbGciOiJIUzI1NiJ9")
    check("eyJhbGciOiJIUzI1NiJ9" not in r, f"Bearer token removed: {r}")

    # URL query token
    r = sanitize("Redirect to https://api.example.com?token=secret_token_123")
    check("secret_token_123" not in r, f"URL query token removed: {r}")

    # Environment variable
    r = sanitize("Config loaded from JOBTRACKER_WRITE_MODE=production")
    check("JOBTRACKER_WRITE_MODE" not in r, f"Env var removed: {r}")
    check("[env-var]" in r, f"Env var replaced: {r}")

    # ── Normal message preservation tests ────────────────────────────────
    print("\n=== Normal Message Preservation ===")

    # "Password field is required" should NOT be mangled
    r = sanitize("Password field is required")
    check("Password field is required" == r or "Password" in r,
          f"'Password field is required' preserved: {r}")
    check("field" in r, f"'field' word preserved: {r}")

    # "Secret question not set" should NOT be mangled
    r = sanitize("Secret question not set")
    check("Secret question not set" == r or "Secret" in r,
          f"'Secret question not set' preserved: {r}")
    check("question" in r, f"'question' word preserved: {r}")

    # "Token expired" should NOT lose "expired"
    r = sanitize("Token expired")
    check("expired" in r, f"'Token expired' preserves 'expired': {r}")

    # "Please enter your password" should not be mangled
    r = sanitize("Please enter your password")
    check("Please enter your password" == r,
          f"'Please enter your password' preserved: {r}")

    # ── Multiline traceback ──────────────────────────────────────────────
    print("\n=== Multiline Traceback ===")

    traceback_msg = """Traceback (most recent call last):
  File "C:\\Users\\erkay\\app.py", line 42, in <module>
    result = do_something()
  File "C:\\Users\\erkay\\lib.py", line 15, in do_something
    raise ValueError("Invalid input")
ValueError: Invalid input"""

    r = sanitize(traceback_msg)
    check("Traceback" not in r, f"Traceback text removed: {r[:80]}")
    check("C:\\Users" not in r, f"Path in traceback removed: {r[:80]}")
    check("erkay" not in r, f"Username in traceback removed: {r[:80]}")
    check("app.py" not in r, f"Source file in traceback removed: {r[:80]}")
    check("ValueError: Invalid input" in r or "[traceback]" in r,
          f"Error type preserved or replaced: {r[:80]}")

    # ── Combined scenarios ───────────────────────────────────────────────
    print("\n=== Combined Scenarios ===")

    # Path + secret + traceback
    combined = """Traceback (most recent call last):
  File "C:\\Users\\secret\\app.py", line 10
KeyError: 'password=abc123'"""
    r = sanitize(combined)
    check("C:\\Users" not in r, f"Combined: path removed: {r[:80]}")
    check("abc123" not in r, f"Combined: secret removed: {r[:80]}")
    check("Traceback" not in r, f"Combined: traceback removed: {r[:80]}")

    # Email address (should not be mangled — not a secret pattern)
    r = sanitize("Notification sent to user@example.com")
    check("user@example.com" in r, f"Email preserved (not a secret): {r}")

    # ── Edge cases ───────────────────────────────────────────────────────
    print("\n=== Edge Cases ===")

    # Empty string
    r = sanitize("")
    check(r == "An unexpected error occurred", f"Empty string returns fallback: {r}")

    # Only whitespace
    r = sanitize("   ")
    check(r == "An unexpected error occurred", f"Whitespace returns fallback: {r}")

    # Very long message
    r = sanitize("x" * 500)
    check(len(r) <= 203, f"Long message truncated ({len(r)} chars)")
    check(r.endswith("..."), f"Long message ends with ...")

    # Unicode message
    r = sanitize("Türkçe hata mesajı: dosya bulunamadı")
    check("Türkçe" in r, f"Unicode preserved: {r}")

    # ── Summary ───────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print(f"SANITIZER PRECISION TEST SUMMARY: {PASS_COUNT} PASS, {FAIL_COUNT} FAIL")
    print("=" * 70)

    if FAIL_COUNT > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
