import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="IOM Carbon Reduction Calculator",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- THEME & STYLING ---
st.markdown("""
    <style>
    .main {
        background-color: #f9fbf9;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border: 1px solid #e0e6e0;
    }
    .stMetric label {
        color: #2e7d32 !important;
        font-weight: 700 !important;
    }
    h1, h2, h3 {
        color: #1b5e20;
        font-family: 'Helvetica Neue', sans-serif;
    }
    .sidebar .sidebar-content {
        background-color: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CORE LOGIC & DATA ---

def get_baseline_factors():
    """Returns standard IPCC/DEFRA emission factors for calculation."""
    return {
        "cattle_ch4": 2.5,          # tCO2e/cow/year
        "fertilizer_n2o": 0.01,     # tCO2e/kg
        "grid_electricity": 0.233,   # kg CO2/kWh
        "tree_seq": 0.02,           # tCO2/tree/year
        "soil_seq": 1.0              # tCO2/hectare/year
    }

def get_measures_dataset():
    """Embedded dataset for the Recommendation Engine."""
    return [
        {"name": "Improved Manure Management", "category": "Livestock", "reduction": 0.2, "cost": 10000},
        {"name": "Precision Fertilizer Use", "category": "Fertilizer", "reduction": 0.15, "cost": 5000},
        {"name": "Solar Installation", "category": "Energy", "reduction": 0.5, "cost": 20000},
        {"name": "Tree Planting", "category": "Sequestration", "reduction": 0.3, "cost": 3000}
    ]

def calculate_results(cattle, fert_kg, kwh, land, trees, scenario="Business as Usual"):
    """
    Main calculation engine based on provided formulas.
    Scenarios adjust inputs slightly to simulate different ambition levels.
    """
    factors = get_baseline_factors()
    
    # Scenario Scaling (Hypothetical modifiers for comparison)
    scale = 1.0
    if scenario == "Moderate": scale = 0.85
    elif scenario == "High Ambition": scale = 0.65

    # 1. Livestock Emissions
    livestock = (cattle * factors["cattle_ch4"]) * scale
    
    # 2. Fertilizer Emissions
    fertilizer = (fert_kg * factors["fertilizer_n2o"]) * scale
    
    # 3. Energy Emissions
    energy = ((kwh * factors["grid_electricity"]) / 1000) * scale
    
    # 4. Total Emissions
    total_emissions = livestock + fertilizer + energy
    
    # 5. Sequestration
    trees_seq = trees * factors["tree_seq"]
    soil_seq = land * factors["soil_seq"]
    sequestration = trees_seq + soil_seq
    
    # 6. Renewable Reduction (Assumes replacing grid energy)
    renewable = energy
    
    # 7. Net Emissions
    net_emissions = total_emissions - (sequestration + renewable)
    
    return {
        "livestock": livestock,
        "fertilizer": fertilizer,
        "energy": energy,
        "total": total_emissions,
        "sequestration": sequestration,
        "renewable": renewable,
        "net": net_emissions
    }

# --- STREAMLIT UI ---

def main():
    # --- HEADER ---
    st.title("Isle of Man Carbon Emissions Reduction Calculator")
    st.markdown("##### Accurate greenhouse gas estimation and mitigation modeling for the agricultural and residential sectors.")
    st.divider()

    # --- SIDEBAR INPUTS ---
    with st.sidebar:
        st.header("⚙️ Configuration")
        scenario = st.selectbox("Current Scenario", ["Business as Usual", "Moderate", "High Ambition"])
        
        st.subheader("🐄 Agriculture")
        cattle = st.number_input("Number of Cattle", min_value=0, value=120, step=10)
        fert_kg = st.number_input("Fertilizer Usage (kg/year)", min_value=0, value=4500, step=100)
        
        st.subheader("🔌 Energy & Land")
        kwh = st.number_input("Energy Consumption (kWh/year)", min_value=0, value=12000, step=500)
        land = st.number_input("Land Area (hectares)", min_value=0.0, value=45.0, step=1.0)
        trees = st.number_input("Trees Planted", min_value=0, value=350, step=50)
        
        st.info("💡 Factors based on IPCC and UK DEFRA 2023 standards.")

    # --- DATA PROCESSING ---
    results = calculate_results(cattle, fert_kg, kwh, land, trees, scenario)
    
    # --- KEY PERFORMANCE INDICATORS ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Emissions", f"{results['total']:.2f} tCO2e")
    
    with col2:
        reduction_val = results['sequestration'] + results['renewable']
        st.metric("Reduction Potential", f"{reduction_val:.2f} tCO2e", delta=f"{reduction_val / results['total'] * 100:.1f}% of total")
        
    with col3:
        st.metric("Net Carbon Balance", f"{results['net']:.2f} tCO2e", delta_color="inverse")

    st.divider()

    # --- VISUALIZATIONS ---
    tab1, tab2 = st.tabs(["📊 Emissions Analysis", "📉 Scenario Comparison"])
    
    with tab1:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.subheader("Emissions Breakdown")
            pie_data = pd.DataFrame({
                "Category": ["Livestock (CH4)", "Fertilizer (N2O)", "Energy (CO2)"],
                "Value": [results['livestock'], results['fertilizer'], results['energy']]
            })
            fig_pie = px.pie(
                pie_data, values="Value", names="Category",
                color_discrete_sequence=px.colors.sequential.Greens_r,
                hole=0.5
            )
            fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with c2:
            st.subheader("Balance Analysis")
            balance_data = pd.DataFrame({
                "Type": ["Gross Emissions", "Sequestration", "Renewable Offset"],
                "Amount": [results['total'], -results['sequestration'], -results['renewable']]
            })
            fig_bar = px.bar(
                balance_data, x="Type", y="Amount", 
                color="Type", color_discrete_map={"Gross Emissions": "#e57373", "Sequestration": "#81c784", "Renewable Offset": "#64b5f6"}
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        st.subheader("Multi-Scenario Benchmark")
        # Generate scenarios
        scenarios = ["Business as Usual", "Moderate", "High Ambition"]
        comp_list = []
        for s in scenarios:
            res = calculate_results(cattle, fert_kg, kwh, land, trees, s)
            comp_list.append({"Scenario": s, "Net Emissions": res['net']})
        
        comp_df = pd.DataFrame(comp_list)
        fig_comp = px.line(comp_df, x="Scenario", y="Net Emissions", markers=True, line_shape="spline")
        fig_comp.update_traces(line_color="#2e7d32", line_width=4, marker_size=12)
        st.plotly_chart(fig_comp, use_container_width=True)

    # --- BEST MEASURES ENGINE ---
    st.header("🧠 Recommendation Engine: Top Mitigation Measures")
    st.markdown("Prioritized strategies based on marginal abatement cost and reduction efficiency.")
    
    measures = get_measures_dataset()
    for m in measures:
        # Calculate impact based on category
        impact_base = 0
        if m['category'] == "Livestock": impact_base = results['livestock']
        elif m['category'] == "Fertilizer": impact_base = results['fertilizer']
        elif m['category'] == "Energy": impact_base = results['energy']
        elif m['category'] == "Sequestration": impact_base = results['sequestration']
        
        m['potential_reduction'] = impact_base * m['reduction']
        m['score'] = m['potential_reduction'] / m['cost'] if m['cost'] > 0 else 0

    # Sort by score and take top 3
    recommended = sorted(measures, key=lambda x: x['score'], reverse=True)[:3]
    
    rec_cols = st.columns(3)
    for i, rec in enumerate(recommended):
        with rec_cols[i]:
            st.success(f"**{rec['name']}**")
            st.write(f"**Category:** {rec['category']}")
            st.write(f"**Est. Saving:** {rec['potential_reduction']:.2f} tCO2e/yr")
            st.write(f"**Implementation Cost:** £{rec['cost']:,}")
            st.progress(min(rec['score'] * 1000, 1.0)) # Visualizing efficiency score

    st.divider()
    st.caption("© 2024 Isle of Man Climate Analytics Tool. Built with Streamlit.")

if __name__ == "__main__":
    main()
