import os
import pandas as pd

def load_data(file_path):
    """Safely load the cleaned dataset from disk."""
    try:
        print(f"Loading cleaned data from: {file_path}")
        df = pd.read_csv(file_path)
        print(f"Loaded {len(df)} patient records.")
        return df
    except FileNotFoundError:
        print(f"Error: Cleaned file not found at {file_path}")
        return None
    except Exception as e:
        print(f"Error loading file: {e}")
        return None

def get_bmi_points(bmi_value):
    """Helper function to calculate risk points for BMI safely."""
    try:
        # Convert to float to handle calculations safely
        val = float(bmi_value)
        if pd.isna(val):
            return 0
        if val >= 30.0:
            return 20
        if val >= 25.0:
            return 10
        return 0
    except (ValueError, TypeError):
        # Return 0 points if data is corrupted or text
        return 0

def get_age_points(age_value):
    """Helper function to calculate risk points for Age safely."""
    try:
        val = float(age_value)
        if pd.isna(val):
            return 0
        if val >= 60:
            return 15
        if val >= 40:
            return 5
        return 0
    except (ValueError, TypeError):
        return 0

def calculate_risk_score(df):
    """Calculate the patient medical risk score based on key metrics."""
    if df is None:
        return None
    
    try:
        # Ensure input data columns are treated as numeric to prevent math crashes
        chronic = pd.to_numeric(df["num_chronic_conditions"], errors="coerce").fillna(0)
        preventive = pd.to_numeric(df["preventive_care_flag"], errors="coerce").fillna(0)
        
        # Apply our safe helper functions row by row
        bmi_pts = df["bmi"].apply(get_bmi_points)
        age_pts = df["age"].apply(get_age_points)
        
        # Standard scoring formula
        chronic_part = chronic * 20
        preventive_bonus = preventive * 10
        
        raw_score = chronic_part + bmi_pts + age_pts - preventive_bonus
        
        # Round to 2 decimal places to match the database DECIMAL(5,2) definition
        df["risk_score"] = raw_score.clip(lower=0).round(2)
        print("Risk scores calculated and rounded successfully.")
    except Exception as e:
        print(f"Warning: Could not calculate risk score - {e}")
    
    return df

def add_bmi_category(df):
    """Categorize patients by BMI range safely without mislabeling empty rows."""
    if df is None:
        return None
    
    try:
        # Step 1: Force column numeric so comparison works flawlessly
        bmi_numeric = pd.to_numeric(df["bmi"], errors="coerce")
        
        # Step 2: Initialize everything as 'Normal' or 'Unknown' first
        df["bmi_category"] = "Normal"
        
        # Step 3: Map specific categories based on strict boundary slots
        df.loc[bmi_numeric >= 30.0, "bmi_category"] = "Obese"
        df.loc[(bmi_numeric >= 25.0) & (bmi_numeric < 30.0), "bmi_category"] = "Overweight"
        df.loc[bmi_numeric < 18.5, "bmi_category"] = "Underweight"
        
        # Step 4: Explicitly catch missing or broken values so they don't get mislabeled
        df.loc[bmi_numeric.isna(), "bmi_category"] = "Unknown"
        
        print("BMI categories added successfully.")
    except Exception as e:
        print(f"Warning: Could not add BMI categories - {e}")
    
    return df

def calculate_cost_per_visit(df):
    """Calculate individual patient billing footprint per visit."""
    if df is None:
        return None
    
    try:
        # Safe numeric conversions
        billing = pd.to_numeric(df["avg_billing_amount"], errors="coerce").fillna(0.0)
        visits = pd.to_numeric(df["annual_visits"], errors="coerce").fillna(1)
        
        # Replace 0 with 1 to completely prevent division-by-zero crashes
        safe_visits = visits.replace(0, 1)
        
        df["cost_per_visit"] = (billing / safe_visits).round(2)
        print("Cost per visit metric calculated.")
    except Exception as e:
        print(f"Warning: Could not calculate cost per visit - {e}")
    
    return df

def engineer_features(input_path, output_path):
    """Orchestrate and apply all new features to the processed data dataset."""
    df = load_data(input_path)
    if df is None:
        return None

    # Process metrics sequentially
    df = calculate_risk_score(df)
    df = add_bmi_category(df)
    df = calculate_cost_per_visit(df)

    # Automatically build target folder directory paths if missing
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    try:
        df.to_csv(output_path, index=False)
        print(f"Features successfully saved to: {output_path}")
        return df
    except Exception as e:
        print(f"Error: Could not save feature file to disk - {e}")
        return None

if __name__ == "__main__":
    # Base path routing relative to script file environment locations
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    cleaned_file = os.path.join(base_dir, "data", "processed", "patients_cleaned.csv")
    features_file = os.path.join(base_dir, "data", "processed", "patients_features.csv")
    
    engineer_features(cleaned_file, features_file)