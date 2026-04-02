# run_tests.py - Run tests from the project root
import sys
import os
from pathlib import Path

# Ensure project root is on sys.path
root = Path(__file__).parent.resolve()
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

import pytest

exit_code = pytest.main([
    "tests/personality",
    "tests/memory",
    "-v",
    "--tb=short",
    "-p", "no:cacheprovider"
])
sys.exit(exit_code)
