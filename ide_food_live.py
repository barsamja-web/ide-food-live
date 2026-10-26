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


def build_markdown_report(model_live, state_log, transition, data_health, data_age_days):
    latest = model_live.iloc[-1]
    latest_date = model_live.index[-1]
    return f"""# IDE-food Live Alert

**Generated at:** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')} UTC  
**Data date:** {latest_date.date()}  
**Data health:** `{data_health}` ({data_age_days} days since observation month-end)  
**Status:** `{latest['status']}`  
**Transition:** `{transition}`  
**IDE_core:** `{latest['IDE_core']:.3f}`

## Component scores

| Component | Score | Regime |
|---|---:|---|
| Energy | {latest['Only_E']:.3f} | {component_regime(latest['Only_E'])} |
| Agriculture | {latest['Only_A']:.3f} | {component_regime(latest['Only_A'])} |
| Fertilizers | {latest['Only_F']:.3f} | {component_regime(latest['Only_F'])} |

## Ablation pair scores

| Ablation | Score |
|---|---:|
| No Energy | {latest['No_E']:.3f} |
| No Agriculture | {latest['No_A']:.3f} |
| No Fertilizers | {latest['No_F']:.3f} |

## Interpretation

{latest['explanation']}

## Data provenance

Source: World Bank Commodity Markets Pink Sheet, monthly historical indices.  
Source URL: {WB_URL}  
Data health indicates observation age, not whether the upstream publisher revised earlier values.

## Last recorded states

{state_log.tail(12).to_markdown(index=False)}
"""


def main():
    print("Fetching World Bank Pink Sheet...")
    df = fetch_world_bank_indices()
    print(f"Data range: {df.index.min().date()} -> {df.index.max().date()}")
    print("Computing IDE-food...")
    model_live = compute_ide(df)

    latest_date = model_live.index[-1]
    data_age_days = (pd.Timestamp.now(tz="UTC").tz_localize(None).normalize() - latest_date).days
    if data_age_days < -31:
        raise ValueError(f"Latest World Bank date is unexpectedly in the future: {latest_date.date()}")
    data_health = "DATA_CURRENT" if data_age_days <= MAX_DATA_AGE_DAYS else "DATA_STALE"
    if data_health == "DATA_STALE":
        print(f"WARNING: latest observation is {data_age_days} days old.")

    state_log, transition = build_state_log(model_live, months=12)
    report = build_markdown_report(model_live, state_log, transition, data_health, data_age_days)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    model_live.to_csv(os.path.join(OUTPUT_DIR, "ide_food_live_full_model.csv"))
    state_log.to_csv(os.path.join(OUTPUT_DIR, "ide_food_live_state_log.csv"), index=False)
    with open(os.path.join(OUTPUT_DIR, "ide_food_live_alert.md"), "w", encoding="utf-8") as f:
        f.write(report)

    latest = model_live.iloc[-1]
    print("\n" + "=" * 70)
    print("IDE-food LIVE SIGNAL")
    print("=" * 70)
    print(f"Date: {latest_date.date()}")
    print(f"Data health: {data_health}")
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
