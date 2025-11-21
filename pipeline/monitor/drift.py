import pandas as pd
import numpy as np
from scipy.stats import ks_2samp
import json


def psi(expected, actual, buckets=10):
    """Population Stability Index (PSI) with smoothing to avoid divide-by-zero."""
    expected_counts, bin_edges = np.histogram(expected, bins=buckets)
    actual_counts, _ = np.histogram(actual, bins=bin_edges)

    # Add smoothing to avoid zeros
    expected_percents = (expected_counts + 1e-6) / (len(expected) + 1e-6)
    actual_percents = (actual_counts + 1e-6) / (len(actual) + 1e-6)

    psi_value = np.sum(
        (expected_percents - actual_percents)
        * np.log((expected_percents / actual_percents) + 1e-6)
    )
    return psi_value


def detect_drift(reference_df: pd.DataFrame,
                 current_df: pd.DataFrame,
                 save_path="drift_report.json"):

    drift_report = {}
    numeric_cols = reference_df.select_dtypes(include=[np.number]).columns

    for col in numeric_cols:
        ref = reference_df[col].dropna()
        cur = current_df[col].dropna()

        if len(ref) > 0 and len(cur) > 0:
            ks_stat, ks_pvalue = ks_2samp(ref, cur)
            psi_value = psi(ref, cur)

            drift_detected = (ks_pvalue < 0.05) or (psi_value > 0.1)

            drift_report[col] = {
                "ks_stat": float(ks_stat),
                "ks_pvalue": float(ks_pvalue),
                "psi": float(psi_value),
                "drift_detected": bool(drift_detected)
            }

    # Convert all numpy types → python native for JSON
    clean_report = json.loads(json.dumps(drift_report, default=lambda x: float(x) if isinstance(x, np.number) else bool(x)))

    # Save JSON
    with open(save_path, "w") as f:
        json.dump(clean_report, f, indent=4)

    print(f"Drift report saved to {save_path}")

    return clean_report
