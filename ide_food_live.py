
# ============================================================
# IDE-food LIVE v0.2
# Automated agro-energy food stress monitor
# Author: Eric de Jesus Rodriguez Mendoza
# ============================================================

import os
import numpy as np
import pandas as pd
from datetime import datetime, UTC

WB_URL = "https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Historical-Data-Monthly.xlsx"

RED = 3.5
WATCH = 3.0
EARLY_IDE = 3.2

weights = {
    "E_z": 0.35,
    "A_z": 0.30,
    "F_z": 0.35,
}

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def parse_wb_date(x):
    if pd.isna(x):
        return pd.NaT
    s = str(x).strip()
    if "M" in s and len(s) >= 6:
        try:
            y, m = s.split("M")
            return pd.Timestamp(int(y), int(m), 1) + pd.offsets.MonthEnd(0)
        except Exception:
            return pd.NaT
    return pd.to_datetime(s, errors="coerce") + pd.offsets.MonthEnd(0)

def sigmoid_score(x):
    return 5 / (1 + np.exp(-x))

def walk_forward_z(series, window=120, min_periods=60):
    mean = series.shift(1).rolling(window, min_periods=min_periods).mean()
    std = series.shift(1).rolling(window, min_periods=min_periods).std()
    return (series - mean) / std.replace(0, np.nan)

def weighted_score(row, active_cols):
    denom = sum(weights[c] for c in active_cols)
    zval = sum(weights[c] * row[c] for c in active_cols) / denom
    return sigmoid_score(zval)

def classify_signal(row):
    ide = row["IDE_core"]
    only_e = row["Only_E"]
    only_a = row["Only_A"]
    only_f = row["Only_F"]

    red = ide >= RED

    soft_structural = (
        red
        and row["No_E"] >= WATCH
        and row["No_A"] >= WATCH
        and row["No_F"] >= WATCH
    )

    early_agroenergy = (
        ide >= EARLY_IDE
        and ((only_e >= RED) or (only_f >= RED))
        and only_a >= 1.5
        and not red
    )

    if soft_structural:
        return "RED_STRUCTURAL"
    elif red:
        return "RED"
    elif early_agroenergy:
        return "EARLY_AGROENERGY_WATCH"
    elif ide >= WATCH:
        return "WATCH"
    else:
        return "GREEN"

def explain_signal(row):
    status = row["status"]

    if status == "RED_STRUCTURAL":
        return (
            "IDE-food is in RED_STRUCTURAL regime. "
            "The agro-energy triad is elevated and remains structurally coherent under soft ablation. "
            "Historically, this state is associated with high domestic food-inflation regimes at 6–12 month horizons."
        )

    if status == "RED":
        return (
            "IDE-food is in RED regime. "
            "The global agro-energy stress score is high, but structural confirmation should be reviewed manually."
        )

    if status == "EARLY_AGROENERGY_WATCH":
        return (
            "IDE-food is in EARLY_AGROENERGY_WATCH. "
            "Energy and/or fertilizers are elevated, while agriculture has not fully joined the regime. "
            "This may correspond to an early latency configuration rather than a full RED regime."
        )

    if status == "WATCH":
        return (
            "IDE-food is in WATCH. "
            "Stress is elevated but below the RED threshold."
        )

    return (
        "IDE-food is GREEN. "
        "No current agro-energy regime alert under this specification."
    )

def component_regime(score):
    if score >= RED:
        return "RED"
    elif score >= WATCH:
        return "WATCH"
    return "GREEN"

