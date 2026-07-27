# Validation Report

## Overall Assessment: Share With Caveats

The model is ready to use as a portfolio work sample. It is not ready to use as a real site-selection decision without utility, parcel, incentive, and proprietary market data.

## Methodology Review

The model answers the right screening question for the target role: how to compare datacenter market advantage using disparate public sources and explicit assumptions. It separates demand, feasibility, and execution risk, then tests how rankings change under base-case, power-first, and inference-first scenarios.

The calculation is transparent and reproducible through `datacenter_market_model.py`. The model avoids causal claims and avoids implying access to Microsoft internal planning data.

## Calculation Spot-Checks

- Ranking logic: Verified. `outputs/market_scores.csv` sorts markets by `base_case` descending.
- Scenario sensitivity: Verified. Power-first and inference-first rankings use separate scenario weights.
- Source separation: Partially verified. EIA price data and Microsoft/CBRE public facts are sourced; market quality scores are judgment inputs and clearly caveated.
- Reproducibility: Verified. Running `python3 datacenter_market_model.py` regenerates CSV, charts, and the executive brief.

## Issues Found

1. Severity: Medium. Several input scores are analyst judgment scores, not direct measurements. Impact: The model is useful for demonstrating thinking but should not be presented as a definitive market forecast.
2. Severity: Medium. Grid load growth is precise for ERCOT and PJM from EIA, but proxied for some other regions. Impact: Regional comparisons outside ERCOT/PJM should be treated as directional.
3. Severity: Low. Charts are static and do not expose every assumption interactively. Impact: Fine for GitHub and resume proof, but a production version should include an editable model or dashboard.

## Suggested Improvements

1. Replace judgment scores with third-party analyst tables when available.
2. Add parcel-level power interconnection timelines and utility queue status.
3. Add sensitivity sliders or a small dashboard for stakeholder review.
4. Add a one-slide executive summary PDF for nontechnical recruiters.

## Required Caveats For Stakeholders

- This is an independent public-data work sample.
- It does not use Microsoft internal demand, vendor, land, power, or analyst-provider data.
- It is a market-screening model, not a final site-selection recommendation.
