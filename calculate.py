import streamlit as st
import pandas as pd
import plotly.express as px

import os

# Check if langchain is installed; if not, mock the agent
try:
    from langchain_groq import ChatGroq
    from langchain.schema import HumanMessage
    from dotenv import load_dotenv
    from supabase import create_client, Client

    load_dotenv()
    LANGCHAIN_AVAILABLE = True

    # Initialize Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    supabase_client: Client | None = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
except ImportError:
    LANGCHAIN_AVAILABLE = False
    supabase_client = None

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="IOM Agricultural Emissions Roadmap",
    page_icon="🚜",
    layout="wide"
)

# --- THEME & STYLING ---
st.markdown("""
<style>
    .main { background-color: #f4f7f6; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .recommendation-card { 
        padding: 15px; 
        border-radius: 8px; 
        border-left: 5px solid #2e7d32; 
        background-color: #e8f5e9; 
        margin-bottom: 10px;
    }
    h1, h2, h3 { color: #1b5e20; }
</style>
""", unsafe_allow_html=True)

# --- EMISSION FACTORS (IPCC + DEFRA ALIGNED) ---
EMISSION_FACTORS = {
    "dairy": 3.0,          # tCO2e/year
    "beef": 2.5,           # tCO2e/year
    "sheep": 0.4,          # tCO2e/year
    "fertilizer": 0.01,    # tCO2e/kg
    "feed": 0.5,           # tCO2e/ton
    "electricity": 0.233   # kg CO2/kWh
}

# --- MEASURES DATASET ---
MEASURES_DB = [
    {"name": "Improved Manure Management", "category": "Livestock", "reduction": 0.2, "cost": 10000},
    {"name": "Optimized Feed Efficiency", "category": "Livestock", "reduction": 0.15, "cost": 8000},
    {"name": "Precision Fertilizer Application", "category": "Soil", "reduction": 0.2, "cost": 5000},
    {"name": "Low Emission Slurry Spreading", "category": "Soil", "reduction": 0.25, "cost": 12000},
    {"name": "Renewable Energy Adoption", "category": "Energy", "reduction": 0.3, "cost": 20000}
]

# --- BENCHMARK DATASET ---
def get_benchmark_data():
    return pd.DataFrame({
        "Year": [2024, 2025, 2024, 2025, 2024, 2025],
        "Farm Type": ["Dairy", "Dairy", "Mixed", "Mixed", "Arable", "Arable"],
        "Avg Emissions (tCO2e)": [480, 465, 340, 330, 190, 185]
    })

# --- CORE CALCULATION LOGIC ---
def calculate_emissions(dairy, beef, sheep, fert_kg, feed_tons, kwh):
    livestock = (dairy * EMISSION_FACTORS["dairy"]) + (beef * EMISSION_FACTORS["beef"]) + (sheep * EMISSION_FACTORS["sheep"])
    fertilizer = fert_kg * EMISSION_FACTORS["fertilizer"]
    feed = feed_tons * EMISSION_FACTORS["feed"]
    energy = (kwh * EMISSION_FACTORS["electricity"]) / 1000  # kWh to ton conversion
    
    total = livestock + fertilizer + feed + energy
    
    return {
        "Livestock": livestock,
        "Fertilizer": fertilizer,
        "Feed": feed,
        "Energy": energy,
        "Total": total
    }

def get_scenarios(base_total):
    return {
        "Business as Usual (BAU)": base_total,
        "Moderate Ambition (-15%)": base_total * 0.85,
        "High Ambition (-35%)": base_total * 0.65
    }

