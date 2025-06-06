import requests
from datetime import date, timedelta

BASE_URL = "http://localhost:8000"
EXPERIMENT_ID = "panel_demo"

def run_demo():
    print("=== Multi-Armed Bandit API Demonstration ===")
    
    # 1. Initialize test data
    print("\n1. Adding sample metrics for 3 variants...")
    variants = ["control", "variant1", "variant2"]
    today = date.today()
    
    for i in range(3):  # Last 3 days
        for variant in variants:
            successes = {
                "control": 50 + i*5,
                "variant1": 70 + i*10,
                "variant2": 60 + i*7
            }[variant]
            
            requests.post(
                f"{BASE_URL}/metrics/",
                json={
                    "experiment_id": EXPERIMENT_ID,
                    "variant_id": variant,
                    "date": str(today - timedelta(days=2-i)),
                    "impressions": 1000,
                    "successes": successes
                }
            )
    
    # 2. Show current allocations
    print("\n2. Getting recommended allocations for tomorrow...")
    response = requests.get(
        f"{BASE_URL}/allocations/{EXPERIMENT_ID}?for_date={today + timedelta(days=1)}"
    )
    allocations = response.json()
    
    print("Recommended traffic distribution:")
    for variant, percentage in allocations["allocations"].items():
        print(f"- {variant}: {percentage:.1f}%")
    
    # 3. Show the algorithm is working
    print("\n3. Analysis:")
    print("Variant1 performed best historically, so it gets highest allocation")
    print("The system automatically balances exploration/exploitation")

if __name__ == "__main__":
    run_demo()