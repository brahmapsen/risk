# test_drift.py
from pipeline.monitor.drift import detect_drift
import pandas as pd

ref = pd.DataFrame({"a": [1, 2, 3, 4, 5]})
cur = pd.DataFrame({"a": [10, 11, 12, 13, 14]})

detect_drift(ref, cur, "test_drift_report.html")
