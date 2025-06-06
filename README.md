# 📊 GAO Capital Strategy Dashboard

A modular, real-time financial dashboard built with Python and Flask. This project reads data from strategy-specific Excel files (including Bloomberg BQL outputs), processes them using Python model scripts, and renders key metrics through an interactive web interface.

---

## 📌 Overview

The dashboard is designed for:

- Monitoring performance and metrics of multiple investment strategies in real-time.
- Simplifying integration with Excel-based financial models.
- Enabling easy extension for new strategy models.
- Supporting institutional-level customization and investor-friendly presentation.

---

## 🧠 How It Works

Each strategy (Rates, Commodities, etc.) has a Python script that:
- Reads the corresponding .xlsx file from the data/ folder.
- Parses, processes, and computes metrics.
- Feeds this data to the Flask app.

Flask renders all output in a web-based dashboard, refreshing regularly based on a timer.

---

## 🧱 Architecture

- **Backend**: Python + Flask
- **Frontend**: Jinja2 templates (HTML) + Bootstrap (optional styling)
- **Data Source**: `.xlsx` files exported from Bloomberg Excel / BQL formulas
- **Modularity**: Each strategy has its own processing script and source data file
- **Auto-Update**: Backend refreshes data periodically
---

## 📂 Project Structure

investment-dashboard-main/
│
├── main.py # Run this script
├── templates/
│ └── dashboard.html # Main HTML template
├── descriptions/ # Markdown files explaining the logic and usage of each model
│ ├── spx_barometer/
│   ├── spx_barometer.md
│   └── images/ # store images for model description here
│ └── ... # Add future model descriptions here
├── src/
│ ├── data_fetch.py # Extracting data Excel/BQL files for corresponding model
│ └── models/
│   ├── spx_barometer.py
│   └── ... # Add future models here
├── data/ # Source Excel/BQL files
│ ├── spx_barometer.xlsx
│ └── ... # Add future data here
├── requirements.txt # Python dependencies
└── LICENSE.txt # MIT license

---

## 🏃 Running the Dashboard

Navigate to the project directory on command prompt/terminal and install dependencies:
```bash 
pip install -r requirements.txt
```
Run the main file:
```bash 
python main.py
```
Open your browser and navigate to [http://192.168.10.88:5000/], where you’ll see a dynamic dashboard with summary outputs from each strategy, which updates daily.

*Note: Currently only accessible within local network, working on live implementations*

## ✍️ Adding a new model
To integrate a new strategy (e.g. Tactical Trading), follow these steps:

**1. Create a New Data File**
Save your Bloomberg/BQL file as an Excel file with the model name (e.g. tactical_trading.xlsx) and place it in the /data directory. It should contain live BQL prompts such that data can be drawn from Bloomberg at regular intervals.

**2. Create a Model Script**
In /models, create your Python model (e.g. tactical_trading.py) which requires the following methods:
A. `process_tactical_trading(raw_df)`: Processes the raw data from the BQL Excel file and outputs the processed data to be displayed.
B. `plot_tactical_trading(processed_df)`: Creates the plot(s) to visualise the processed data using Plotly and outputs the plots as a html object

**3. Import model into main.py**
In main.py, import your new model and add it to the `MODEL_RESGISTRY` dictionary:
```python
from src.models.tactical_trading import process_tactical_trading, plot_tactical_trading

MODEL_REGISTRY = {
    #...
    "tactical_trading": {
        "display_name": "Tactical Trading Insights",
        "file": "tactical_trading.xlsx",
        "processor": process_tactical_trading,
        "plotter": plot_tactical_trading,
    },
}
```

After this step, run the dashboard again and your model's plot will be displayed on the webapp.

---

## 🧠 Editing the Dashboard Template
The main dashboard layout is in templates/dashboard.html. You can edit the styl (e.g. font, colour, etc.) of the dashboard under `<style>` and the main layout under `<body>`.

---

## 📅 Roadmap

- Live web implementation and authentication
- One-day economic snapshot
- Alerts/threshold logic for extreme signals

---

## 👨‍💼 Maintainer

Royce Lim
Associate, GAO Capital
Contact: associates@gao-cap.com / royce@gao-adv.com

---

## 📄 License

This project is licensed under the [MIT License](./LICENSE.txt).

