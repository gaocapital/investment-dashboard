# main.py  ─────────────────────────────────────────────────────
import time
import threading
from pathlib import Path
import pythoncom
from flask import Flask, render_template
import pandas as pd

from src.data_fetch import fetch_data
from src.models.spx_barometer import process_spx_barometer, plot_spx_barometer
# from src.models.other_model import process_other, plot_other

# ── Model registry ────────────────────────────────────────────
MODEL_REGISTRY = {
    "spx_barometer": {
        "display_name": "Equities Forward-Sharpe Barometer",
        "file": "spx_barometer.xlsx",
        "processor": process_spx_barometer,
        "plotter": plot_spx_barometer,
    },
    # add more models here …
}

# ── Shared store that Flask will read ─────────────────────────
latest_outputs: dict[str, dict] = {}

# ── Run all models once and update globals ────────────────────
def run_all_models() -> None:
    global latest_outputs
    new_dict: dict[str, dict] = {}

    for key, info in MODEL_REGISTRY.items():
        data_dict = fetch_data(info["file"])
        if not data_dict:
            print(f"⚠ {info['display_name']} returned no data")
            continue

        processed = info["processor"](data_dict)
        print(processed)
        html_plot = info["plotter"](processed)

        new_dict[key] = {
            "display_name": info["display_name"],
            "data": processed,
            "plot": html_plot,
        }

    latest_outputs = new_dict


# ── Background thread: refresh once every 24 h ────────────────
def pipeline_loop():
    pythoncom.CoInitialize()
    try:
        while True:
            print("🔄  Refreshing models …")
            run_all_models()
            print("✅  Models refreshed; sleeping 24 h")
            time.sleep(86_400)            # 24 hours
    finally:
        pythoncom.CoUninitialize()


# ── Flask app ─────────────────────────────────────────────────
TEMPL_DIR = Path(__file__).parent / "templates"

app = Flask(__name__, template_folder=str(TEMPL_DIR))

@app.route("/")
def index():
    return render_template("index.html", latest_outputs=latest_outputs)

def start_flask():
    # listen on all interfaces so LAN machines can reach it
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)


# ── Main entry ────────────────────────────────────────────────
if __name__ == "__main__":
    run_all_models()                                            # first load

    threading.Thread(target=pipeline_loop, daemon=True).start() # refresh thread
    threading.Thread(target=start_flask,  daemon=True).start() # web server thread

    print("🌐  Visit http://192.168.10.88:5000/  (or http://127.0.0.1:5000/)")

    # keep main process alive
    while True:
        time.sleep(60)
