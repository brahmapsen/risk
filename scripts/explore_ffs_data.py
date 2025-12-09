"""
Comprehensive data exploration script for FFS Claims Database.
Analyzes the database structure, data quality, and identifies potential features
for readmission risk prediction.
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import warnings

warnings.filterwarnings("ignore")

DB_PATH = "data/sas_table_subset_copy.db"


def get_table_info(conn):
    """Get basic table information."""
    cursor = conn.cursor()
    
    # Get table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    print("=" * 80)
    print("DATABASE OVERVIEW")
    print("=" * 80)
    print(f"Tables: {tables}")
    print()
    
    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {tables[0]}")
    row_count = cursor.fetchone()[0]
    print(f"Total Rows: {row_count:,}")
    
    # Get column count
    cursor.execute(f"PRAGMA table_info({tables[0]})")
    columns = cursor.fetchall()
    print(f"Total Columns: {len(columns)}")
    print()
    
    return tables[0], columns


def analyze_missing_values(conn, table_name, sample_size=100000):
    """Analyze missing values in key columns."""
    print("=" * 80)
    print("MISSING VALUE ANALYSIS")
    print("=" * 80)
    
    # Key columns to analyze
    key_columns = [
        'C_HDR_MBR_AGE', 'C_HDR_MBR_GENDER_CD', 'IPSTAY_ID', 'IPSTAY_LOS',
        'C_HDR_ADMIT_DT', 'C_HDR_DISCH_DT', 'C_HDR_DIAG_PRIM_CD',
        'C_HDR_DRG_CD', 'BILL_AMT', 'PAID_AMT', 'IPSTAY_ID_PRIOR',
        'C_HDR_MBR_SYS_ID', 'C_HDR_TCN_ID'
    ]
    
    # Sample data for faster analysis
    query = f"""
    SELECT {', '.join(key_columns)} 
    FROM {table_name} 
    LIMIT {sample_size}
    """
    
    df = pd.read_sql_query(query, conn)
    
    missing_stats = []
    for col in key_columns:
        if col in df.columns:
            null_count = df[col].isna().sum()
            null_pct = (null_count / len(df)) * 100
            missing_stats.append({
                'Column': col,
                'Missing Count': null_count,
                'Missing %': f"{null_pct:.2f}%",
                'Non-Null Count': len(df) - null_count
            })
    
    missing_df = pd.DataFrame(missing_stats)
    print(missing_df.to_string(index=False))
    print()
    
    return df


def analyze_temporal_features(conn, table_name):
    """Analyze temporal patterns (admission dates, discharge dates, readmissions)."""
    print("=" * 80)
    print("TEMPORAL ANALYSIS (Readmission Patterns)")
    print("=" * 80)
    
    # Check date columns
    query = f"""
    SELECT 
        COUNT(*) as total_records,
        COUNT(DISTINCT IPSTAY_ID) as unique_stays,
        COUNT(DISTINCT C_HDR_MBR_SYS_ID) as unique_members,
        MIN(C_HDR_ADMIT_DT) as min_admit_date,
        MAX(C_HDR_ADMIT_DT) as max_admit_date,
        MIN(IPSTAY_BEG_DT) as min_stay_beg,
        MAX(IPSTAY_END_DT) as max_stay_end
    FROM {table_name}
    WHERE IPSTAY_ID IS NOT NULL
    """
    
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchone()
    
    print(f"Total Records: {result[0]:,}")
    print(f"Unique Inpatient Stays: {result[1]:,}")
    print(f"Unique Members: {result[2]:,}")
    print(f"Admit Date Range: {result[3]} to {result[4]}")
    print(f"Stay Date Range: {result[5]} to {result[6]}")
    print()
    
    # Analyze readmission patterns (stays with prior stays)
    query = f"""
    SELECT 
        COUNT(DISTINCT IPSTAY_ID) as stays_with_prior,
        COUNT(DISTINCT CASE WHEN IPSTAY_ID_PRIOR IS NOT NULL THEN IPSTAY_ID END) as readmissions
    FROM {table_name}
    WHERE IPSTAY_ID IS NOT NULL
    """
    
    cursor.execute(query)
    result = cursor.fetchone()
    print(f"Stays with Prior Stay ID: {result[0]:,}")
    print(f"Potential Readmissions: {result[1]:,}")
    print()


def analyze_clinical_features(conn, table_name, sample_size=100000):
    """Analyze clinical features (diagnoses, DRG, procedures)."""
    print("=" * 80)
    print("CLINICAL FEATURE ANALYSIS")
    print("=" * 80)
    
    # Sample data
    query = f"""
    SELECT 
        C_HDR_DIAG_PRIM_CD,
        C_HDR_DRG_CD,
        C_HDR_DRG_CD_DESC,
        C_HDR_DIAG_1_CD,
        C_HDR_DIAG_2_CD,
        C_HDR_DIAG_3_CD,
        C_DTL_PROC_CD,
        IPSTAY_LOS,
        C_HDR_MBR_AGE,
        C_HDR_MBR_GENDER_CD
    FROM {table_name}
    WHERE IPSTAY_ID IS NOT NULL
    LIMIT {sample_size}
    """
    
    df = pd.read_sql_query(query, conn)
    
    print(f"Sample Size: {len(df):,} records")
    print()
    
    # Primary diagnosis distribution
    if 'C_HDR_DIAG_PRIM_CD' in df.columns:
        print("Top 10 Primary Diagnoses:")
        diag_counts = df['C_HDR_DIAG_PRIM_CD'].value_counts().head(10)
        for diag, count in diag_counts.items():
            print(f"  {diag}: {count:,} ({count/len(df)*100:.2f}%)")
        print()
    
    # DRG distribution
    if 'C_HDR_DRG_CD' in df.columns:
        print("Top 10 DRG Codes:")
        drg_counts = df['C_HDR_DRG_CD'].value_counts().head(10)
        for drg, count in drg_counts.items():
            print(f"  {drg}: {count:,} ({count/len(df)*100:.2f}%)")
        print()
    
    # Length of stay statistics
    if 'IPSTAY_LOS' in df.columns:
        los_data = df['IPSTAY_LOS'].dropna()
        print("Length of Stay Statistics:")
        print(f"  Mean: {los_data.mean():.2f} days")
        print(f"  Median: {los_data.median():.2f} days")
        print(f"  Std Dev: {los_data.std():.2f} days")
        print(f"  Min: {los_data.min():.0f} days")
        print(f"  Max: {los_data.max():.0f} days")
        print()
    
    # Age distribution
    if 'C_HDR_MBR_AGE' in df.columns:
        age_data = df['C_HDR_MBR_AGE'].dropna()
        age_data = age_data[(age_data >= 0) & (age_data <= 120)]  # Filter outliers
        print("Age Statistics (filtered 0-120):")
        print(f"  Mean: {age_data.mean():.1f} years")
        print(f"  Median: {age_data.median():.1f} years")
        print(f"  Min: {age_data.min():.0f} years")
        print(f"  Max: {age_data.max():.0f} years")
        print()
    
    return df


def analyze_financial_features(conn, table_name, sample_size=100000):
    """Analyze financial features."""
    print("=" * 80)
    print("FINANCIAL FEATURE ANALYSIS")
    print("=" * 80)
    
    query = f"""
    SELECT 
        BILL_AMT,
        PAID_AMT,
        ALLOW_AMT,
        TOT_REIMB_AMT,
        IPSTAY_TOTAL_PAID
    FROM {table_name}
    WHERE IPSTAY_ID IS NOT NULL
    LIMIT {sample_size}
    """
    
    df = pd.read_sql_query(query, conn)
    
    financial_cols = ['BILL_AMT', 'PAID_AMT', 'ALLOW_AMT', 'TOT_REIMB_AMT', 'IPSTAY_TOTAL_PAID']
    
    for col in financial_cols:
        if col in df.columns:
            data = df[col].dropna()
            if len(data) > 0:
                print(f"{col}:")
                print(f"  Mean: ${data.mean():,.2f}")
                print(f"  Median: ${data.median():,.2f}")
                print(f"  Min: ${data.min():,.2f}")
                print(f"  Max: ${data.max():,.2f}")
                print()


def suggest_features_for_readmission():
    """Suggest potential features for readmission risk prediction."""
    print("=" * 80)
    print("SUGGESTED FEATURES FOR READMISSION RISK PREDICTION")
    print("=" * 80)
    
    feature_categories = {
        "Demographic Features": [
            "age (C_HDR_MBR_AGE)",
            "gender (C_HDR_MBR_GENDER_CD)",
            "race (C_HDR_MBR_RACE_CD)",
            "age_group (derived: 0-18, 19-35, 36-50, 51-65, 65+)"
        ],
        "Clinical Features": [
            "primary_diagnosis (C_HDR_DIAG_PRIM_CD) - encode as categorical",
            "primary_diagnosis_category (first 3 chars of ICD-10 code)",
            "number_of_diagnoses (count non-null C_HDR_DIAG_*_CD)",
            "DRG_code (C_HDR_DRG_CD)",
            "DRG_weight (R_CD_REL_WT_AMT)",
            "admission_type (C_HDR_ADMIT_TYP_CD)",
            "admission_source (derived from codes)"
        ],
        "Stay Characteristics": [
            "length_of_stay (IPSTAY_LOS)",
            "discharge_disposition (C_HDR_PMT_TY_CD)",
            "claim_status (C_HDR_CLM_STAT_CD)",
            "number_of_claims_per_stay (IPSTAY_NUM_CLAIMS)"
        ],
        "Historical Features": [
            "has_prior_stay (1 if IPSTAY_ID_PRIOR IS NOT NULL, else 0)",
            "prior_stay_count (count of prior stays per member)",
            "days_since_last_stay (if prior stay exists)",
            "total_historical_stays (count all stays per member)",
            "avg_historical_los (average LOS across all prior stays)"
        ],
        "Financial Features": [
            "total_paid_amount (IPSTAY_TOTAL_PAID)",
            "bill_amount (BILL_AMT)",
            "paid_amount (PAID_AMT)",
            "cost_per_day (total_paid / LOS)",
            "reimbursement_ratio (PAID_AMT / BILL_AMT)"
        ],
        "Provider Features": [
            "billing_provider_specialty (C_HDR_BLNG_SPECL_CD)",
            "rendering_provider_specialty (RNDR_SPECL_CD)",
            "provider_experience (count of claims per provider)"
        ],
        "Temporal Features": [
            "admission_month (extract from C_HDR_ADMIT_DT)",
            "admission_day_of_week",
            "season (Q1, Q2, Q3, Q4)",
            "days_since_first_stay (for member)"
        ],
        "Exception/Quality Features": [
            "has_exception_codes (1 if any EXC_CD_* is not null)",
            "exception_code_count (count of non-null exception codes)",
            "duplicate_claim_flag (EXC_CD_H_1 = '0102')"
        ]
    }
    
    for category, features in feature_categories.items():
        print(f"\n{category}:")
        for feature in features:
            print(f"  • {feature}")
    
    print("\n" + "=" * 80)
    print("FEATURE ENGINEERING RECOMMENDATIONS")
    print("=" * 80)
    print("""
