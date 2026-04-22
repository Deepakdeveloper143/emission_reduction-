import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase_client: Client | None = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

if supabase_client:
    try:
        record = {
            "Measure Name": "Test",
            "Category": "Livestock",
            "Phase": "Phase 1",
            "Scenario": "Moderate Ambition",
            "Implementation Cost (£)": 50000,
            "Time": 12,
            "Feasibility": "Medium",
            "Delivery": "Direct Grant",
            "Action": "Short-Term",
            "Location": "Isle of Man"
        }
        response = supabase_client.table("agricultural_emissions").insert(record).execute()
        print("Success! Table data:", response.data)
    except Exception as e:
        print("Error:", str(e))
else:
    print("Could not initialize Supabase client.")
