"""Test that _find_tracker() works when launcher.py is inside 07_Scripts/"""
import os, sys

TRACKER_NAME = "Developer_Job_Application_Tracker_PRO.xlsx"

def _find_tracker(BASE_DIR):
    candidates = [
        os.path.join(BASE_DIR, TRACKER_NAME),
        os.path.join(BASE_DIR, "..", TRACKER_NAME),
        os.path.join(BASE_DIR, "..", "..", TRACKER_NAME),
        os.path.join(BASE_DIR, "..", "01_Main_Product", TRACKER_NAME),
        os.path.join(BASE_DIR, "..", "..", "01_Main_Product", TRACKER_NAME),
    ]
    for p in candidates:
        p = os.path.normpath(p)
        if os.path.exists(p):
            return p
    root = os.path.normpath(os.path.join(BASE_DIR, "..", ".."))
    for dirpath, _, files in os.walk(root):
        if TRACKER_NAME in files:
            return os.path.join(dirpath, TRACKER_NAME)
    return None

# Simulate ZIP extraction: launcher.py is in 07_Scripts/
# Real tracker is in releases/<latest>/01_Main_Product/

import glob
zips = sorted(glob.glob(r"c:/Users/erkay/Desktop/önemli/releases/*.zip"))
if zips:
    print(f"Latest ZIP: {zips[-1]}")

# Simulate from 07_Scripts
fake_07 = r"c:/Users/erkay/Desktop/Yeni klasor (14)/07_Scripts"
result = _find_tracker(fake_07)
print(f"\nSimulated from 07_Scripts:")
print(f"  BASE_DIR = {fake_07}")
print(f"  Found tracker: {result}")
print(f"  Exists: {os.path.exists(result) if result else False}")

# Real case: running from project root
real_base = r"c:/Users/erkay/Desktop/önemli"
result2 = _find_tracker(real_base)
print(f"\nFrom project root:")
print(f"  Found: {result2}")
print(f"  Exists: {os.path.exists(result2) if result2 else False}")
