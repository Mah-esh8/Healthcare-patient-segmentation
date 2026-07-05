import os
import pandas as pd 

REQUIRED_COLUMNS = [
    "PatientID", "Age", "Gender", "State", "City", "Height_cm", "Weight_kg",
    "BMI", "Insurance_Type", "Primary_Condition", "Num_Chronic_Conditions",
    "Annual_Visits", "Avg_Billing_Amount", "Last_Visit_Date",
    "Days_Since_Last_Visit", "Preventive_Care_Flag"
]

VALID_GENDERS = ["Male", "Female", "Other"]

def load_data(file_path):
    """Loads CSV safely, neutralizing file system and parsing engine crashes."""
    try:
        return pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"[CRITICAL] Target dataset file not found at: {file_path}")
        return None
    except pd.errors.EmptyDataError:
        print(f"[CRITICAL] Selected data file is completely empty: {file_path}")
        return None
    except Exception as e:
        print(f"[CRITICAL] Unexpected file load or corruption failure: {str(e)}")
        return None


def check_columns(df):
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        print(f"[CRITICAL] Missing structural columns: {missing}")
    return missing


def check_duplicates(df):
    # Protects logic against missing/null value evaluation errors
    valid_ids = df["PatientID"].dropna()
    count = valid_ids.duplicated().sum()
    if count > 0:
        print(f"[WARNING] Duplicate PatientID profiles identified: {count} rows.")
    return count


def check_id_length(df, max_length=20):
    # Safely converts to string format to check lengths accurately
    lengths = df["PatientID"].fillna("").astype(str).str.len()
    bad_rows = df[lengths > max_length]
    if len(bad_rows) > 0:
        print(f"[WARNING] PatientID values exceeding max layout limits ({max_length} chars): {len(bad_rows)} rows.")
    return len(bad_rows)


def check_range(df, column, min_value=None, max_value=None):
    """Safely validates range bounds without crashing on corrupt text or symbols."""
    # Convert data type to numeric safely. Irregular strings become NaN instead of crashing
    numeric_series = pd.to_numeric(df[column], errors='coerce')
    
    issues = pd.Series([False] * len(df))
    if min_value is not None:
        issues = issues | (numeric_series < min_value) | (numeric_series.isna() & df[column].notna())
    if max_value is not None:
        issues = issues | (numeric_series > max_value)
        
    bad_rows = df[issues]
    if len(bad_rows) > 0:
        print(f"[CRITICAL] Column '{column}' violates database constraints (Range: {min_value} to {max_value}): {len(bad_rows)} invalid rows.")
    return len(bad_rows)


def check_allowed_values(df, column, allowed_values):
    # Standardizes string checks by stripping accidental whitespace padding
    series_to_check = df[column].astype(str).str.strip() if df[column].dtype == 'object' else df[column]
    bad_rows = df[~series_to_check.isin(allowed_values)]
    if len(bad_rows) > 0:
        print(f"[CRITICAL] Column '{column}' contains invalid values for MySQL constraints: {bad_rows[column].unique()}")
    return len(bad_rows)


def check_missing_primary_conditions(df):
    missing = df["Primary_Condition"].isnull()
    if missing.sum() > 0:
        print(f"[WARNING] Missing Primary_Condition fields: {missing.sum()} records.")
        linked_to_zero_chronic = df.loc[missing, "Num_Chronic_Conditions"].eq(0).all()
        if linked_to_zero_chronic:
            print("  -> Self-Correction Note: All missing records correlate with 0 chronic conditions.")
        else:
            print("  -> Data Discrepancy: Some missing metrics do not match standard zero chronic criteria.")
    return missing.sum()


def check_dates(df):
    # Coerces corrupt date structures smoothly to handle invalid inputs gracefully
    parsed_dates = pd.to_datetime(df["Last_Visit_Date"], errors="coerce")
    bad_rows_count = parsed_dates.isnull().sum() - df["Last_Visit_Date"].isnull().sum()
    if bad_rows_count > 0:
        print(f"[WARNING] Unparseable or malformed date rows in Last_Visit_Date: {bad_rows_count} instances.")
    return bad_rows_count


def running_validation(file_path):
    """Orchestrates comprehensive validation check, safeguarding pipeline flow control."""
    df = load_data(file_path)
    if df is None:
        return False

    # Structural Integrity Enforcement
    missing_cols = check_columns(df)
    if missing_cols:
        return False

    critical_errors = 0

    # Execute and track critical data anomalies
    check_duplicates(df)
    check_id_length(df)
    
    # Range validations: Increment failure tracker if any bounds are completely broken
    critical_errors += check_range(df, "Age", min_value=0, max_value=100)
    critical_errors += check_range(df, "Height_cm", min_value=0)
    critical_errors += check_range(df, "Weight_kg", min_value=0)
    critical_errors += check_range(df, "BMI", min_value=0)
    critical_errors += check_range(df, "Num_Chronic_Conditions", min_value=0)
    critical_errors += check_range(df, "Annual_Visits", min_value=0)
    critical_errors += check_range(df, "Avg_Billing_Amount", min_value=0)
    critical_errors += check_range(df, "Days_Since_Last_Visit", min_value=0)
    
    # Categorical integrity evaluations
    critical_errors += check_allowed_values(df, "Gender", VALID_GENDERS)
    critical_errors += check_allowed_values(df, "Preventive_Care_Flag", [0, 1])
    
    # General warning lookups (Informational metrics; don't break database execution directly)
    check_missing_primary_conditions(df)
    check_dates(df)

    # Final Gatekeeper Assessment
    if critical_errors > 0:
        print(f"\n[FAILURE] Validation complete. Blocked {critical_errors} database-breaking values from entering execution.")
        return False

    print("\n[SUCCESS] All critical structural and database validation checks passed cleanly.")
    return True


if __name__ == "__main__":
    # Standardize path routing strategies dynamically across files safely
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SAMPLE_PATH = os.path.join(BASE_DIR, "data", "raw", "patient_segmentation_dataset.csv")
    
    # Fallback backup configuration string to support manual testing
    if not os.path.exists(SAMPLE_PATH):
        SAMPLE_PATH = r"C:\Users\rebel\OneDrive\Documents\Healthcare-patient-segmentation\data\raw\patient_segmentation_dataset.csv"
        
    running_validation(SAMPLE_PATH)