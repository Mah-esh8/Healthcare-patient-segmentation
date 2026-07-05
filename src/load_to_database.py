import os
import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from database import get_engine

def load_data(file_path):
    """Safely load a processed CSV file from the local filesystem path."""
    try:
        print(f"Loading data from disk asset: {file_path}")
        df = pd.read_csv(file_path)
        print(f"Successfully loaded {len(df)} records.")
        return df
    except FileNotFoundError:
        print(f"[CRITICAL] Error: Expected file target not found at {file_path}")
        return None
    except Exception as e:
        print(f"[CRITICAL] Unexpected error loading dataset: {e}")
        return None

def load_to_database(patients_path, profiles_path):
    """
    Orchestrates the purge and insertion of healthcare data into MySQL.
    
    Uses a unified database transaction to maintain atomicity (all-or-nothing).
    """
    patients_df = load_data(patients_path)
    profiles_df = load_data(profiles_path)
    
    if patients_df is None or profiles_df is None:
        print("[FAILURE] Aborting database load due to missing or unreadable source data files.")
        return False

    if patients_df.empty or profiles_df.empty:
        print("[FAILURE] Aborting database load: One or both Source DataFrames are empty.")
        return False

    try:
        engine = get_engine()
    except Exception as e:
        print(f"[CRITICAL] Failed to initialize database engine: {e}")
        return False

    # Establish an explicit, atomic transaction block for safe pipeline execution
    try:
        print("\nStarting atomic database migration context...")
        with engine.begin() as conn:
            
            # Step 1: Purge old tracking tables in reverse Foreign Key order
            print("Purging legacy tables dynamically...")
            conn.execute(text("DELETE FROM patients_clustered"))
            conn.execute(text("DELETE FROM cluster_profiles"))
            print("Successfully cleared historical records from tables.")

            # Step 2: Stream cluster profiles into the database first (FK Parent)
            print("Streaming cluster profiles to database...")
            profiles_df.to_sql(
                name="cluster_profiles",
                con=conn,
                if_exists="append",
                index=False,
                chunksize=500,
                method="multi"
            )
            print(f"Successfully migrated {len(profiles_df)} rows into 'cluster_profiles'.")

            # Step 3: Stream clustered patient records into the database (FK Child)
            print("Streaming finalized patient data segments to database...")
            patients_df.to_sql(
                name="patients_clustered",
                con=conn,
                if_exists="append",
                index=False,
                chunksize=2000,
                method="multi"
            )
            print(f"Successfully migrated {len(patients_df)} rows into 'patients_clustered'.")

        print("\n========== DATABASE TRANSACTION COMMITTED SECURELY ==========")
        print("✅ All clinical data sets successfully loaded into MySQL!")
        return True

    except SQLAlchemyError as e:
        print("\n[CRITICAL] TRANSACTION ROLLBACK TRIGGERED.")
        print(f"Database operation failed with error: {e}")
        print("The database has rolled back automatically to its pre-pipeline state. No data changed.")
        return False
    except Exception as e:
        print(f"\n[CRITICAL] Unexpected application exception caught mid-transaction: {e}")
        print("Ensuring rollback execution satisfies integrity safety mandates.")
        return False

if __name__ == "__main__":
    # Resolves paths safely from healthcare-patient-segmentation/src/ to the root directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    patients_file = os.path.join(base_dir, "data", "processed", "patients_final.csv")
    profiles_file = os.path.join(base_dir, "data", "processed", "cluster_profiles.csv")
    
    load_to_database(patients_file, profiles_file)