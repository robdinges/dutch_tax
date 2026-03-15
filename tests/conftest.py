"""Pytest configuration: voeg de projectroot toe aan het zoekpad zodat
test-modules de applicatiecode kunnen importeren vanuit de bovenliggende map."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
