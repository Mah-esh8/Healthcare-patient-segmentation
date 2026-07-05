import os
import time
import sys

def execute_full_pipeline():
    """
    Orchestrates the entire End-to-End Healthcare Patient Segmentation Pipeline.
    
    Enforces strict gating: if any stage fails or returns None/False, execution
    halts immediately to protect data, model, and database integrity.
    """
    start_time = time.time()
    print("=" * 75)
    print("🚀 INITIALIZING HEALTHCARE PATIENT SEGMENTATION PIPELINE COHORT")
    print("=" * 75)

    # Resolve paths dynamically 2 levels up from src/ to healthcare-patient-segmentation/
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Centralized Asset Pathway Matrix
    raw_data_path = os.path.join(base_dir, "data", "raw", "patient_segmentation_dataset.csv")
    cleaned_data_path = os.path.join(base_dir, "data", "processed", "patients_cleaned.csv")
    features_data_path = os.path.join(base_dir, "data", "processed", "patients_features.csv")
    processed_data_path = os.path.join(base_dir, "data", "processed", "patients_processed.csv")
    clustered_data_path = os.path.join(base_dir, "data", "processed", "patients_clustered.csv")
    patients_final_path = os.path.join(base_dir, "data", "processed", "patients_final.csv")
    cluster_profiles_path = os.path.join(base_dir, "data", "processed", "cluster_profiles.csv")
    
    scaler_path = os.path.join(base_dir, "models", "scaler.pkl")
    model_path = os.path.join(base_dir, "models", "kmeans_model.pkl")
    chart_path = os.path.join(base_dir, "reports", "cluster_chart.png")

    # Force append the local directory context to resolve imports cleanly
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        from data_validation import running_validation
        from data_cleaning import clean_data
        from feature_engineering import engineer_features
        from preprocessing import preprocess_data
        from clustering import run_clustering  # NOTE: Adjust if your entry-point function uses a different name
        from cluster_interpretation import run_interpretation
        from load_to_database import load_to_database
    except ImportError as e:
        print(f"\n[CRITICAL] Pipeline Import Map Error: {e}")
        print("Ensure all script files exist within the 'src/' directory with correct function signatures.")
        return False

    # -------------------------------------------------------------------------
    # STAGE 1: Data Validation Gate
    # -------------------------------------------------------------------------
    print("\n--- STAGE 1: RUNNING DATA VALIDATION CONSTRAINTS ---")
    if not running_validation(raw_data_path):
        print("[CRITICAL] Pipeline Broken: Raw data failed structural integrity validation.")
        return False

    # -------------------------------------------------------------------------
    # STAGE 2: Data Cleaning Execution
    # -------------------------------------------------------------------------
    print("\n--- STAGE 2: EXECUTING DATA CLEANING & RECTIFICATION ---")
    cleaned_df = clean_data(raw_data_path, cleaned_data_path)
    if cleaned_df is None:
        print("[CRITICAL] Pipeline Broken: Data cleaning operations returned an execution failure.")
        return False

    # -------------------------------------------------------------------------
    # STAGE 3: Feature Engineering Derivations
    # -------------------------------------------------------------------------
    print("\n--- STAGE 3: CALCULATING RISK SCORES & CLINICAL FEATURES ---")
    features_df = engineer_features(cleaned_data_path, features_data_path)
    if features_df is None:
        print("[CRITICAL] Pipeline Broken: Feature engineering processing failed.")
        return False

    # -------------------------------------------------------------------------
    # STAGE 4: Feature Preprocessing (Scaling & Dummies)
    # -------------------------------------------------------------------------
    print("\n--- STAGE 4: STANDARDIZING NUMERICS & ENCODING CATEGORICALS ---")
    processed_df = preprocess_data(features_data_path, processed_data_path, scaler_path)
    if processed_df is None:
        print("[CRITICAL] Pipeline Broken: Mathematical data preprocessing failed.")
        return False

    # -------------------------------------------------------------------------
    # STAGE 5: Unsupervised Clustering Execution (K-Means)
    # -------------------------------------------------------------------------
    print("\n--- STAGE 5: RUNNING UNSUPERVISED PATIENT CLUSTERING ---")
    clustered_df = run_clustering(processed_data_path, clustered_data_path, model_path, chart_path)
    if clustered_df is None:
        print("[CRITICAL] Pipeline Broken: Unsupervised model clustering phase failed.")
        return False

    # -------------------------------------------------------------------------
    # STAGE 6: Interpretation & Database Alignment Schema
    # -------------------------------------------------------------------------
    print("\n--- STAGE 6: MAPPING LABEL TIERS & ALIGNING TO SQL LAYOUT ---")
    interpretation_result = run_interpretation(features_data_path, clustered_data_path, patients_final_path, cluster_profiles_path)
    if interpretation_result is None:
        print("[CRITICAL] Pipeline Broken: Cluster profile structural synthesis failed.")
        return False

    # -------------------------------------------------------------------------
    # STAGE 7: Relational Database Migration (Atomic Transaction)
    # -------------------------------------------------------------------------
    print("\n--- STAGE 7: TRANSMITTING FINALIZED ASSETS TO MYSQL WAREHOUSE ---")
    db_status = load_to_database(patients_final_path, cluster_profiles_path)
    if not db_status:
        print("[CRITICAL] Pipeline Broken: Atomic warehouse database ingestion failed.")
        return False

    # -------------------------------------------------------------------------
    # Execution Diagnostic Complete
    # -------------------------------------------------------------------------
    elapsed_time = round(time.time() - start_time, 2)
    print("\n" + "=" * 75)
    print(f"🎉 PIPELINE EXECUTED COMPLETELY AND SUCCESSFULLY IN {elapsed_time}s!")
    print(f"   - Validated & Cleaned: {cleaned_data_path}")
    print(f"   - Features Extracted:  {features_data_path}")
    print(f"   - Scaled Matrices:     {processed_data_path}")
    print(f"   - Model Artifacts:     {scaler_path} & {model_path}")
    print(f"   - Labeled Clusters:    {clustered_data_path}")
    print(f"   - SQL Profiles Ready:  {patients_final_path} & {cluster_profiles_path}")
    print(f"   - Relational Database: Sync completed securely inside MySQL Warehouse.")
    print("=" * 75)
    return True

if __name__ == "__main__":
    execute_full_pipeline()