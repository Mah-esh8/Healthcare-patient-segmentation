import os
import pandas as pd

def load_data(file_path):
    """Safely load a CSV dataset from the local filesystem path."""
    try:
        print(f"Loading file asset from: {file_path}")
        df = pd.read_csv(file_path)
        print(f"Loaded {len(df)} records successfully.")
        return df
    except FileNotFoundError:
        print(f"Error: Target file not found at {file_path}")
        return None
    except Exception as e:
        print(f"Error executing file load operations: {e}")
        return None

def merge_cluster_labels(features_df, clustered_df):
    """Merge cluster assignment IDs back onto baseline patient features without suffix collision."""
    if features_df is None or clustered_df is None:
        return None
    
    # Enhancement: Clear old/placeholder cluster tracking to prevent cluster_id_x / cluster_id_y duplication
    cleaned_features = features_df.drop(columns=["cluster_id"], errors="ignore")
    
    cluster_info = clustered_df[["patient_id", "cluster_id"]]
    merged = cleaned_features.merge(cluster_info, on="patient_id", how="left")
    return merged

def _get_dominant_categorical(series, default_fallback="Unknown"):
    """Helper guard evaluating categorical modes securely to neutralize IndexError crashes."""
    if series is None or series.dropna().empty:
        return default_fallback
    
    calculated_mode = series.mode()
    # Safe Guard: Verify that the computed mode collection contains structural index records before extraction
    if not calculated_mode.empty:
        return calculated_mode.iloc[0]
    return default_fallback

def summarize_each_cluster(df):
    """Compile foundational clinical profiling matrix calculations for each identified cluster."""
    if df is None:
        return None
        
    total_records = len(df)
    summaries = []
    
    for cluster_id, group in df.groupby("cluster_id"):
        summary = {
            "cluster_id": int(cluster_id),
            "patient_count": len(group),
            "avg_age": round(float(group["age"].mean()), 2),
            "avg_bmi": round(float(group["bmi"].mean()), 2),
            "avg_risk_score": round(float(group["risk_score"].mean()), 2),
            "segment_size_pct": round(float(len(group) / total_records * 100), 2),
            "avg_annual_visits": round(float(group["annual_visits"].mean()), 2),
            "avg_billing_amount": round(float(group["avg_billing_amount"].mean()), 2),
            "avg_days_since_last_visit": round(float(group["days_since_last_visit"].mean()), 2),
            "dominant_insurance_type": _get_dominant_categorical(group["insurance_type"], default_fallback="None"),
            "dominant_condition": _get_dominant_categorical(group["primary_condition"], default_fallback="Normal"),
        }
        summaries.append(summary)
    
    return pd.DataFrame(summaries)

def add_cluster_labels(profiles_df):
    """Assign human-readable clinical tier category markers ordered logically by average cluster risk."""
    if profiles_df is None:
        return None
        
    # Sort by risk first to assign tier labels consistently
    sorted_profiles = profiles_df.sort_values("avg_risk_score", ascending=False).copy()
    
    tier_labels = ["Highest Risk Patients", "High Risk Patients", "Moderate Risk Patients", "Low Risk Patients"]
    sorted_profiles["cluster_label"] = [
        tier_labels[i] if i < len(tier_labels) else f"Cluster {i+1} Segment" 
        for i in range(len(sorted_profiles))
    ]
    return sorted_profiles

def create_recommendations(profiles_df):
    """Generate business and medical outreach strategies tailored to specific risk score buckets."""
    if profiles_df is None:
        return None
        
    recommendations = []
    for _, row in profiles_df.iterrows():
        if row["avg_risk_score"] >= 60.0:
            rec = "Prioritize preventive care programs and frequent check-ins for this high-risk group."
        elif row["avg_risk_score"] >= 30.0:
            rec = "Offer targeted wellness programs and monitoring."
        else:
            rec = "Continue standard care and routine reminders."
        recommendations.append(rec)
        
    profiles_df["recommendation"] = recommendations
    return profiles_df

def run_interpretation(features_path, clustered_path, patients_output, profiles_output):
    """Core analytical sequence loading datasets, constructing indicators, and structuring schemas."""
    features = load_data(features_path)
    clustered = load_data(clustered_path)
    if features is None or clustered is None:
        return None

    merged = merge_cluster_labels(features, clustered)
    if merged is None:
        return None

    profiles = summarize_each_cluster(merged)
    profiles = add_cluster_labels(profiles)
    profiles = create_recommendations(profiles)

    # Enhancement: Reorder columns to align exactly with the SQL target schemas
    cluster_profiles_schema_order = [
        "cluster_id", "cluster_label", "patient_count", "avg_age", "avg_bmi",
        "avg_risk_score", "segment_size_pct", "avg_annual_visits",
        "avg_billing_amount", "avg_days_since_last_visit",
        "dominant_insurance_type", "dominant_condition", "recommendation"
    ]
    
    patients_clustered_schema_order = [
        "patient_id", "age", "gender", "state", "city", "height_cm", "weight_kg",
        "bmi", "insurance_type", "primary_condition", "risk_score", 
        "num_chronic_conditions", "annual_visits", "avg_billing_amount", 
        "last_visit_date", "days_since_last_visit", "preventive_care_flag", "cluster_id"
    ]

    # Reindex columns to match target database definitions exactly
    if profiles is not None:
        profiles = profiles[[col for col in cluster_profiles_schema_order if col in profiles.columns]]
        
    if merged is not None:
        # Drops temporary engineered columns (e.g., bmi_category, cost_per_visit) that don't belong in the SQL layout
        merged = merged[[col for col in patients_clustered_schema_order if col in merged.columns]]

    # Export finalized files back to target filesystem paths
    for path, data in [(patients_output, merged), (profiles_output, profiles)]:
        if data is not None:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            data.to_csv(path, index=False)
            print(f"Processed output exported to: {path}")

    return merged, profiles

if __name__ == "__main__":
    # Standard dynamic pathway routing strategies relative to current script folder context
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    features_file = os.path.join(base_dir, "data", "processed", "patients_features.csv")
    clustered_file = os.path.join(base_dir, "data", "processed", "patients_clustered.csv")
    patients_file = os.path.join(base_dir, "data", "processed", "patients_final.csv")
    profiles_file = os.path.join(base_dir, "data", "processed", "cluster_profiles.csv")
    
    run_interpretation(features_file, clustered_file, patients_file, profiles_file)