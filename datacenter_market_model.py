from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "market_inputs.csv"
OUTPUT_DIR = ROOT / "outputs"


SCENARIOS = {
    "base_case": {
        "demand": 0.40,
        "feasibility": 0.35,
        "risk": 0.25,
        "description": "Balanced market-entry view across demand, speed-to-power, and execution risk.",
    },
    "power_first": {
        "demand": 0.30,
        "feasibility": 0.50,
        "risk": 0.20,
        "description": "Prioritizes faster capacity delivery and lower power-cost exposure.",
    },
    "inference_first": {
        "demand": 0.50,
        "feasibility": 0.25,
        "risk": 0.25,
        "description": "Prioritizes regional inference demand, latency, and workload fit.",
    },
}


def read_rows() -> list[dict[str, str]]:
    with DATA_PATH.open(newline="") as handle:
        return list(csv.DictReader(handle))


def min_max(values: list[float]) -> tuple[float, float]:
    return min(values), max(values)


def normalize(value: float, low: float, high: float, invert: bool = False) -> float:
    if high == low:
        score = 0.5
    else:
        score = (value - low) / (high - low)
    if invert:
        score = 1 - score
    return max(0.0, min(1.0, score))


def score_markets(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    prices = [float(row["eia_avg_retail_price_cents_kwh_2024"]) for row in rows]
    load_growth = [float(row["load_growth_signal_pct_2025_2027"]) for row in rows]
    price_low, price_high = min_max(prices)
    load_low, load_high = min_max(load_growth)

    scored: list[dict[str, object]] = []
    for row in rows:
        demand_signal = float(row["cbre_demand_signal"]) / 5
        workload_fit = float(row["azure_workload_fit"]) / 5
        latency_fit = float(row["latency_inference_fit"]) / 5
        fiber_signal = float(row["fiber_expansion_signal"]) / 5
        power_availability = float(row["power_availability_signal"]) / 5
        water_risk = float(row["water_cooling_risk"]) / 5
        community_risk = float(row["community_permitting_risk"]) / 5
        price_score = normalize(float(row["eia_avg_retail_price_cents_kwh_2024"]), price_low, price_high, invert=True)
        load_growth_score = normalize(float(row["load_growth_signal_pct_2025_2027"]), load_low, load_high)

        demand = (
            0.35 * demand_signal
            + 0.25 * workload_fit
            + 0.20 * latency_fit
            + 0.10 * fiber_signal
            + 0.10 * load_growth_score
        )
        feasibility = (
            0.35 * power_availability
            + 0.25 * price_score
            + 0.20 * fiber_signal
            + 0.20 * (1 - water_risk)
        )
        risk = (
            0.40 * load_growth_score
            + 0.30 * water_risk
            + 0.30 * community_risk
        )

        scenario_scores = {}
        for scenario, weights in SCENARIOS.items():
            score = (
                weights["demand"] * demand
                + weights["feasibility"] * feasibility
                + weights["risk"] * (1 - risk)
            )
            scenario_scores[scenario] = round(score * 100, 1)

        scored.append(
            {
                "market": row["market"],
                "state": row["state"],
                "grid_region": row["grid_region"],
                "market_type": row["market_type"],
                "demand_score": round(demand * 100, 1),
                "feasibility_score": round(feasibility * 100, 1),
                "risk_score": round(risk * 100, 1),
                "base_case": scenario_scores["base_case"],
                "power_first": scenario_scores["power_first"],
                "inference_first": scenario_scores["inference_first"],
                "source_confidence": row["source_confidence"],
                "notes": row["notes"],
            }
        )

    scored.sort(key=lambda item: item["base_case"], reverse=True)
    return scored


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def plot_scores(scored: list[dict[str, object]]) -> None:
    markets = [str(row["market"]) for row in scored]
    base = [float(row["base_case"]) for row in scored]
    power = [float(row["power_first"]) for row in scored]
    inference = [float(row["inference_first"]) for row in scored]

    plt.figure(figsize=(12, 6.5))
    y = range(len(markets))
    plt.barh([i + 0.24 for i in y], inference, height=0.24, label="Inference first")
    plt.barh(y, base, height=0.24, label="Base case")
    plt.barh([i - 0.24 for i in y], power, height=0.24, label="Power first")
    plt.yticks(list(y), markets)
    plt.gca().invert_yaxis()
    plt.xlabel("Risk-adjusted market advantage score, 0 to 100")
    plt.title("Datacenter Market Advantage by Scenario")
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "market_advantage_scores.png", dpi=180)
    plt.close()


