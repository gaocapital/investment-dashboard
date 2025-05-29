import time
from src.models.spx_barometer import process_spx_barometer
from src.models.vol_signal import process_vol_signal
from src.data_fetch import fetch_data

# Map model keys to their Excel files and processing functions
MODEL_REGISTRY = {
    'spx_barometer': {
        'file': 'spx_barometer.xlsx',
        'processor': process_spx_barometer
    },
    'vol_signal': {
        'file': 'vol_signal.xlsx',
        'processor': process_vol_signal
    },
    # Add more models here
}

def run_all_models():
    results = {}

    for model_name, model_info in MODEL_REGISTRY.items():
        # Fetch data from the corresponding Excel file
        data = fetch_data(model_info['file'])

        # Process the data through the model's processing function
        processed_output = model_info['processor'](data)

        # Store results under the model's name
        results[model_name] = processed_output

    return results

def run_pipeline():
    while True:
        # Run all models
        all_results = run_all_models()

        # Print or store the results for Flask to consume
        print("All model results:", all_results) # To be replaced by Flask connection

        # Sleep before next refresh
        time.sleep(600) # 10-min interval
      
if __name__ == "__main__":
    # Start the pipeline
    run_pipeline()

