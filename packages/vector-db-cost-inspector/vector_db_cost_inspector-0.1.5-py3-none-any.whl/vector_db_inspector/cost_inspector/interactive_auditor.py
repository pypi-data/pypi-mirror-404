from dataclasses import dataclass
from .utilities import print_header, print_money, get_user_input, print_cta

@dataclass
class WorkloadProfile:
    name: str
    stale_rate: float

PROFILES = {
    "1": WorkloadProfile("GenAI Chat History", 0.90),
    "2": WorkloadProfile("Logs / Observability", 0.98),
    "3": WorkloadProfile("E-Commerce / Catalog", 0.40),
    "4": WorkloadProfile("Core Knowledge Base (RAG)", 0.15)
}

def run_auditor(default_count=None):
    """
    Runs the manual questionnaire.
    """
    print_header("PHASE 2: WORKLOAD MODELING")
    
    # 1. Get Count
    if default_count:
        print(f"Vectors detected: {default_count:,}")
        vector_count = default_count
    else:
        val = get_user_input("Enter estimated total vectors", "1000000")
        vector_count = int(val.replace(",", ""))

    # 2. Get Profile
    print("\nSince we couldn't find timestamps, please select your use case:")
    for k, p in PROFILES.items():
        print(f"  [{k}] {p.name}")
        
    choice = get_user_input("Select profile", "1")
    profile = PROFILES.get(choice, PROFILES["1"])
    
    print(f"\n>> Modeling as: {profile.name} (Est. {int(profile.stale_rate*100)}% Decay)")
    
    # 3. Calculate Logic (Simplified for brevity)
    # Assuming 1536 dimensions
    size_gb = (vector_count * 1536 * 4) / 1e9
    stale_gb = size_gb * profile.stale_rate
    
    ram_cost = stale_gb * 100  # $100/GB/mo premium
    s3_cost = stale_gb * 0.023 # S3 cost
    savings = ram_cost - s3_cost
    
    print_header("ESTIMATED RESULTS")
    print(f"Total Volume:      {size_gb:.2f} GB")
    print(f"Likely Stale:      {stale_gb:.2f} GB")
    print_money(f"Projected Savings: ${savings:.2f} / Month")
    print_cta()
    
    print("\n[!] NOTE: To get an exact number, add a 'created_at' timestamp to your metadata")
    print("    and re-run this tool. We can then inspect the real distribution.")
