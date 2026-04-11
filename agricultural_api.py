from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import os
import random
from typing import List
from datetime import datetime

# --- Supabase Initialization ---
from dotenv import load_dotenv

# Load local .env file if it exists
load_dotenv()

SUPABASE_AVAILABLE = False
supabase_client = None

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://hnbtaawkwpozougvgrmw.supabase.co").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_qnq9Vu2Etv17Yedu2oD44w_txHj-Cxw").strip()

try:
    from supabase import create_client, Client
    
    if SUPABASE_URL and SUPABASE_KEY:
        supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        SUPABASE_AVAILABLE = True
        print("Supabase connected successfully.")
    else:
        print("INFO: SUPABASE_URL or SUPABASE_KEY not found in environment. Running without database storage.")
except ImportError:
    print("INFO: supabase package not installed. Running without database storage.")
except Exception as e:
    print(f"Failed to initialize Supabase. Error: {e}")

# Attempt to import ML dependencies (assuming pandas, scikit-learn are in requirements)
try:
    import pandas as pd
    import numpy as np
    from sklearn.preprocessing import LabelEncoder
    from sklearn.ensemble import RandomForestRegressor
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

# --- ML Model Initialization ---
ML_MODELS_READY = False
models = {}
label_encoders = {}
numeric_cols = [
    'Annual Reduction (tCO2e/yr)',
    'Implementation Cost (£)',
    'Cost/Tonne (£/tCO2e)',
    'Cost Savings (£/yr)'
]
input_columns = ['Category', 'Phase', 'Scenario', 'Implementation Cost (£)', 'Time', 'Feasibility', 'Delivery', 'Action']
output_columns = ['Annual Reduction (tCO2e/yr)', 'Lifetime Reduction (tCO2e)', 'Cost/Tonne (£/tCO2e)', 'Cost Savings (£/yr)', 'Adoption (%)']

def clean_numeric_column(df_target, column_name):
    if column_name in df_target.columns and df_target[column_name].dtype == 'object':
        cleaned_series = df_target[column_name].astype(str).str.replace(r'[£,]', '', regex=True)
        numeric_part = cleaned_series.str.extract(r'(-?\d+\.?\d*)')[0]
        df_target[column_name] = pd.to_numeric(numeric_part, errors='coerce').fillna(0)
    return df_target

def train_models():
    global ML_MODELS_READY, models, label_encoders
    if not ML_AVAILABLE:
        print("ML libraries not installed. Using Mock Predictions.")
        return
    
    file_to_read = 'agriculture_emissions_dataset.xlsx'
    if not os.path.exists(file_to_read):
        print(f"INFO: Dataset '{file_to_read}' not found. Running in Simulated Prediction mode.")
        return
        
    try:
        df = pd.read_excel(file_to_read)
        
        # Check if required columns exist (case-insensitive check might be better but let's stick to exact for now)
        missing_inputs = [col for col in input_columns if col not in df.columns]
        missing_outputs = [col for col in output_columns if col not in df.columns]
        
        if missing_inputs or missing_outputs:
            print(f"Dataset is missing columns: {missing_inputs + missing_outputs}. Using Mock Predictions.")
            return

        for col_name in numeric_cols:
            df = clean_numeric_column(df, col_name)
            
        for col in input_columns:
            if df[col].dtype == 'object':
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col].astype(str))
                label_encoders[col] = le
                
        for target in output_columns:
            X = df[input_columns]
            y = df[target]
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X, y)
            models[target] = model
            
        ML_MODELS_READY = True
        print("ML Models successfully trained from Excel dataset.")
    except Exception as e:
        print(f"Failed to train ML models: {e}. Using Mock Predictions.")

# Train models on startup
train_models()

# --- Configuration ---

