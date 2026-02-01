import random
import statistics
import datetime
import time
from .utilities import print_header, print_success, print_money, print_cta

def run_inspector(index, stats, time_field):
    """
    Scans real data to calculate staleness distribution.
    """
    total_vectors = stats['total_vector_count']
    dimension = stats['dimension']
    
    print_header("PHASE 2: STATISTICAL SAMPLING")
    print(f"Sampling index for '{time_field}' distribution...")

    timestamps = []
    
    # We probe 50 random sectors of the vector space
    sample_size = 50
    for i in range(sample_size):
        rand_vec = [random.uniform(-1, 1) for _ in range(dimension)]
        try:
            resp = index.query(vector=rand_vec, top_k=5, include_metadata=True)
            for match in resp['matches']:
                md = match.get('metadata', {})
                if time_field in md:
                    ts = float(md[time_field])
                    # Handle milliseconds vs seconds
                    if ts > 4000000000: ts = ts / 1000
                    timestamps.append(ts)
        except Exception as e:
            pass
        print(f"\rProbing sector {i+1}/{sample_size}...", end="")
    
    print("\n")
    
    if not timestamps:
        print("Error: Could not retrieve valid timestamps despite detection.")
        return

    # Calculate Stats
    now = time.time()
    ninety_days = 90 * 24 * 60 * 60
    cutoff = now - ninety_days
    
    stale_count = sum(1 for t in timestamps if t < cutoff)
    stale_rate = stale_count / len(timestamps)
    
    oldest = datetime.datetime.fromtimestamp(min(timestamps)).strftime('%Y-%m-%d')
    newest = datetime.datetime.fromtimestamp(max(timestamps)).strftime('%Y-%m-%d')
    
    # Report
    print_header("REAL DATA DIAGNOSTICS")
    print(f"Oldest Record:   {oldest}")
    print(f"Newest Record:   {newest}")
    print(f"Observed Stale%: {stale_rate*100:.1f}% (Vectors > 90 days old)")
    
    # Cost Math
    # Estimated: $100/mo per 1GB RAM (Managed), $0.02/mo per 1GB S3
    est_vectors_stale = int(total_vectors * stale_rate)
    vector_size_gb = (total_vectors * (dimension * 4 + 100)) / 1e9 # rough GB
    
    wasted_gb = vector_size_gb * stale_rate
    monthly_waste = wasted_gb * 100 # Premium RAM cost
    s3_cost = wasted_gb * 0.023
    
    net_savings = monthly_waste - s3_cost

    print("\n=== FINANCIAL IMPACT ===")
    if net_savings > 10:
        print_success(f"Archivable Data: {est_vectors_stale:,} vectors")
        print_money(f"Potential Monthly Savings: ${net_savings:.2f}")
        print("\nRecommendation: Your data has timestamps. You can automate this TODAY.")
        print_cta(savings_found=true)
    else:
        print("Your index is fresh. No significant savings available.")
        print_cta()
