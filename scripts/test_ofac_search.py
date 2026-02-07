import sys
import os
import asyncio

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.pathway_service import pathway_service

def test_ofac_search():
    print("Testing OFAC Sanctions Search...")
    
    # Ensure OFAC stream is initialized (it might be lazy or async, but create_ofac_stream is sync)
    pathway_service.create_ofac_stream()
    
    # Test with a known name from the CSV (viewed earlier: "AEROCARIBBEAN AIRLINES")
    query = "AERO"
    print(f"Searching for: {query}")
    
    try:
        # Debugging: call internal logic directly to see DF
        import pandas as pd
        csv_path = os.path.join(pathway_service.data_dir, "ofac_sdn.csv")
        df = pd.read_csv(csv_path, 
                             names=["ent_num", "SDN_Name", "SDN_Type", "Program", "Title", "Call_Sign", 
                                    "Vess_type", "Tonnage", "GRT", "Vess_flag", "Vess_owner", "Remarks"],
                             header=None,
                             dtype=str)
        print("DEBUG: DataFrame Head:")
        print(df.head())
        print(f"DEBUG: 'SDN_Name' column values: {df['SDN_Name'].head().tolist()}")
        
        results = pathway_service.search_sanctions(query)
        print(f"Found {len(results)} results:")
        for res in results:
            print(f"- {res.get('SDN_Name')} ({res.get('Program')})")
            
        if len(results) > 0:
            print("SUCCESS: Search returned results.")
        else:
            print("WARNING: Search returned no results. Check if CSV exists and is populated.")
            
    except Exception as e:
        print(f"ERROR: Search failed with {e}")

if __name__ == "__main__":
    test_ofac_search()
