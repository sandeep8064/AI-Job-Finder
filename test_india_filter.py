
import sys
import os
sys.path.append(os.getcwd())

from main import is_in_india

test_cases = [
    ("Bangalore, India", True),
    ("Noida, Uttar Pradesh", True),
    ("New York, USA", False),
    ("London, UK", False),
    ("Hyderabad", True),
    ("Remote", True),
    ("Pune / Maharashtra", True),
    ("Singapore", False),
    ("", True),
]

print("Testing is_in_india logic:")
for loc, expected in test_cases:
    result = is_in_india(loc)
    print(f"'{loc}' -> {result} (Expected: {expected})")
    assert result == expected
print("All tests passed!")