def fetch_world_bank_indices():
    raw = pd.read_excel(
        WB_URL,
        sheet_name="Monthly Indices",
        header=None,
        engine="openpyxl"
    )

    df = raw.iloc[9:, [0, 2, 4, 6, 8, 13]].copy()
    df.columns = ["Date", "Energy", "Agriculture", "Food", "Grains", "Fertilizers"]

    df["Date"] = df["Date"].apply(parse_wb_date)

    for c in ["Energy", "Agriculture", "Food", "Grains", "Fertilizers"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = (
        df.dropna(subset=["Date"])
          .set_index("Date")
          .sort_index()
          .loc["1990-01-31":]
          .dropna(subset=["Energy", "Agriculture", "Food", "Grains", "Fertilizers"])
    )

    return df

def compute_ide(df):
    mom = np.log(df[["Energy", "Agriculture", "Fertilizers"]]).diff(12)
    mom.columns = ["Energy_mom12", "Agriculture_mom12", "Fertilizers_mom12"]

    z = pd.DataFrame(index=df.index)
    z["E_z"] = walk_forward_z(mom["Energy_mom12"])
    z["A_z"] = walk_forward_z(mom["Agriculture_mom12"])
    z["F_z"] = walk_forward_z(mom["Fertilizers_mom12"])
    z = z.clip(-4, 4)

    ide = pd.DataFrame(index=df.index)
    ide["IDE_core"] = z.apply(lambda r: weighted_score(r, ["E_z", "A_z", "F_z"]), axis=1)

    ide["No_E"] = z.apply(lambda r: weighted_score(r, ["A_z", "F_z"]), axis=1)
    ide["No_A"] = z.apply(lambda r: weighted_score(r, ["E_z", "F_z"]), axis=1)
    ide["No_F"] = z.apply(lambda r: weighted_score(r, ["E_z", "A_z"]), axis=1)

    ide["Only_E"] = z.apply(lambda r: weighted_score(r, ["E_z"]), axis=1)
    ide["Only_A"] = z.apply(lambda r: weighted_score(r, ["A_z"]), axis=1)
    ide["Only_F"] = z.apply(lambda r: weighted_score(r, ["F_z"]), axis=1)

    model_live = df.join(mom).join(z).join(ide).dropna(subset=["IDE_core"]).copy()
    model_live["status"] = model_live.apply(classify_signal, axis=1)
    model_live["explanation"] = model_live.apply(explain_signal, axis=1)

    return model_live

def build_state_log(model_live, months=12):
    history = model_live.tail(months).copy()

    state_log = pd.DataFrame({
        "date": history.index.date.astype(str),
        "status": history["status"].values,
        "IDE_core": history["IDE_core"].round(3).values,
        "Energy": history["Only_E"].round(3).values,
        "Agriculture": history["Only_A"].round(3).values,
        "Fertilizers": history["Only_F"].round(3).values,
    })

    state_log["date"] = pd.to_datetime(state_log["date"])
    state_log = state_log.sort_values("date")

    current_status = state_log.iloc[-1]["status"]

    consecutive = 1
    for s in reversed(state_log["status"].iloc[:-1].tolist()):
        if s == current_status:
            consecutive += 1
        else:
            break

    alert_statuses = ["WATCH", "EARLY_AGROENERGY_WATCH", "RED", "RED_STRUCTURAL"]

    if current_status in alert_statuses and consecutive > 1:
        transition = f"PERSISTENT_{consecutive}_MONTHS"
    elif current_status in alert_statuses:
        transition = "NEW_ACTIVE_SIGNAL"
    else:
        transition = "NO_ACTIVE_ALERT"

    return state_log, transition

def build_markdown_report(model_live, state_log, transition):
    latest = model_live.iloc[-1]
    latest_date = model_live.index[-1]

    alert_text = f"""# IDE-food Live Alert

**Generated at:** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')} UTC  
**Data date:** {latest_date.date()}  
**Status:** `{latest["status"]}`  
**Transition:** `{transition}`  
**IDE_core:** `{latest["IDE_core"]:.3f}`

## Component scores

| Component | Score | Regime |
|---|---:|---|
| Energy | {latest["Only_E"]:.3f} | {component_regime(latest["Only_E"])} |
| Agriculture | {latest["Only_A"]:.3f} | {component_regime(latest["Only_A"])} |
| Fertilizers | {latest["Only_F"]:.3f} | {component_regime(latest["Only_F"])} |

## Ablation pair scores

| Ablation | Score |
|---|---:|
| No Energy | {latest["No_E"]:.3f} |
| No Agriculture | {latest["No_A"]:.3f} |
| No Fertilizers | {latest["No_F"]:.3f} |

## Interpretation

{latest["explanation"]}

## Last recorded states

{state_log.tail(12).to_markdown(index=False)}
"""

    return alert_text

def main():
    print("Fetching World Bank Pink Sheet...")
    df = fetch_world_bank_indices()

    print(f"Data range: {df.index.min().date()} → {df.index.max().date()}")
    print("Computing IDE-food...")
    model_live = compute_ide(df)

    state_log, transition = build_state_log(model_live, months=12)
    report = build_markdown_report(model_live, state_log, transition)

    model_live.to_csv(os.path.join(OUTPUT_DIR, "ide_food_live_full_model.csv"))
    state_log.to_csv(os.path.join(OUTPUT_DIR, "ide_food_live_state_log.csv"), index=False)

    with open(os.path.join(OUTPUT_DIR, "ide_food_live_alert.md"), "w", encoding="utf-8") as f:
        f.write(report)

    latest = model_live.iloc[-1]
    latest_date = model_live.index[-1]

    print("\n" + "=" * 70)
    print("IDE-food LIVE SIGNAL")
    print("=" * 70)
    print(f"Date: {latest_date.date()}")
    print(f"Status: {latest['status']}")
    print(f"Transition: {transition}")
    print(f"IDE_core: {latest['IDE_core']:.3f}")
    print(f"Energy: {latest['Only_E']:.3f}")
    print(f"Agriculture: {latest['Only_A']:.3f}")
    print(f"Fertilizers: {latest['Only_F']:.3f}")
    print("=" * 70)

    print("\nFiles written:")
    print(f"- {OUTPUT_DIR}/ide_food_live_full_model.csv")
    print(f"- {OUTPUT_DIR}/ide_food_live_state_log.csv")
    print(f"- {OUTPUT_DIR}/ide_food_live_alert.md")

if __name__ == "__main__":
    main()
