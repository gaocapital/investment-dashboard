# spx_barometer.py
# ---------------------------------------------------------------------------
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ─────────────────────────────────────────────────────────────────────────────
#  Helper: Excel-equivalent RORR
# ─────────────────────────────────────────────────────────────────────────────
def get_rorr(px_last, gr, idx_curr, idx_next):
    """
    Inverts the valuation identity
        r = f(px_last, gr, idx_curr, idx_next)

        Excel formula (row 423, with $B absolute):
        =(
           N  -  B*(1-U/100)
           + SQRT( (B*(1-U/100)-N)^2
                   - 4*B*((U/100)*(N-B) - O )
                 )
         ) / (2*B) * 100

        where
          B -> px_last
          U -> gr              (in percent, e.g. 5 => 0.05)
          O -> idx_curr  (current-year dividend estimate)
          N -> idx_next  (next-year dividend estimate)

    Parameters
    ----------
    px_last   : scalar / array-like
    gr        : growth-rate (percent, NOT decimal)  scalar / array-like
    idx_curr  : current-year dividend estimate      scalar / array-like
    idx_next  : next-year dividend estimate         scalar / array-like

    Returns
    -------
    ndarray or float
        Required rate of return **expressed in percent** (×100),
        or np.nan if the discriminant is negative.
    """
    # broadcast inputs to same shape (works for scalars, Series, arrays)
    B, U, O, N = np.broadcast_arrays(px_last, gr, idx_curr, idx_next)

    # pieces of the quadratic
    term  = B * (1 - U / 100.0)
    disc  = (term - N) ** 2 - 4 * B * ((U / 100.0) * (N - B) - O)

    # negative discriminant → no real solution → NaN
    root  = np.where(disc >= 0, np.sqrt(disc), np.nan)

    numerator   = N - term + root
    denominator = 2 * B

    r_percent = (numerator / denominator) * 100.0
    return r_percent.item() if r_percent.size == 1 else r_percent


# ─────────────────────────────────────────────────────────────────────────────
#  Helper: fix “#N/A Requesting Data…” penultimate row date
# ─────────────────────────────────────────────────────────────────────────────
def fix_na_date(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df["DATE"].iloc[-2], str) and "N/A" in df["DATE"].iloc[-2]:
        df = df.copy()
        df.at[df.index[-2], "DATE"] = (
            pd.to_datetime(df["DATE"].iloc[-1]) - pd.offsets.BDay(1)
        )
    return df


# ─────────────────────────────────────────────────────────────────────────────
#  Core model
# ─────────────────────────────────────────────────────────────────────────────
def process_spx_barometer(data, lookback=30):
    # Reverse the order (assuming data is oldest to newest)
    cleaned_data = data.ffill().iloc[::-1]

    # Fix NA date issue
    cleaned_data = fix_na_date(cleaned_data)

    # Set Datetime index
    cleaned_data = cleaned_data.set_index("DATE")

    # Convert all columns to floats
    cleaned_data = cleaned_data.apply(pd.to_numeric, errors='coerce')
    
    # Drop 'PX_LAST' column for rolling mean on others
    smoothed_data = cleaned_data.drop("PX_LAST", axis=1).rolling(window=lookback).mean()

    # Re-assign 'PX_LAST' values to the smoothed data
    smoothed_data["PX_LAST"] = cleaned_data.loc[smoothed_data.index, "PX_LAST"]

    # Cleaning NaN data
    smoothed_data = smoothed_data.ffill().dropna()

    # Calculate GR (Growth Rate)
    smoothed_data["GR"] = (1 - smoothed_data["DVD_PAYOUT_RATIO"] / 100) * smoothed_data["BEST_ROE"]

    # Calculate RORR using vectorized get_rorr
    smoothed_data["RORR"] = get_rorr(
        smoothed_data["PX_LAST"],
        smoothed_data["GR"],
        smoothed_data["IDX_EST_DVD_CURR_YR"], 
        smoothed_data["IDX_EST_DVD_NXT_YR"], 
    )

    # Calculate ERP
    smoothed_data["ERP"] = smoothed_data["RORR"] - smoothed_data["USGG12M"]

    # Calculate FWD_SHARPE (clip at 0 and 1)
    smoothed_data["FWD_SHARPE"] = smoothed_data["ERP"] / smoothed_data["VOLATILITY_360D"] - 0.1
    smoothed_data["FWD_SHARPE"] = smoothed_data["FWD_SHARPE"].clip(lower=0, upper=1)
    
    # Prepare result
    result = smoothed_data[["PX_LAST", "FWD_SHARPE"]]
    result.columns = ["SPX", "FWD_SHARPE"]

    return result


