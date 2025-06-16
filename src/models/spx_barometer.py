# spx_barometer.py (generic multi-index version)
# ---------------------------------------------------------------------------
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ─────────────────────────────────────────────────────────────────────────────
#  Scaling functions
# ─────────────────────────────────────────────────────────────────────────────
def barometer_scaler(name, raw_series):
    if name == "SPX":
        result = (raw_series - 0.1).clip(lower=0, upper=1)
        return result
    elif name == "TPX":
        result = (2*raw_series - 0.2).clip(lower=0, upper=1)
        return result
    else:
        return "No scaling function defined for name"

# ─────────────────────────────────────────────────────────────────────────────
#  Helper: Excel-equivalent RORR
# ─────────────────────────────────────────────────────────────────────────────
def get_rorr(px_last, gr, idx_curr, idx_next):
    B, U, O, N = np.broadcast_arrays(px_last, gr, idx_curr, idx_next)
    term = B * (1 - U / 100.0)
    disc = (term - N) ** 2 - 4 * B * ((U / 100.0) * (N - B) - O)
    root = np.where(disc >= 0, np.sqrt(disc), np.nan)
    numerator = N - term + root
    denominator = 2 * B
    return (numerator / denominator) * 100.0

# ─────────────────────────────────────────────────────────────────────────────
#  Helper: drop any rows containing "#N/A"
# ─────────────────────────────────────────────────────────────────────────────
def drop_na_rows(df: pd.DataFrame) -> pd.DataFrame:
    df = df.replace(r"#N/A.*", np.nan, regex=True)
    df = df.ffill()
    return df.dropna()

# ─────────────────────────────────────────────────────────────────────────────
#  Core model (single index)
# ─────────────────────────────────────────────────────────────────────────────
def process_spx_barometer_single(name: str, data: pd.DataFrame, lookback: int = 30) -> pd.DataFrame:
    df = data.copy().ffill().iloc[::-1]
    df = drop_na_rows(df)
    df = df.set_index('DATE')
    df = df.apply(pd.to_numeric, errors='coerce')
    sm = df.drop('PX_LAST', axis=1).rolling(window=lookback).mean()
    sm['PX_LAST'] = df.loc[sm.index, 'PX_LAST']
    sm = sm.ffill().dropna()
    sm['GR'] = (1 - sm['DVD_PAYOUT_RATIO'] / 100) * sm['BEST_ROE']
    sm['RORR'] = get_rorr(
        sm['PX_LAST'], sm['GR'],
        sm['IDX_EST_DVD_CURR_YR'], sm['IDX_EST_DVD_NXT_YR']
    )
    sm['ERP'] = sm['RORR'] - sm['RF']
    raw_fwd_sharpe = sm['ERP'] / sm['VOLATILITY_360D']
    sm['FWD_SHARPE'] = barometer_scaler(name, raw_fwd_sharpe)
    return sm[['PX_LAST', 'FWD_SHARPE']]

# ─────────────────────────────────────────────────────────────────────────────
#  Core model (multi-index)
# ─────────────────────────────────────────────────────────────────────────────
def process_spx_barometer(raw_dict: dict, lookback: int = 30) -> dict:
    processed = {}
    for name, df in raw_dict.items():
        if 'DATE' not in df.columns:
            continue
        processed[name] = process_spx_barometer_single(name, df, lookback)
    return processed

# ─────────────────────────────────────────────────────────────────────────────
#  Plotting (single index)
# ─────────────────────────────────────────────────────────────────────────────
def plot_spx_barometer_single(df: pd.DataFrame, index_name: str, title_line: str = '') -> str:
    if df.empty:
        return "<div style='color:#ccc'>No data available</div>"
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, errors='coerce')
    df = df.sort_index()
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{'secondary_y': True}, {'type': 'domain'}]],
        column_widths=[0.65, 0.35],
        horizontal_spacing=0.08
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=df['PX_LAST'], name=index_name, mode='lines'),
        row=1, col=1, secondary_y=False
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=df['FWD_SHARPE'], name=f'{index_name} Sharpe', mode='lines'),
        row=1, col=1, secondary_y=True
    )
    lo, hi = df['PX_LAST'].min(), df['PX_LAST'].max()
    pad = 0.05 * (hi - lo)
    fig.update_yaxes(
        range=[lo-pad, hi+pad],
        title=index_name,
        row=1, col=1
    )
    fig.update_yaxes(
        range=[0,1],
        title='',
        secondary_y=True,
        row=1, col=1
    )
    fig.update_xaxes(type='date', tickformat='%Y-%m', rangeslider={'visible':True,'thickness':0.05}, row=1, col=1)
    last = float(df['FWD_SHARPE'].iloc[-1])
    state = 'Buy' if last < .3 else 'Hold' if last <= .7 else 'Sell'
    color = 'green' if last < .3 else 'yellow' if last <= .7 else 'red'
    fig.add_trace(
        go.Indicator(
            mode='gauge+number', value=last,
            number={'valueformat':'.2f'},
            title={'text':f"<b>{state}</b>", 'font':{'color':color,'size':32}},
            gauge={
                'axis': {'range': [0, 1]},
                'bar': {'color': 'rgba(0,0,0,0)', 'thickness': 0},
                'steps': [
                    {'range': [0, 0.3], 'color': 'green'},
                    {'range': [0.3, 0.7], 'color': 'yellow'},
                    {'range': [0.7, 1], 'color': 'red'}
                ],
                'threshold': {
                    'value': last,
                    'line': {'color': 'white', 'width': 6},
                    'thickness': 0.9
                }
            }
        ), row=1, col=2
    )
    fig.update_layout(
        title={
            'text': f"<b>{title_line}</b>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24}
        },
        template='plotly_dark',
        margin={'t':60,'l':40,'r':40,'b':40},
        height=460,
        showlegend=False
    )
    return fig.to_html(full_html=False)

# ─────────────────────────────────────────────────────────────────────────────
#  Plotting (multi-index) using single-index plot function
# ─────────────────────────────────────────────────────────────────────────────
def plot_spx_barometer(df_dict: dict, title_prefix: str = '') -> str:
    html_fragments = []
    row = []
    for i, (name, df) in enumerate(df_dict.items(), start=1):
        title_line = f"{title_prefix} - {name}" if title_prefix else name
        fig_html = plot_spx_barometer_single(df, index_name=name, title_line=title_line)
        row.append(fig_html)
        if len(row) == 2 or i == len(df_dict):
            html_fragments.append("<div style='display:flex;justify-content:space-between;'>" + "".join(row) + "</div><br>")
            row = []
    return "<div>" + "".join(html_fragments) + "</div>"