1. CREATE MEMBER-LEVEL AGGREGATIONS:
   - Group by C_HDR_MBR_SYS_ID to create member-level features
   - Calculate historical readmission rates per member
   - Aggregate stay-level features to member level

2. CREATE STAY-LEVEL FEATURES:
   - Group by IPSTAY_ID to aggregate claim-level data
   - Calculate total costs, number of claims, procedures per stay

3. TEMPORAL FEATURES:
   - Calculate time between stays (readmission window: 30 days)
   - Create sequence features (first stay, second stay, etc.)

4. ENCODING STRATEGIES:
   - One-hot encode top N diagnosis codes (e.g., top 50)
   - Target encode rare diagnosis codes
   - Embed DRG codes (or use as categorical)

5. HANDLE MISSING VALUES:
   - Impute missing ages with median
   - Create "missing" category for categorical features
   - Use 0 for missing financial amounts

6. TARGET VARIABLE:
   - Create readmitted_30d flag: 1 if next stay within 30 days of discharge
   - Use IPSTAY_END_DT and next IPSTAY_BEG_DT to calculate
   - Consider 60-day and 90-day readmissions as alternative targets
    """)


def main():
    """Main exploration function."""
    print("\n" + "=" * 80)
    print("FFS CLAIMS DATABASE EXPLORATION")
    print("=" * 80)
    print(f"Database: {DB_PATH}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if not Path(DB_PATH).exists():
        print(f"ERROR: Database file not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # 1. Basic table info
        table_name, columns = get_table_info(conn)
        
        # 2. Missing value analysis
        df_sample = analyze_missing_values(conn, table_name)
        
        # 3. Temporal analysis
        analyze_temporal_features(conn, table_name)
        
        # 4. Clinical features
        clinical_df = analyze_clinical_features(conn, table_name)
        
        # 5. Financial features
        analyze_financial_features(conn, table_name)
        
        # 6. Feature suggestions
        suggest_features_for_readmission()
        
        print("\n" + "=" * 80)
        print("EXPLORATION COMPLETE")
        print("=" * 80)
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print("Next Steps:")
        print("1. Review the feature suggestions above")
        print("2. Create a feature extraction script (see scripts/extract_ffs_features.py)")
        print("3. Build member-level and stay-level aggregations")
        print("4. Create target variable (30-day readmission flag)")
        print("5. Train model with new features")
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()

