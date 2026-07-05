import os
import pandas as pd
from sklearn.preprocessing import StandardScaler
import joblib

# Columns we need for machine learning
NUMERIC_COLUMNS = [
    "age", "height_cm", "weight_kg", "bmi", "num_chronic_conditions",
    "annual_visits", "avg_billing_amount", "days_since_last_visit",
    "cost_per_visit", "risk_score"
]

CATEGORICAL_COLUMNS = ["gender", "state", "insurance_type", "primary_condition", "bmi_category"]

def load_data(file_path):
    """Load the feature-engineered CSV file safely."""
    try:
        print(f"Loading data for preprocessing from: {file_path}")
        df = pd.read_csv(file_path)
        print(f"Loaded {len(df)} records successfully.")
        return df
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except Exception as e:
        print(f"Error loading file: {e}")
        return None

def verify_pipeline_columns(df):
    """Ensure all required numeric and categorical columns exist in the file."""
    if df is None:
        return False
        
    missing_columns = []
    
    # Check numeric list
    for col in NUMERIC_COLUMNS:
        if col not in df.columns:
            missing_columns.append(col)
            
    # Check categorical list
    for col in CATEGORICAL_COLUMNS:
        if col not in df.columns:
            missing_columns.append(col)
            
    if missing_columns:
        print(f"[CRITICAL] Preprocessing halted. Missing expected columns: {missing_columns}")
        return False
        
    return True

def drop_unneeded_columns(df):
    """Remove columns we don't need for clustering calculations."""
    if df is None:
        return None
        
    columns_to_drop = ["city", "last_visit_date", "cluster_id"]
    
    # Only drop columns that are actually present in the dataframe
    existing_to_drop = [col for col in columns_to_drop if col in df.columns]
    
    if existing_to_drop:
        df = df.drop(columns=existing_to_drop)
        print(f"Dropped tracking columns: {existing_to_drop}")
    return df

def encode_categories(df):
    """Convert text categories into numbers using explicit one-hot encoding."""
    if df is None:
        return None
        
    try:
        # dtype=int forces 1 and 0 outputs, preventing newer Pandas from making True/False columns
        df = pd.get_dummies(df, columns=CATEGORICAL_COLUMNS, dtype=int)
        print("Categorical columns one-hot encoded with integer flags.")
    except Exception as e:
        print(f"Warning: Could not encode categories - {e}")
    return df

def scale_numbers(df, scaler_path):
    """Scale numeric columns so they are balanced for clustering models."""
    if df is None:
        return None
        
    try:
        scaler = StandardScaler()
        
        # Scale only our specific numeric training features in place
        df[NUMERIC_COLUMNS] = scaler.fit_transform(df[NUMERIC_COLUMNS])
        
        # Save the scaler object for upcoming inference pipeline stages
        os.makedirs(os.path.dirname(scaler_path), exist_ok=True)
        joblib.dump(scaler, scaler_path)
        print(f"Standard scaler saved to: {scaler_path}")
    except Exception as e:
        print(f"Warning: Scaling execution failure - {e}")
    return df

def preprocess_data(input_path, output_path, scaler_path):
    """Main coordinator function running the complete preprocessing pipeline."""
    df = load_data(input_path)
    if df is None:
        return None

    # Structural Gatekeeper: Stop early if data columns don't match assumptions
    if not verify_pipeline_columns(df):
        return None

    # Step-by-step feature transformations
    df = drop_unneeded_columns(df)
    df = encode_categories(df)
    df = scale_numbers(df, scaler_path)

    # Save the finalized processed training set to disk
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    try:
        df.to_csv(output_path, index=False)
        print(f"✅ Preprocessed data successfully saved to: {output_path}")
        return df
    except Exception as e:
        print(f"Error saving processed file: {e}")
        return None

if __name__ == "__main__":
    # Standard dynamic path routing strategies relative to script folder location
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    features_file = os.path.join(base_dir, "data", "processed", "patients_features.csv")
    processed_file = os.path.join(base_dir, "data", "processed", "patients_processed.csv")
    scaler_file = os.path.join(base_dir, "models", "scaler.pkl")
    
    preprocess_data(features_file, processed_file, scaler_file)