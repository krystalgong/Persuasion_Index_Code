from pathlib import Path

import numpy as np
import pandas as pd

from PI_score_generator import HELPER_DIR, score_all
from persuasion_runner import run_expanded_lexicons


def calculate_dual_weighted_score(raw_scores: dict, sub_ci_df: pd.DataFrame, mean_ci_df: pd.DataFrame) -> dict:
    """
    Applies empirical weights from two regression levels:
    1. Sub-features (e.g., Sentiment.anger)
    2. Category Means (e.g., Sentiment.mean)
    """
    # Create lookups
    sub_weights = sub_ci_df['coef'].to_dict()
    mean_weights = mean_ci_df['coef'].to_dict()
    
    # We track two different final log-odds paths
    sub_total_log_odds = sub_weights.get("intercept", 0.0)
    mean_total_log_odds = mean_weights.get("intercept", 0.0)
    
    weighted_out = {}

    for cat, subfeatures in raw_scores.items():
        weighted_out[cat] = {}
        
        # A) Apply Sub-feature weights
        for subk, score_val in subfeatures.items():
            if subk == "mean": continue
            
            f_key = f"{cat}.{subk}"
            w = sub_weights.get(f_key, 0.0)
            weighted_val = score_val * w
            weighted_out[cat][subk] = float(round(weighted_val, 4))
            sub_total_log_odds += weighted_val
            
        # B) Apply Category Mean weight
        raw_mean = subfeatures.get("mean", 0.0)
        m_key = f"{cat}.mean"
        m_weight = mean_weights.get(m_key, 0.0)
        
        weighted_mean_impact = raw_mean * m_weight
        weighted_out[cat]["mean"] = float(round(weighted_mean_impact, 4))
        mean_total_log_odds += weighted_mean_impact

    # C) Metadata for Final Probability
    weighted_out["metadata"] = {
        "sub_model": {
            "log_odds": float(round(sub_total_log_odds, 4)),
            "prob": float(round(1 / (1 + np.exp(-sub_total_log_odds)), 4))
        },
        "mean_model": {
            "log_odds": float(round(mean_total_log_odds, 4)),
            "prob": float(round(1 / (1 + np.exp(-mean_total_log_odds)), 4))
        }
    }
    
    return weighted_out

def get_persuasion_report(
    text: str,
    use_expanded_lexicons: bool = True,
) -> tuple:
    """
    Returns two objects:
    1. Raw Linguistic Scores (score_all)
    2. Empirical weighted scores using the UKP logistic-regression weights.
    """
    # 1. Paths to the empirical coefficient files
    sub_path = HELPER_DIR / "regression_outputs" / "ci_ukp_subfeatures.csv"
    mean_path = HELPER_DIR / "regression_outputs" / "ci_ukp_mean.csv"

    run_expanded_lexicons(use_expanded_lexicons)
    
    # 2. Extract Baseline Features
    raw_scores = score_all(text)
    
    # 3. Check for stored CI files
    if not Path(sub_path).exists() or not Path(mean_path).exists():
        return raw_scores, None
    
    # 4. Load the coefficients
    ci_ukp_sub = pd.read_csv(sub_path, index_col=0)
    ci_ukp_mean = pd.read_csv(mean_path, index_col=0)
    
    # 5. Reuse your existing function to perform the math
    # This returns the nested dict with both sub-feature and mean weights
    ukp_weighted = calculate_dual_weighted_score(
        raw_scores=raw_scores,
        sub_ci_df=ci_ukp_sub,
        mean_ci_df=ci_ukp_mean
    )
    
    return raw_scores, ukp_weighted
