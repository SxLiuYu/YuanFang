# conftest.py
import sys
import os
from pathlib import Path

# Ensure project root is on sys.path
root = Path(__file__).parent
sys.path = [str(root)] + [p for p in sys.path if str(root.resolve()) != os.path.normpath(p)]