# Initialize FastAPI App
app = FastAPI(
    title="Agricultural Emissions Reduction Tool",
    description="Backend API to predict, collect and retrieve Agricultural emissions reduction data.",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Data Models ---

class PredictionInput(BaseModel):
    category: str = Field(..., example="Livestock")
    phase: str = Field(..., example="Phase 1")
    scenario: str = Field(..., example="High")
    implementation_cost: float = Field(..., example=50000.0)
    time: str = Field(..., example="Long")
    feasibility: str = Field(..., example="Medium")
    delivery: str = Field(..., example="Subsidy")
    action: str = Field(..., example="Long")

# --- Helper: Save to Supabase ---
def save_to_supabase(input_data: dict, predictions: dict, mode: str):
    """Save prediction input and results to Supabase. Fails silently if unavailable."""
    if not SUPABASE_AVAILABLE:
        return
    try:
        record = {
            "category": input_data.get("category", ""),
            "phase": input_data.get("phase", ""),
            "scenario": input_data.get("scenario", ""),
            "implementation_cost": input_data.get("implementation_cost", 0),
            "time": input_data.get("time", ""),
            "feasibility": input_data.get("feasibility", ""),
            "delivery": input_data.get("delivery", ""),
            "action": input_data.get("action", ""),
            "annual_reduction": predictions.get("annual_reduction", 0),
            "lifetime_reduction": predictions.get("lifetime_reduction", 0),
            "cost_per_tonne": predictions.get("cost_per_tonne", 0),
            "cost_savings": predictions.get("cost_savings", 0),
            "adoption": predictions.get("adoption", 0),
            "mode": mode,
            "created_at": datetime.utcnow().isoformat()
        }
        supabase_client.table("predictions").insert(record).execute()
        print("Prediction saved to Supabase.")
    except Exception as e:
        print(f"Warning: Failed to save to Supabase: {e}")

# --- API Endpoints ---
@app.post("/predict", tags=["AI Prediction"])
async def predict_emissions(data: PredictionInput):
    """
    Predict agricultural emission reductions based on input parameters.
    Uses Random Forest if trained, otherwise uses a smart fallback formulation.
    Results are saved to Supabase if configured.
    """
    input_dict = data.dict()

    if ML_MODELS_READY:
        try:
            # Prepare data
            new_data = pd.DataFrame([{
                'Category': data.category,
                'Phase': data.phase,
                'Scenario': data.scenario,
                'Implementation Cost (£)': data.implementation_cost,
                'Time': data.time,
                'Feasibility': data.feasibility,
                'Delivery': data.delivery,
                'Action': data.action
            }])
            
            # Encode strings
            for col in new_data.columns:
                if col in label_encoders:
                    if new_data[col].iloc[0] not in label_encoders[col].classes_:
                        new_data[col] = label_encoders[col].transform([label_encoders[col].classes_[0]])
                    else:
                        new_data[col] = label_encoders[col].transform(new_data[col].astype(str))
                elif col in numeric_cols:
                    new_data[col] = new_data[col].astype(float)
            
            # Predict
            results = {}
            for target, model in models.items():
                results[target] = float(model.predict(new_data)[0])
            
            predictions = {
                "annual_reduction": results['Annual Reduction (tCO2e/yr)'],
                "lifetime_reduction": results['Lifetime Reduction (tCO2e)'],
                "cost_per_tonne": results['Cost/Tonne (£/tCO2e)'],
                "cost_savings": results['Cost Savings (£/yr)'],
                "adoption": results['Adoption (%)']
            }
            mode = "ML Engine"
            save_to_supabase(input_dict, predictions, mode)
            return {"status": "success", "mode": mode, "predictions": predictions}
        except Exception as e:
            print(f"ML Predict failed: {e}. Falling back to mock calculation.")
    
    # MOCK PREDICTIONS (Fallback algorithm when dataset not present)
    base_reduction = data.implementation_cost * 0.00015
    multiplier = 1.0
    if data.scenario == "High": multiplier = 1.4
    elif data.scenario == "Low": multiplier = 0.6
    
    annual = base_reduction * multiplier * random.uniform(0.8, 1.2)
    lifetime = annual * (15 if data.time == "Long" else 5 if data.time == "Medium" else 2)
    
    adoption = 40 + (25 if data.feasibility == "High" else 10 if data.feasibility == "Medium" else -10)
    if data.delivery == "Subsidy" or data.delivery == "Grant":
        adoption += 15

    predictions = {
        "annual_reduction": round(annual, 2),
        "lifetime_reduction": round(lifetime, 2),
        "cost_per_tonne": round((data.implementation_cost / max(1, lifetime)), 2),
        "cost_savings": round(annual * 45 * random.uniform(0.9, 1.1), 2),
        "adoption": round(min(max(adoption, 0), 100), 2)
    }
    mode = "Simulated Override (Dataset Missing)"
    save_to_supabase(input_dict, predictions, mode)
    return {"status": "success", "mode": mode, "predictions": predictions}


@app.get("/history", tags=["History"])
async def get_history(limit: int = 50):
    """
    Retrieve past prediction records from Supabase.
    Returns the most recent predictions, newest first.
    """
    if not SUPABASE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not configured. Set SUPABASE_URL and SUPABASE_KEY environment variables.")
    try:
        response = supabase_client.table("predictions").select("*").order("created_at", desc=True).limit(limit).execute()
        return {"status": "success", "count": len(response.data), "records": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")


@app.get("/compare-scenarios", tags=["Visualization"])
async def compare_scenarios(
    category: str = "Livestock",
    phase: str = "Phase 1",
    implementation_cost: float = 50000,
    time: str = "Long",
    feasibility: str = "Medium",
    delivery: str = "Subsidy",
    action: str = "Long"
):
    """
    Compare emission reductions across Low, Medium, and High scenarios.
    Returns data formatted for chart visualization.
    """
    scenarios = ["Low", "Medium", "High"]
    comparison = {}
    
    for scenario in scenarios:
        base_reduction = implementation_cost * 0.00015
        multiplier = {"Low": 0.6, "Medium": 1.0, "High": 1.4}[scenario]
        
        annual = base_reduction * multiplier * random.uniform(0.9, 1.1)
        lifetime = annual * (15 if time == "Long" else 5 if time == "Medium" else 2)
        adoption_val = 40 + (25 if feasibility == "High" else 10 if feasibility == "Medium" else -10)
        if delivery in ["Subsidy", "Grant"]:
            adoption_val += 15
        
        comparison[scenario] = {
            "annual_reduction": round(annual, 2),
            "lifetime_reduction": round(lifetime, 2),
            "cost_per_tonne": round((implementation_cost / max(1, lifetime)), 2),
            "cost_savings": round(annual * 45 * random.uniform(0.9, 1.1), 2),
            "adoption": round(min(max(adoption_val, 0), 100), 2)
        }
    
    return {"status": "success", "comparison": comparison}


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to the Agricultural Emissions Reduction Tool API.",
        "supabase_connected": SUPABASE_AVAILABLE,
        "ml_models_ready": ML_MODELS_READY,
        "endpoints": {
            "predict": "POST /predict",
            "history": "GET /history",
            "compare": "GET /compare-scenarios",
            "docs": "GET /docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
