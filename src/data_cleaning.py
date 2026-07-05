import os
import pandas as pd

def load_data(file_path):
    """Safely open the CSV file and handle missing files."""
    try:
        print(f"Loading raw data from: {file_path}")
        df = pd.read_csv(file_path)
        print(f"Loaded {len(df)} patient records successfully.")
        return df
    except FileNotFoundError:
        print(f"Error: Could not find the file at {file_path}")
        return None
    except Exception as e:
        print(f"Error while loading file: {e}")
        return None

def remove_duplicates(df):
    """Remove rows with duplicate PatientIDs to keep data unique."""
    if df is None:
        return None
    
    before = len(df)
    # Keep the first occurrence of the patient record
    df = df.drop_duplicates(subset="PatientID", keep="first")
    removed = before - len(df)
    
    if removed > 0:
        print(f"Removed {removed} duplicate patient records.")
    return df

def fill_missing_values(df):
    """Fill missing medical conditions and text spaces safely."""
    if df is None:
        return None
        
    # Fix missing primary conditions with 'Normal' to pass database constraints
    missing_condition = df["Primary_Condition"].isnull().sum()
    if missing_condition > 0:
        df["Primary_Condition"] = df["Primary_Condition"].fillna("Normal")
        print(f"Filled {missing_condition} blank Primary_Condition rows with 'Normal'.")
        
    # Fill missing text info with clean defaults instead of leaving them empty
    df["State"] = df["State"].fillna("Unknown")
    df["City"] = df["City"].fillna("Unknown")
    df["Insurance_Type"] = df["Insurance_Type"].fillna("None")
    
    return df

def clean_text_columns(df):
    """Remove extra spaces around text values without corrupting blank spaces."""
    if df is None:
        return None
        
    # Only loop through text columns
    for col in df.select_dtypes(include=["object"]).columns:
        # Strip spacing safely only if the cell contains actual text
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
    return df

def fix_types_and_align_schema(df):
    """Convert column types safely and rename them to match the MySQL database."""
    if df is None:
        return None
        
    try:
        # Convert date column safely (invalid dates will become NaT comfortably)
        df["Last_Visit_Date"] = pd.to_datetime(df["Last_Visit_Date"], errors="coerce")
        
        # Fill missing flags with 0 first to prevent an integer conversion crash
        df["Preventive_Care_Flag"] = df["Preventive_Care_Flag"].fillna(0).astype(int)
        
        # Map PascalCase CSV columns to match lowercase database table names
        column_mapping = {
            "PatientID": "patient_id", "Age": "age", "Gender": "gender", 
            "State": "state", "City": "city", "Height_cm": "height_cm", 
            "Weight_kg": "weight_kg", "BMI": "bmi", "Insurance_Type": "insurance_type", 
            "Primary_Condition": "primary_condition", "Num_Chronic_Conditions": "num_chronic_conditions", 
            "Annual_Visits": "annual_visits", "Avg_Billing_Amount": "avg_billing_amount", 
            "Last_Visit_Date": "last_visit_date", "Days_Since_Last_Visit": "days_since_last_visit", 
            "Preventive_Care_Flag": "preventive_care_flag"
        }
        df = df.rename(columns=column_mapping)
        
        # Add placeholder columns required by the database schema
        df["risk_score"] = 0.00
        df["cluster_id"] = None
        
        print("Data types converted and columns aligned with database schema successfully.")
    except Exception as e:
        print(f"Warning: Unexpected type correction error - {e}")
        
    return df

def clean_data(input_path, output_path):
    """Main coordinator function to run the cleaning pipeline steps sequentially."""
    df = load_data(input_path)
    if df is None:
        return None

    # Step-by-step pipeline transformations
    df = remove_duplicates(df)
    df = fill_missing_values(df)
    df = clean_text_columns(df)
    df = fix_types_and_align_schema(df)

    # Automatically build the destination directory if it is missing
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    try:
        df.to_csv(output_path, index=False)
        print(f"Cleaned data successfully saved to: {output_path}")
        return df
    except Exception as e:
        print(f"Error: Could not save the cleaned file to disk - {e}")
        return None

if __name__ == "__main__":
    # Locate paths dynamically relative to where this script file lives
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    raw_file = os.path.join(base_dir, "data", "raw", "patient_segmentation_dataset.csv")
    cleaned_file = os.path.join(base_dir, "data", "processed", "patients_cleaned.csv")
    
    clean_data(raw_file, cleaned_file)