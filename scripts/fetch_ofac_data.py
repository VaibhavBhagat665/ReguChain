import requests
import os
import time
import requests
import os
import time
# import schedule # Imported inside run_scheduler if needed

URL = "https://www.treasury.gov/ofac/downloads/sdn.csv"
# Adjust path to be relative to the script location: ../backend/data
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "ofac_sdn.csv")

def fetch_data():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    print(f"Downloading OFAC SDN List from {URL}...")
    try:
        response = requests.get(URL)
        response.raise_for_status()
        
        # Save to file
        with open(OUTPUT_FILE, 'wb') as f:
            f.write(response.content)
        
        print(f"Successfully saved to {OUTPUT_FILE} at {time.ctime()}")
        return True
    except Exception as e:
        print(f"Error downloading data: {e}")
        return False

def run_scheduler():
    import schedule
    print("Starting OFAC data fetch scheduler (Daily update)...")
    fetch_data() # Run oncd immediately
    
    # Schedule to run every 24 hours
    schedule.every(24).hours.do(fetch_data)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    # If run with --loop argument, start scheduler, else just run once
    import sys
    if "--loop" in sys.argv:
        try:
            import schedule
            run_scheduler()
        except ImportError:
            print("Schedule module not found. Running once. Install with 'pip install schedule'")
            fetch_data()
    else:
        fetch_data()
