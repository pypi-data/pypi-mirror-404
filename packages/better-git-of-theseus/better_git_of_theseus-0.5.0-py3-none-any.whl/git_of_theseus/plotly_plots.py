import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import dateutil.parser
import collections
import math
import os
from .utils import generate_n_colors

# Harmonious, professional color palette (Modern & Muted)
# Inspired by Tableau 20 and modern UI systems
PREMIUM_PALETTE = [
    "#4E79A7", "#A0CBE8", "#F28E2B", "#FFBE7D", "#59A14F", 
    "#8CD17D", "#B6992D", "#F1CE63", "#499894", "#86BCB6",
    "#E15759", "#FF9D9A", "#79706E", "#BAB0AC", "#D37295", 
    "#FABFD2", "#B07AA1", "#D4A1D2", "#9D7660", "#D7B5A6"
]

def _process_stack_line_data(data, max_n=20, normalize=False):
    if not isinstance(data, dict):
        import json
        data = json.load(open(data))

    y = np.array(data["y"])
    labels = data["labels"]
    ts = [dateutil.parser.parse(t) for t in data["ts"]]

    if y.shape[0] > max_n:
        js = sorted(range(len(labels)), key=lambda j: max(y[j]), reverse=True)
        other_indices = js[max_n:]
        if other_indices:
            other_sum = np.sum([y[j] for j in other_indices], axis=0)
            top_js = sorted(js[:max_n], key=lambda j: labels[j])
            y = np.array([y[j] for j in top_js] + [other_sum])
            labels = [labels[j] for j in top_js] + ["other"]
    
    y_sums = np.sum(y, axis=0)
    y_sums[y_sums == 0] = 1.0

    if normalize:
        y = 100.0 * y / y_sums

    return ts, y, labels

def plotly_stack_plot(data, max_n=20, normalize=False, title=None):
    ts, y, labels = _process_stack_line_data(data, max_n, normalize)
    fig = go.Figure()
    
    for i, label in enumerate(labels):
        color = PREMIUM_PALETTE[i % len(PREMIUM_PALETTE)]
        fig.add_trace(go.Scatter(
            x=ts, 
            y=y[i], 
            mode='lines',
            name=label,
            stackgroup='one', 
            line=dict(width=0.5, color='rgba(255,255,255,0.3)'), 
            fillcolor=color,
            hoverinfo='x+y+name'
        ))

    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=20)) if title else None,
        yaxis=dict(
            title="Share of LoC (%)" if normalize else "Lines of Code",
            range=[0, 100.1] if normalize else None,
            gridcolor='rgba(128,128,128,0.2)'
        ),
        xaxis=dict(title="Date", gridcolor='rgba(128,128,128,0.2)'),
        hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    return fig

def plotly_line_plot(data, max_n=20, normalize=False, title=None):
    ts, y, labels = _process_stack_line_data(data, max_n, normalize)
    fig = go.Figure()

    for i, label in enumerate(labels):
         fig.add_trace(go.Scatter(
            x=ts, 
            y=y[i], 
            mode='lines',
            name=label,
            line=dict(width=2.5, color=PREMIUM_PALETTE[i % len(PREMIUM_PALETTE)])
        ))

    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=20)) if title else None,
        yaxis=dict(
            title="Share of LoC (%)" if normalize else "Lines of Code",
            range=[0, 100.1] if normalize else None,
            gridcolor='rgba(128,128,128,0.2)'
        ),
        xaxis=dict(title="Date", gridcolor='rgba(128,128,128,0.2)'),
        hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    return fig

def plotly_survival_plot(commit_history, exp_fit=False, years=5, title=None):
    deltas = collections.defaultdict(lambda: np.zeros(2))
    total_n = 0
    YEAR = 365.25 * 24 * 60 * 60
    
    for commit, history in commit_history.items():
        t0, orig_count = history[0]
        total_n += orig_count
        last_count = orig_count
        for t, count in history[1:]:
            deltas[t - t0] += (count - last_count, 0)
            last_count = count
        deltas[history[-1][0] - t0] += (-last_count, -orig_count)

    P = 1.0
    xs, ys = [], []
    sorted_times = sorted(deltas.keys())
    
    for t in sorted_times:
        delta_k, delta_n = deltas[t]
        xs.append(t / YEAR)
        ys.append(100.0 * P)
        if total_n > 0:
             P *= 1 + delta_k / total_n
        total_n += delta_n
        if P < 0.05: break
            
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=xs, y=ys,
        mode='lines',
        name='Survival Rate',
        line=dict(color=PREMIUM_PALETTE[0], width=3)
    ))

    if exp_fit:
        try:
            import scipy.optimize
            def fit(k):
                loss, curr_total_n = 0.0, sum(h[0][1] for h in commit_history.values())
                P_fit, curr_total_n_fit = 1.0, curr_total_n
                for t in sorted_times:
                    delta_k, delta_n = deltas[t]
                    pred = curr_total_n_fit * math.exp(-k * t / YEAR)
                    loss += (curr_total_n_fit * P_fit - pred) ** 2
                    if curr_total_n_fit > 0: P_fit *= 1 + delta_k / curr_total_n_fit
                    curr_total_n_fit += delta_n
                return loss
            k_opt = scipy.optimize.fmin(fit, 0.5, maxiter=50, disp=False)[0]
            ts_fit = np.linspace(0, years, 100)
            ys_fit = [100.0 * math.exp(-k_opt * t) for t in ts_fit]
            half_life = math.log(2) / k_opt
            fig.add_trace(go.Scatter(
                x=ts_fit, y=ys_fit,
                mode='lines',
                name=f"Exp. Fit (Half-life: {half_life:.2f} yrs)",
                line=dict(color=PREMIUM_PALETTE[10], dash='dash', width=2)
            ))
        except ImportError: pass

    fig.update_layout(
        title=dict(text=title, x=0.5) if title else None,
        yaxis=dict(title="Lines still present (%)", range=[0, 105], gridcolor='rgba(128,128,128,0.2)'),
        xaxis=dict(title="Years", range=[0, years], gridcolor='rgba(128,128,128,0.2)'),
        hovermode="x unified",
        margin=dict(l=20, r=20, t=50, b=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    return fig

def plotly_bar_plot(data, max_n=20, title=None):
    _, y, labels = _process_stack_line_data(data, max_n, normalize=False)
    latest_values = [row[-1] for row in y]
    indices = sorted(range(len(labels)), key=lambda i: latest_values[i], reverse=True)
    sorted_labels = [labels[i] for i in indices]
    sorted_values = [latest_values[i] for i in indices]
    
    fig = go.Figure(go.Bar(
        x=sorted_labels,
        y=sorted_values,
        marker=dict(
            color=sorted_values,
            colorscale=[[i/(len(PREMIUM_PALETTE)-1), c] for i, c in enumerate(PREMIUM_PALETTE)],
            showscale=False
        )
    ))

    fig.update_layout(
        title=dict(text=f"{title} (Latest)" if title else "Latest Distribution", x=0.5),
        yaxis=dict(title="Lines of Code", gridcolor='rgba(128,128,128,0.2)'),
        xaxis=dict(title=""),
        margin=dict(l=20, r=20, t=50, b=100),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    return fig
