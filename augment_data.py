import pandas as pd
import numpy as np
import os

def augment_data_for_iom():
    csv_path = 'agricultural_data.csv'
    if not os.path.exists(csv_path):
        print("CSV not found. Please run data_generator.py first.")
        return

    df = pd.read_csv(csv_path)
    
    # Add Location column if it doesn't exist
    if 'Location' not in df.columns:
        df['Location'] = 'Isle of Man'
    
    # Generate new rows for "Climate Change" category
    num_new_samples = 150
    categories = ['Climate Change']
    phases = ['Phase 1', 'Phase 2', 'Phase 3'] # Added Phase 3 for IOM
    scenarios = ['Business as Usual', 'Moderate Ambition', 'High Ambition', 'Net Zero 2050']
    feasibility = ['Low', 'Medium', 'High', 'Very High']
    delivery = ['Direct Grant', 'Technical Support', 'Policy Regulation', 'Market Mechanism', 'Community Investment']
    actions = ['Short-Term', 'Long-Term', 'Ongoing']

    new_data = {
        'Category': np.random.choice(categories, num_new_samples),
        'Phase': np.random.choice(phases, num_new_samples),
        'Scenario': np.random.choice(scenarios, num_new_samples),
        'Implementation Cost (£)': np.random.uniform(10000, 1000000, num_new_samples),
        'Time': np.random.randint(6, 120, num_new_samples), # More long-term for CC
        'Feasibility': np.random.choice(feasibility, num_new_samples),
        'Delivery': np.random.choice(delivery, num_new_samples),
        'Action': np.random.choice(actions, num_new_samples),
        'Location': 'Isle of Man',
        
        # Output columns
        'Annual Reduction (tCO2e/yr)': np.random.uniform(500, 10000, num_new_samples),
        'Lifetime Reduction (tCO2e)': np.random.uniform(5000, 200000, num_new_samples),
        'Cost/Tonne (£/tCO2e)': np.random.uniform(2, 400, num_new_samples),
        'Cost Savings (£/yr)': np.random.uniform(5000, 250000, num_new_samples),
        'Adoption (%)': np.random.uniform(20, 100, num_new_samples)
    }

    df_new = pd.DataFrame(new_data)
    
    # Combine
    df_combined = pd.concat([df, df_new], ignore_index=True)
    
    # Ensure all columns exist in original df (some might be missing if I just added them to new_data)
    # Actually I should make sure original df has Location
    df_combined.to_csv(csv_path, index=False)
    print(f"Data augmented. Total rows: {len(df_combined)}. Added 'Climate Change' category for Isle of Man.")

if __name__ == "__main__":
    augment_data_for_iom()