def plot_risk(scored: list[dict[str, object]]) -> None:
    markets = [str(row["market"]) for row in scored]
    demand = [float(row["demand_score"]) for row in scored]
    feasibility = [float(row["feasibility_score"]) for row in scored]
    risk = [float(row["risk_score"]) for row in scored]

    plt.figure(figsize=(12, 6.5))
    x = range(len(markets))
    plt.plot(x, demand, marker="o", label="Demand")
    plt.plot(x, feasibility, marker="o", label="Feasibility")
    plt.plot(x, risk, marker="o", label="Execution risk (lower is better)")
    plt.xticks(list(x), markets, rotation=30, ha="right")
    plt.ylabel("Component score, 0 to 100")
    plt.title("Demand, Feasibility, and Execution Risk Components")
    plt.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "component_score_comparison.png", dpi=180)
    plt.close()


def write_brief(scored: list[dict[str, object]]) -> None:
    top = scored[:3]
    power_first = sorted(scored, key=lambda item: item["power_first"], reverse=True)[:3]
    inference_first = sorted(scored, key=lambda item: item["inference_first"], reverse=True)[:3]
    lines = [
        "# Executive Brief",
        "",
        "This independent model ranks North American datacenter markets by risk-adjusted market advantage for AI and cloud capacity planning.",
        "",
        "## Base Case Readout",
        "",
    ]
    for index, row in enumerate(top, start=1):
        lines.append(
            f"{index}. {row['market']}: {row['base_case']} score, demand {row['demand_score']}, "
            f"feasibility {row['feasibility_score']}, risk {row['risk_score']}."
        )
    lines.extend(
        [
            "",
            "## Scenario Movement",
            "",
            "Power-first top markets: "
            + ", ".join(f"{row['market']} ({row['power_first']})" for row in power_first)
            + ".",
            "Inference-first top markets: "
            + ", ".join(f"{row['market']} ({row['inference_first']})" for row in inference_first)
            + ".",
            "",
            "## Interpretation",
            "",
            "Northern Virginia remains the demand anchor, but its advantage depends on whether capacity, power timing, and community pressure can be managed.",
            "West Texas / Pecos improves under a power-first view because dedicated capacity and on-site energy matter, but ERCOT load growth raises execution risk.",
            "Atlanta and Hillsboro / Portland look attractive as balanced or feasibility-led alternatives where the next question is site-level power timing.",
            "",
            "## What I Would Validate Next",
            "",
            "1. Utility interconnection timelines by site, not by state.",
            "2. Real land parcels, water sourcing, and permitting calendars.",
            "3. Third-party analyst capacity forecasts and preleasing data.",
            "4. Microsoft internal demand by workload family and latency requirement.",
        ]
    )
    (OUTPUT_DIR / "executive_brief.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    rows = read_rows()
    scored = score_markets(rows)
    fields = [
        "market",
        "state",
        "grid_region",
        "market_type",
        "demand_score",
        "feasibility_score",
        "risk_score",
        "base_case",
        "power_first",
        "inference_first",
        "source_confidence",
        "notes",
    ]
    write_csv(OUTPUT_DIR / "market_scores.csv", scored, fields)
    plot_scores(scored)
    plot_risk(scored)
    write_brief(scored)


if __name__ == "__main__":
    main()
