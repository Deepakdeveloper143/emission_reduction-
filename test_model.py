from agent_logic import EmissionModel

def test_model():
    model = EmissionModel()
    test_input = {
        'Category': 'Climate Change',
        'Phase': 'Phase 2',
        'Scenario': 'High Ambition',
        'Implementation Cost (£)': 250000,
        'Time': 36,
        'Feasibility': 'High',
        'Delivery': 'Policy Regulation',
        'Action': 'Long-Term',
        'Location': 'Isle of Man'
    }
    prediction = model.predict(test_input)
    print("Test Prediction Results:")
    for k, v in prediction.items():
        print(f"{k}: {v}")

if __name__ == "__main__":
    test_model()
