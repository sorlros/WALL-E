import sys
import os

print(f"CWD: {os.getcwd()}")
print(f"Path: {sys.path}")

try:
    from backend.api import missions
    print("SUCCESS: backend.api.missions imported")
except ImportError as e:
    print(f"ERROR: {e}")
except Exception as e:
    print(f"EXCEPTION: {e}")
