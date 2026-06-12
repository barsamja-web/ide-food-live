# IDE-food Live

**IDE-food Live** is an automated agro-energy food-stress monitor designed to detect early and structurally coherent food-risk regimes from global commodity data.

The system ingests World Bank commodity indices, computes a walk-forward IDE-food regime score, applies structural ablation diagnostics, classifies the current regime, and emits a live Markdown alert through GitHub Actions.

Current live status:

```text
EARLY_AGROENERGY_WATCH — PERSISTENT_2_MONTHS
```

As of the latest run, the monitor detects elevated Energy and Fertilizers stress while Agriculture has not yet fully joined the regime. This is interpreted as an early agroenergy latency configuration rather than a full RED structural regime.

---

## Purpose

IDE-food Live is not intended to be a simple commodity-price tracker.

Its purpose is to monitor whether global agro-energy stress is entering a regime that may be relevant for future food-price vulnerability, especially over 6–12 month horizons.

The system distinguishes between:

* normal conditions,
* elevated watch states,
* early agroenergy latency,
* full RED regimes,
* structurally coherent RED regimes.

---

## Methodology

The monitor currently uses the World Bank Pink Sheet Monthly Indices, including:

* Energy
* Agriculture
* Fertilizers
* Food
* Grains

The core IDE-food score is computed from the agro-energy triad:

```text
Energy + Agriculture + Fertilizers
```

The system calculates 12-month log changes and transforms them into walk-forward z-scores using only prior information. This avoids look-ahead leakage.

The current core score is:

```text
IDE_core = sigmoid(weighted_z_score) × 5
```

with baseline weights:

```text
Energy       0.35
Agriculture  0.30
Fertilizers  0.35
```

---

## Regime classification

The live monitor classifies each month into one of the following states:

| Status                 | Meaning                                                               |
| ---------------------- | --------------------------------------------------------------------- |
| GREEN                  | No current agro-energy alert                                          |
| WATCH                  | Elevated stress, below RED threshold                                  |
| EARLY_AGROENERGY_WATCH | Energy and/or fertilizers are elevated before Agriculture fully joins |
| RED                    | High agro-energy stress score                                         |
| RED_STRUCTURAL         | High score with soft structural confirmation under ablation           |

The current early-warning rule is designed to identify cases where Energy and Fertilizers move first, while Agriculture has not yet fully transmitted the stress.

---

## Structural ablation

IDE-food Live includes ablation diagnostics to test whether the signal depends on the expected agro-energy structure.

The monitor computes:

| Ablation       | Meaning                   |
| -------------- | ------------------------- |
| No Energy      | Agriculture + Fertilizers |
| No Agriculture | Energy + Fertilizers      |
| No Fertilizers | Energy + Agriculture      |

This helps distinguish generic high-score episodes from structurally interpretable agro-energy regimes.

---

## Outputs

Each automated run writes results to the `outputs/` folder:

```text
outputs/
  ide_food_live_full_model.csv
  ide_food_live_state_log.csv
  ide_food_live_alert.md
```

The main live report is:

```text
outputs/ide_food_live_alert.md
```

It includes:

* generation timestamp,
* latest data month,
* current regime status,
* transition state,
* IDE-core score,
* component scores,
* ablation pair scores,
* interpretation,
* last recorded monthly states.

---

## Automation

The monitor runs through GitHub Actions.

The workflow file is located at:

```text
.github/workflows/run_ide_food.yml
```

It can be triggered manually from the GitHub Actions tab and is also scheduled to run automatically once per month.

---

## Current interpretation

The latest live signal is:

```text
EARLY_AGROENERGY_WATCH
PERSISTENT_2_MONTHS
```

This means that the system has detected a persistent early agroenergy stress configuration for two consecutive months.

In the current configuration:

* Energy is in RED.
* Fertilizers are in RED.
* Agriculture remains below WATCH.

Therefore, this is not classified as a full RED structural regime. It is classified as an early latency signal requiring monitoring over the coming months.

---

## Research status

IDE-food Live is an experimental research monitor.

It should not be interpreted as a deterministic prediction system or as financial, investment, policy, or humanitarian advice.

Its current purpose is diagnostic:

```text
Detect agro-energy regime configurations that may precede or accompany food-price vulnerability.
```

The strongest current interpretation is that IDE-food behaves as a regime-transmission monitor rather than as a point-event forecasting tool.

---

## License and attribution

This project is part of the IDE/APM and IDE-food research line developed by Eric de Jesus Rodriguez Mendoza.

Use, citation, and reuse should preserve attribution to the author and should not represent the monitor as an officially endorsed institutional food-security product.