# ─────────────────────────────────────────────────────────────────────────────
#  Plot: dual-axis line + gauge
# ─────────────────────────────────────────────────────────────────────────────
def plot_spx_barometer(
    df: pd.DataFrame,
    title_line: str = "SPX vs FWD_SHARPE",
) -> str:
    """
    Build the dual-axis SPX-vs-Sharpe line chart + gauge.
    Returns an HTML fragment ready for Flask/Jinja.
    """

    # ── guard ────────────────────────────────────────────────────────────
    if df.empty:
        return "<div style='color:#ccc'>No data available</div>"

    # 🟢 ensure x-axis is a **date** axis in CHRONO order
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, errors="coerce")
    df = df[~df.index.isna()] 
    df = df.sort_index()        # ascending

    # ── subplot scaffold ────────────────────────────────────────────────
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"secondary_y": True}, {"type": "domain"}]],
        column_widths=[0.65, 0.35],
        horizontal_spacing=0.08,
    )

    # ── line chart (left) ───────────────────────────────────────────────
    fig.add_trace(
        go.Scatter(x=df.index, y=df["SPX"],
                   name="SPX", mode="lines", line_color="royalblue"),
        row=1, col=1, secondary_y=False)

    fig.add_trace(
        go.Scatter(x=df.index, y=df["FWD_SHARPE"],
                   name="FWD_SHARPE", mode="lines", line_color="orangered"),
        row=1, col=1, secondary_y=True)

    # dynamic y-axis scaling
    lo, hi = df["SPX"].min(), df["SPX"].max(); pad = 0.05 * (hi - lo)
    fig.update_yaxes(range=[lo - pad, hi + pad], title="SPX", row=1, col=1)
    fig.update_yaxes(range=[0, 1], title="FWD_SHARPE",
                     secondary_y=True, row=1, col=1)

    # 🟢 proper date x-axis with range-slider
    fig.update_xaxes(
        type="date",
        tickformat="%Y-%m",
        rangeslider=dict(visible=True, thickness=0.05),
        row=1, col=1
    )

    # ── gauge (right) ───────────────────────────────────────────────────
    last_val = round(float(df["FWD_SHARPE"].iloc[-1]), 2)
    state = "Buy" if last_val < .3 else "Hold" if last_val <= .7 else "Sell"
    zone_col = "green" if last_val < .3 else "yellow" if last_val <= .7 else "red"

    gauge = go.Indicator(
        mode="gauge+number",
        value=last_val,
        number=dict(valueformat=".2f"),
        title=dict(text=f"<b>{state}</b><br>", font=dict(color=zone_col, size=32)),
        gauge=dict(
            axis=dict(range=[0, 1]),
            bar=dict(color="rgba(0,0,0,0)", thickness=0),
            steps=[
                {"range": [0, 0.3], "color": "green"},
                {"range": [0.3, 0.7], "color": "yellow"},
                {"range": [0.7, 1],  "color": "red"},
            ],
            threshold=dict(value=last_val,
                           line=dict(color="white", width=6),
                           thickness=0.9),
        )
    )
    fig.add_trace(gauge, row=1, col=2)

    # ── layout polish ───────────────────────────────────────────────────
    fig.update_layout(
        title=title_line,
        template="plotly_dark",
        margin=dict(t=60, l=40, r=40, b=40),
        height=460,
        legend=dict(x=0.02, y=0.98),
    )

    return fig.to_html(full_html=False)

