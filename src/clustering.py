import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Allows plots to save quietly without opening visual windows
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import joblib

def load_data(file_path):
    """Safely load the preprocessed training dataset from disk."""
    try:
        print(f"Loading processed data from: {file_path}")
        df = pd.read_csv(file_path)
        print(f"Loaded {len(df)} records successfully.")
        return df
    except FileNotFoundError:
        print(f"Error: Processed file not found at {file_path}")
        return None
    except Exception as e:
        print(f"Error loading file: {e}")
        return None

def get_features(df):
    """Isolate purely numeric columns for mathematical clustering calculations."""
    if df is None or df.empty:
        return None
        
    # Automatically filter out text, notes, dates, or IDs
    # This keeps our scaled columns and integer dummy columns safely
    features_df = df.select_dtypes(include=["number"])
    
    # If this script is run on an already clustered file, drop the old column
    if "cluster_id" in features_df.columns:
        features_df = features_df.drop(columns=["cluster_id"])
        
    return features_df

def try_different_k(X, max_k=8):
    """Evaluate cluster size variations using both Elbow and Silhouette metrics."""
    if X is None or X.empty:
        return []
        
    print(f"Evaluating potential cluster counts from k=2 to k={max_k}...")
    results = []
    
    for k in range(2, max_k + 1):
        try:
            model = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = model.fit_predict(X)
            
            # Capture both metrics for a comprehensive view
            inertia = model.inertia_
            silhouette = silhouette_score(X, labels)
            
            print(f"k = {k} | Inertia (Elbow): {inertia:,.2f} | Silhouette: {silhouette:.4f}")
            results.append({"k": k, "inertia": inertia, "silhouette": silhouette})
        except Exception as e:
            print(f"Warning: Metrics calculation skipped for k={k} due to: {e}")
            
    return results

def plot_results(results, output_path):
    """Generate and save clear, dual-metric validation charts for documentation."""
    if not results:
        print("Warning: No evaluation data available to plot.")
        return
        
    ks = [r["k"] for r in results]
    inertias = [r["inertia"] for r in results]
    silhouettes = [r["silhouette"] for r in results]
    
    # Create a clean side-by-side visualization layout
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Left Panel: The Elbow Chart (Inertia)
    ax1.plot(ks, inertias, marker='o', color='royalblue', linewidth=2)
    ax1.set_title("Elbow Method (Inertia trend)")
    ax1.set_xlabel("Number of Clusters (k)")
    ax1.set_ylabel("Inertia Score (Lower is Better)")
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    # Right Panel: The Silhouette Chart
    ax2.plot(ks, silhouettes, marker='s', color='darkorange', linewidth=2)
    ax2.set_title("Silhouette Density Analysis")
    ax2.set_xlabel("Number of Clusters (k)")
    ax2.set_ylabel("Silhouette Score (Higher is Better)")
    ax2.grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    
    # Establish directory pathways if missing on the local machine
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    try:
        plt.savefig(output_path, dpi=150)
        print(f"Evaluation charts successfully saved to: {output_path}")
    except Exception as e:
        print(f"Error: Could not save analysis graphics to disk - {e}")
    finally:
        plt.close()

def run_clustering(input_path, output_path, model_path, chart_path, chosen_k=4):
    """Main coordinator function to train and export the patient segmentation model."""
    df = load_data(input_path)
    if df is None:
        return None

    X = get_features(df)
    if X is None or X.empty:
        print("Error: Abandoning execution due to an invalid or empty feature matrix.")
        return None

    # Track metrics and plot trends
    results = try_different_k(X)
    plot_results(results, chart_path)

    # Train final model on chosen_k target
    print(f"\nTraining final operational segmentation model with k = {chosen_k}")
    try:
        model = KMeans(n_clusters=chosen_k, random_state=42, n_init=10)
        df["cluster_id"] = model.fit_predict(X)
        
        # Save trained cluster model configurations
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        joblib.dump(model, model_path)
        print(f"Model file saved successfully to: {model_path}")
        
        # Save labeled records
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"✅ Clustered results successfully saved to: {output_path}")
        
        return df
    except Exception as e:
        print(f"Error: Clustering pipeline training phase failed - {e}")
        return None

if __name__ == "__main__":
    # Resolve dynamic relative pathways based on script execution context
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    processed_file = os.path.join(base_dir, "data", "processed", "patients_processed.csv")
    clustered_file = os.path.join(base_dir, "data", "processed", "patients_clustered.csv")
    model_file = os.path.join(base_dir, "models", "kmeans_model.pkl")
    chart_file = os.path.join(base_dir, "reports", "cluster_chart.png")
    
    run_clustering(processed_file, clustered_file, model_file, chart_file)