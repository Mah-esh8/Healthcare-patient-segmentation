import os
import sys

# Compute the root directory relative to this script location
root_dir = os.path.dirname(os.path.abspath(__file__))

# Inject the src/ subdirectory path so python resolves pipeline package scripts effortlessly
sys.path.append(os.path.join(root_dir, "src"))

from pipeline import execute_full_pipeline

if __name__ == "__main__":
    # Fire the orchestrated workflow
    pipeline_success = execute_full_pipeline()
    
    # Enforce standard system exit signaling rules for production integration
    if not pipeline_success:
        print("\n[STOP] Pipeline execution exited with errors.")
        sys.exit(1)
        
    print("\n[COMPLETE] Script terminated normally with system code 0.")
    sys.exit(0)