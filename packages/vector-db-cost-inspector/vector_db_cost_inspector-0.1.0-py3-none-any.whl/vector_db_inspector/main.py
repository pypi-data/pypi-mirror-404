import os
import sys
import random
from dotenv import load_dotenv
from pinecone import Pinecone
from .cost_inspector.utilities import print_header, print_warning, get_user_input
from .cost_inspector import real_inspector
from .cost_inspector import interactive_auditor

# Common keys used for timestamps in the wild
COMMON_TIME_KEYS = ['created_at', 'timestamp', 'date', 'unix_ts', 'ts', 'created', 'datetime']

if len(sys.argv) > 1 and sys.argv[1] == "--help-me":
    print("Need help optimizing your Vector DB?")
    print("Email me: billychenph@example.com")
    sys.exit(0)

def detect_time_field(index, stats):
    """
    Probes the index to find a likely timestamp field in metadata.
    """
    print(">> Probing index for metadata structure...")
    
    # Try to fetch a few random vectors to inspect metadata
    # Since we can't 'random sample' easily, we use a random vector query
    dimension = stats['dimension']
    
    potential_keys = set()
    
    # Probe 3 times to get a sample
    for _ in range(3):
        try:
            rand_vec = [random.uniform(-0.1, 0.1) for _ in range(dimension)]
            resp = index.query(vector=rand_vec, top_k=5, include_metadata=True)
            for match in resp.get('matches', []):
                if match.get('metadata'):
                    potential_keys.update(match['metadata'].keys())
        except Exception:
            pass # Sallow errors during probing

    if not potential_keys:
        return None

    # Check for exact matches in our common list
    for key in COMMON_TIME_KEYS:
        if key in potential_keys:
            return key
            
    # If no auto-match, ask the user
    print(f"Found metadata keys: {list(potential_keys)}")
    user_key = get_user_input("Which field contains the creation time? (Press Enter if none)")
    
    if user_key and user_key in potential_keys:
        return user_key
        
    return None
def main():
    print_header("VECTOR SAVINGS ESTIMATOR")
    # Load env vars
    load_dotenv(override=True)
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME")

    # CASE 1: No Keys -> Fallback directly to Auditor
    if not api_key or not index_name:
        print_warning("No Pinecone credentials and index name found in environment.")
        print("Switching to INTERACTIVE MODE (Estimator)...")
        interactive_auditor.run_auditor()
        return

    # CASE 2: Keys Found -> Connect and Probe
    try:
        print(f"Connecting to Pinecone Index: {index_name}...")
        pc = Pinecone(api_key=api_key)
        index = pc.Index(index_name)
        stats = index.describe_index_stats()
        
        total_vectors = stats['total_vector_count']
        if total_vectors == 0:
            print("Index is empty. Switching to Interactive Mode to model potential costs.")
            interactive_auditor.run_auditor()
            return

        # Attempt to find time metadata
        time_field = detect_time_field(index, stats)

        if time_field:
            print(f"\n[+] Detected timestamp field: '{time_field}'")
            print(">> Running REAL DATA INSPECTION...")
            real_inspector.run_inspector(index, stats, time_field)
        else:
            print("\n[-] No timestamp metadata found.")
            print(">> Switching to INTERACTIVE AUDITOR (Workload Profiling)...")
            interactive_auditor.run_auditor(default_count=total_vectors)

    except Exception as e:
        print_warning(f"Connection Failed: {e}")
        print("Falling back to Interactive Mode...")
        interactive_auditor.run_auditor()

if __name__ == "__main__":
    # This block allows you to run the script directly while developing:
    # python vector_db_inspector/main.py
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
