try:
    from langchain_groq import ChatGroq
    from langchain.schema import HumanMessage
    from dotenv import load_dotenv
    from supabase import create_client, Client
    import os
    print("Imports passed")
    load_dotenv()
    print("SUPABASE_URL =", os.getenv("SUPABASE_URL"))
    print("SUPABASE_KEY =", os.getenv("SUPABASE_KEY"))
except ImportError as e:
    print("ImportError:", e)
except Exception as e:
    print("Exception:", e)
