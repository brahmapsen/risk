"""
Feature extraction script for FFS Claims Database.
Transforms claim-level data into member-level and stay-level features
for readmission risk prediction.
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings("ignore")

DB_PATH = "data/sas_table_subset_copy.db"
OUTPUT_PATH = "data/ffs_features.csv"


def extract_stay_level_features(conn):
    """
    Extract features at the inpatient stay level.
    Groups claim-level data by IPSTAY_ID.
    """
    print("Extracting stay-level features...")
    
    query = """
    SELECT 
        IPSTAY_ID,
        C_HDR_MBR_SYS_ID as member_id,
        MIN(C_HDR_ADMIT_DT) as admit_date,
        MAX(C_HDR_DISCH_DT) as discharge_date,
        MAX(IPSTAY_BEG_DT) as stay_beg_date,
        MAX(IPSTAY_END_DT) as stay_end_date,
        MAX(IPSTAY_LOS) as length_of_stay,
        MAX(C_HDR_MBR_AGE) as age,
        MAX(C_HDR_MBR_GENDER_CD) as gender,
        MAX(C_HDR_MBR_RACE_CD) as race,
        MAX(C_HDR_DIAG_PRIM_CD) as primary_diagnosis,
        MAX(C_HDR_DRG_CD) as drg_code,
        MAX(C_HDR_DRG_CD_DESC) as drg_description,
        MAX(R_CD_REL_WT_AMT) as drg_weight,
        MAX(C_HDR_ADMIT_TYP_CD) as admission_type,
        MAX(C_HDR_ADMIT_TYP_CD_DESC) as admission_type_desc,
        MAX(C_HDR_PMT_TY_CD) as payment_type,
        MAX(C_HDR_PMT_TY_CD_DESC) as payment_type_desc,
        MAX(C_HDR_CLM_STAT_CD) as claim_status,
        MAX(IPSTAY_ID_PRIOR) as prior_stay_id,
        MAX(IPSTAY_NUM_CLAIMS) as num_claims,
        SUM(BILL_AMT) as total_bill_amount,
        SUM(PAID_AMT) as total_paid_amount,
        SUM(ALLOW_AMT) as total_allowed_amount,
        MAX(IPSTAY_TOTAL_PAID) as stay_total_paid,
        COUNT(*) as claim_line_count,
        -- Count number of diagnoses
        COUNT(DISTINCT C_HDR_DIAG_PRIM_CD) + 
        COUNT(DISTINCT C_HDR_DIAG_1_CD) +
        COUNT(DISTINCT C_HDR_DIAG_2_CD) +
        COUNT(DISTINCT C_HDR_DIAG_3_CD) as num_diagnoses,
        -- Exception codes
        MAX(CASE WHEN EXC_CD_H_1 IS NOT NULL THEN 1 ELSE 0 END) as has_exception_h1,
        MAX(CASE WHEN EXC_CD_H_2 IS NOT NULL THEN 1 ELSE 0 END) as has_exception_h2,
        COUNT(DISTINCT CASE WHEN EXC_CD_H_1 = '0102' THEN 1 END) as has_duplicate_flag
    FROM sas_table_subset
    WHERE IPSTAY_ID IS NOT NULL 
      AND C_HDR_MBR_SYS_ID IS NOT NULL
    GROUP BY IPSTAY_ID, C_HDR_MBR_SYS_ID
    """
    
    df = pd.read_sql_query(query, conn)
    
    # Convert dates
    date_cols = ['admit_date', 'discharge_date', 'stay_beg_date', 'stay_end_date']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Calculate derived features
    df['cost_per_day'] = df['total_paid_amount'] / (df['length_of_stay'] + 1e-6)
    df['reimbursement_ratio'] = df['total_paid_amount'] / (df['total_bill_amount'] + 1e-6)
    df['has_prior_stay'] = (df['prior_stay_id'].notna()).astype(int)
    
    # Extract diagnosis category (first 3 chars of ICD-10)
    if 'primary_diagnosis' in df.columns:
        df['diag_category'] = df['primary_diagnosis'].str[:3]
    
    print(f"  Extracted {len(df):,} stay-level records")
    return df


def calculate_readmission_target(stays_df, readmission_window_days=30):
    """
    Calculate readmission target variable.
    For each stay, check if the member had another stay within the readmission window.
    """
    print(f"Calculating {readmission_window_days}-day readmission target...")
    
    # Sort by member and discharge date
    stays_df = stays_df.sort_values(['member_id', 'discharge_date']).copy()
    
    # Initialize target
    stays_df['readmitted_30d'] = 0
    
    # For each member, check if next stay is within readmission window
    for member_id in stays_df['member_id'].unique():
        member_stays = stays_df[stays_df['member_id'] == member_id].copy()
        
        if len(member_stays) > 1:
            for i in range(len(member_stays) - 1):
                current_discharge = member_stays.iloc[i]['discharge_date']
                next_admit = member_stays.iloc[i + 1]['admit_date']
                
                if pd.notna(current_discharge) and pd.notna(next_admit):
                    days_between = (next_admit - current_discharge).days
                    if 0 < days_between <= readmission_window_days:
                        # Mark current stay as having a readmission
                        stay_id = member_stays.iloc[i]['IPSTAY_ID']
                        stays_df.loc[stays_df['IPSTAY_ID'] == stay_id, 'readmitted_30d'] = 1
    
    readmission_rate = stays_df['readmitted_30d'].mean() * 100
    print(f"  Readmission rate: {readmission_rate:.2f}%")
    print(f"  Total readmissions: {stays_df['readmitted_30d'].sum():,}")
    
    return stays_df


def add_member_historical_features(stays_df):
    """
    Add member-level historical features (prior stays, historical averages, etc.)
    """
    print("Adding member historical features...")
    
    stays_df = stays_df.sort_values(['member_id', 'discharge_date']).copy()
    
    # Initialize historical feature columns
    stays_df['stay_sequence'] = 0
    stays_df['total_historical_stays'] = 0
    stays_df['avg_historical_los'] = 0.0
    stays_df['days_since_last_stay'] = np.nan
    stays_df['total_historical_paid'] = 0.0
    
    for member_id in stays_df['member_id'].unique():
        member_stays = stays_df[stays_df['member_id'] == member_id].copy()
        member_stays = member_stays.sort_values('discharge_date')
        
        for idx, (_, stay) in enumerate(member_stays.iterrows()):
            stay_id = stay['IPSTAY_ID']
            
            # Stay sequence (1st, 2nd, 3rd, etc.)
            stays_df.loc[stays_df['IPSTAY_ID'] == stay_id, 'stay_sequence'] = idx + 1
            
            # Historical features (only for stays after the first)
            if idx > 0:
                prior_stays = member_stays.iloc[:idx]
                
                # Total historical stays
                stays_df.loc[stays_df['IPSTAY_ID'] == stay_id, 'total_historical_stays'] = len(prior_stays)
                
                # Average historical LOS
                if prior_stays['length_of_stay'].notna().any():
                    avg_los = prior_stays['length_of_stay'].mean()
                    stays_df.loc[stays_df['IPSTAY_ID'] == stay_id, 'avg_historical_los'] = avg_los
                
                # Days since last stay
                last_discharge = prior_stays.iloc[-1]['discharge_date']
                current_admit = stay['admit_date']
                if pd.notna(last_discharge) and pd.notna(current_admit):
                    days_since = (current_admit - last_discharge).days
                    stays_df.loc[stays_df['IPSTAY_ID'] == stay_id, 'days_since_last_stay'] = days_since
                
                # Total historical paid amount
                if prior_stays['total_paid_amount'].notna().any():
                    total_paid = prior_stays['total_paid_amount'].sum()
                    stays_df.loc[stays_df['IPSTAY_ID'] == stay_id, 'total_historical_paid'] = total_paid
    
    print("  Historical features added")
    return stays_df


def add_temporal_features(stays_df):
    """Add temporal features (month, day of week, season, etc.)"""
    print("Adding temporal features...")
    
    if 'admit_date' in stays_df.columns:
        stays_df['admit_month'] = stays_df['admit_date'].dt.month
        stays_df['admit_day_of_week'] = stays_df['admit_date'].dt.dayofweek
        stays_df['admit_quarter'] = stays_df['admit_date'].dt.quarter
        stays_df['admit_year'] = stays_df['admit_date'].dt.year
    
    if 'discharge_date' in stays_df.columns:
        stays_df['discharge_month'] = stays_df['discharge_date'].dt.month
        stays_df['discharge_day_of_week'] = stays_df['discharge_date'].dt.dayofweek
    
    print("  Temporal features added")
    return stays_df


def encode_categorical_features(stays_df):
    """Encode categorical features for ML."""
    print("Encoding categorical features...")
    
    # Gender encoding (F=0, M=1, other=2)
    if 'gender' in stays_df.columns:
        gender_map = {'F': 0, 'M': 1, 'f': 0, 'm': 1}
        stays_df['gender_encoded'] = stays_df['gender'].map(gender_map).fillna(2).astype(int)
    
    # Age groups
    if 'age' in stays_df.columns:
        stays_df['age_group'] = pd.cut(
            stays_df['age'],
            bins=[0, 18, 35, 50, 65, 120],
            labels=['0-18', '19-35', '36-50', '51-65', '65+']
        )
        # One-hot encode age groups
        age_dummies = pd.get_dummies(stays_df['age_group'], prefix='age_group')
        stays_df = pd.concat([stays_df, age_dummies], axis=1)
    
    # Top N diagnosis categories (one-hot encode)
    if 'diag_category' in stays_df.columns:
        top_diag_cats = stays_df['diag_category'].value_counts().head(20).index
        for diag_cat in top_diag_cats:
            stays_df[f'diag_cat_{diag_cat}'] = (stays_df['diag_category'] == diag_cat).astype(int)
    
    print("  Categorical features encoded")
    return stays_df


def handle_missing_values(stays_df):
    """Handle missing values."""
    print("Handling missing values...")
    
    # Fill numeric columns with median
    numeric_cols = stays_df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if col not in ['readmitted_30d', 'IPSTAY_ID']:  # Don't fill target or ID
            stays_df[col] = stays_df[col].fillna(stays_df[col].median())
    
    # Fill categorical columns with mode or 'Unknown'
    categorical_cols = stays_df.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        if col not in ['IPSTAY_ID', 'member_id']:  # Don't fill IDs
            mode_val = stays_df[col].mode()[0] if len(stays_df[col].mode()) > 0 else 'Unknown'
            stays_df[col] = stays_df[col].fillna(mode_val)
    
    print("  Missing values handled")
    return stays_df


def main():
    """Main feature extraction function."""
    print("\n" + "=" * 80)
    print("FFS CLAIMS FEATURE EXTRACTION")
    print("=" * 80)
    print(f"Database: {DB_PATH}")
    print(f"Output: {OUTPUT_PATH}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if not Path(DB_PATH).exists():
        print(f"ERROR: Database file not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Step 1: Extract stay-level features
        stays_df = extract_stay_level_features(conn)
        
        # Step 2: Calculate readmission target
        stays_df = calculate_readmission_target(stays_df, readmission_window_days=30)
        
        # Step 3: Add member historical features
        stays_df = add_member_historical_features(stays_df)
        
        # Step 4: Add temporal features
        stays_df = add_temporal_features(stays_df)
        
        # Step 5: Encode categorical features
        stays_df = encode_categorical_features(stays_df)
        
        # Step 6: Handle missing values
        stays_df = handle_missing_values(stays_df)
        
        # Step 7: Save to CSV
        print(f"\nSaving features to {OUTPUT_PATH}...")
        Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)
        stays_df.to_csv(OUTPUT_PATH, index=False)
        
        print("\n" + "=" * 80)
        print("FEATURE EXTRACTION COMPLETE")
        print("=" * 80)
        print(f"Total records: {len(stays_df):,}")
        print(f"Total features: {len(stays_df.columns)}")
        print(f"Readmission rate: {stays_df['readmitted_30d'].mean()*100:.2f}%")
        print(f"Output saved to: {OUTPUT_PATH}")
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print("Next Steps:")
        print("1. Review the extracted features: df = pd.read_csv('data/ffs_features.csv')")
        print("2. Explore feature distributions and correlations")
        print("3. Train model with new features")
        print("4. Compare performance with existing model")
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()