def main():
    st.title("🌱 IOM Agricultural Emissions Roadmap (2027–2032)")
    st.markdown("### Decision Support Tool for Active Farming Practices")
    st.divider()

    # --- 1. FARM INPUTS (SIDEBAR) ---
    with st.sidebar:
        st.header("📋 Farm Inputs")
        farm_type = st.selectbox("Farm Type", ["Dairy", "Mixed", "Arable"])
        
        st.subheader("🐄 Livestock Count")
        dairy = st.number_input("Dairy Cattle", min_value=0, value=150, step=10)
        beef = st.number_input("Beef Cattle", min_value=0, value=100, step=10)
        sheep = st.number_input("Sheep", min_value=0, value=500, step=50)
        
        st.subheader("🚜 Nutrient & Feed")
        fert_kg = st.number_input("Fertilizer Usage (kg/year)", min_value=0, value=8000, step=500)
        feed_tons = st.number_input("Feed Usage (tons/year)", min_value=0, value=200, step=10)
        
        st.subheader("⚡ Farm Inputs")
        kwh = st.number_input("Energy Consumption (kWh/year)", min_value=0, value=15000, step=500)
        
        st.info("Excluded: Land-use change & Tree planting")

        # Supabase Connection Verification
        if supabase_client:
            st.success("✅ Supabase Connected")
        else:
            st.warning("⚠️ Supabase not connected. Please set SUPABASE_URL and SUPABASE_KEY in .env")

    # Perform calculations
    emissions_data = calculate_emissions(dairy, beef, sheep, fert_kg, feed_tons, kwh)
    scenarios = get_scenarios(emissions_data["Total"])
    
    benchmark_df = get_benchmark_data()
    avg_benchmark = benchmark_df.loc[benchmark_df["Farm Type"] == farm_type, "Avg Emissions (tCO2e)"].mean()

    # --- 2. EMISSIONS RESULTS ---
    st.header("2. Emissions Results")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Emissions", f"{emissions_data['Total']:.1f} tCO2e/yr")
    c2.metric("Livestock Impact", f"{emissions_data['Livestock']:.1f} tCO2e/yr")
    c3.metric(f"Avg {farm_type} Benchmark", f"{avg_benchmark:.1f} tCO2e/yr", delta=f"{emissions_data['Total'] - avg_benchmark:.1f} vs Avg", delta_color="inverse")
    c4.metric("Current Scenario", "BAU")

    # Breakdown Chart & Highest Source
    col1, col2 = st.columns([1, 1])
    
    breakdown_df = pd.DataFrame({
        "Category": ["Livestock", "Fertilizer", "Feed", "Energy"],
        "Emissions (tCO2e)": [emissions_data["Livestock"], emissions_data["Fertilizer"], emissions_data["Feed"], emissions_data["Energy"]]
    })
    
    highest_source = breakdown_df.loc[breakdown_df["Emissions (tCO2e)"].idxmax()]

    with col1:
        st.subheader("Emissions Breakdown")
        fig_pie = px.pie(breakdown_df, values="Emissions (tCO2e)", names="Category", hole=0.4, color_discrete_sequence=px.colors.sequential.Greens_r)
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with col2:
        st.subheader("Key Insight")
        st.warning(f"⚠️ Your highest emission source is **{highest_source['Category']}** ({highest_source['Emissions (tCO2e)']:.1f} tCO2e).")
        st.write(f"Focusing mitigation efforts on {highest_source['Category'].lower()} management will yield the highest impact on your farm's carbon footprint.")


    # --- 3. SCENARIO ANALYSIS ---
    st.divider()
    st.header("3. Scenario Analysis (Roadmap 2027-2032)")
    
    scenario_df = pd.DataFrame(list(scenarios.items()), columns=["Scenario", "Total Emissions (tCO2e)"])
    fig_bar = px.bar(scenario_df, x="Scenario", y="Total Emissions (tCO2e)", color="Scenario",
                     color_discrete_map={"Business as Usual (BAU)": "#e57373", "Moderate Ambition (-15%)": "#81c784", "High Ambition (-35%)": "#2e7d32"})
    st.plotly_chart(fig_bar, use_container_width=True)

    # --- 4. RECOMMENDATIONS ---
    st.divider()
    st.header("4. Recommendations & Decision Support")
    
    # Calculate scores for measures based on user's highest emissions
    recommendations = []
    for m in MEASURES_DB:
        category_emissions = 0
        if m["category"] == "Livestock": category_emissions = emissions_data["Livestock"]
        elif m["category"] == "Soil": category_emissions = emissions_data["Fertilizer"]
        elif m["category"] == "Energy": category_emissions = emissions_data["Energy"]
        
        annual_reduction = category_emissions * m["reduction"]
        score = annual_reduction / m["cost"] if m["cost"] > 0 else 0
        
        recommendations.append({
            "name": m["name"],
            "category": m["category"],
            "annual": annual_reduction,
            "cost": m["cost"],
            "score": score
        })
        
    # Sort by cost-effectiveness
    top_measures = sorted(recommendations, key=lambda x: x["score"], reverse=True)[:3]
    
    st.markdown("Top 3 most cost-effective measures for your farm based on **Reduction per £**:")
    
    cols = st.columns(3)
    for i, measure in enumerate(top_measures):
        lifetime_reduction = measure["annual"] * 10
        with cols[i]:
            st.markdown(f'''
            <div class="recommendation-card">
                <h4>{measure['name']}</h4>
                <p><b>Target:</b> {measure['category']}</p>
                <p><b>Annual Reduction:</b> {measure['annual']:.2f} tCO2e/yr</p>
                <p><b>10-yr Reduction:</b> {lifetime_reduction:.1f} tCO2e</p>
                <p><b>Est. Cost:</b> £{measure['cost']:,}</p>
                <p><b>Cost Efficiency:</b> {(measure['cost']/measure['annual'] if measure['annual']>0 else 0):.0f} £/tCO2e</p>
            </div>
            ''', unsafe_allow_html=True)


    # --- 5. ADVISORY AGENT ---
    st.divider()
    st.header("🤖 Agricultural AI Advisor")
    user_question = st.text_input("Ask a question (e.g., 'What is the best option for my farm?')")
    
    if user_question:
        if LANGCHAIN_AVAILABLE and os.getenv("GROQ_API_KEY"):
            try:
                llm = ChatGroq(temperature=0.2, model_name="llama3-8b-8192")
                context = f"Farm Type: {farm_type}, Total Emissions: {emissions_data['Total']:.1f} tCO2e. Highest source: {highest_source['Category']}. Top measure: {top_measures[0]['name']}."
                response = llm([HumanMessage(content=f"Context: {context}. Question: {user_question} Please answer concisely as an IOM agricultural consultant.")])
                st.info(response.content)
            except Exception as e:
                st.error("Error communicating with AI agent. Please check your GROQ_API_KEY.")
        else:
            st.info("Simulated Agent Response: Focusing on {} is your most cost-effective strategy, offering {:.1f} tCO2e annual reduction for an estimated £{}.".format(
                top_measures[0]['name'], top_measures[0]['annual'], top_measures[0]['cost']))

    # --- 6. SAVE TO DATABASE ---
    st.divider()
    st.header("💾 Record Data")
    if st.button("Save Farm Data to Supabase"):
        if supabase_client:
            try:
                record = {
                    "farm_type": farm_type,
                    "dairy_cattle": dairy,
                    "beef_cattle": beef,
                    "sheep": sheep,
                    "fertilizer_kg": fert_kg,
                    "feed_tons": feed_tons,
                    "energy_kwh": kwh,
                    "total_emissions": emissions_data["Total"],
                    "highest_source": highest_source['Category']
                }
                
                # Assume table exists named 'farm_emissions'
                response = supabase_client.table("farm_emissions").insert(record).execute()
                st.success("Successfully saved to Supabase (farm_emissions table)!")
            except Exception as e:
                st.error(f"Error saving to database: {str(e)}")
        else:
            st.error("Cannot save data: Supabase credentials are not configured in .env")

if __name__ == "__main__":
    main()
