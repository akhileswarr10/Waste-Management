import os
import sys
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app import app

def test_phase2():
    print("=" * 60)
    print("RUNNING PHASE 2 ML PIPELINE & PREDICTIONS TEST")
    print("=" * 60)

    client = app.test_client()

    # 1. Call GET /api/predictions
    print("[*] Triggering GET /api/predictions...")
    res = client.get("/api/predictions")
    assert res.status_code == 200, f"Predictions request failed: {res.data}"
    
    payload = json.loads(res.data)
    assert payload.get("status") == "success", f"Status is not success: {payload}"
    
    data = payload.get("data", {})
    total_bins = data.get("total_bins", 0)
    at_risk = data.get("at_risk_bins_count", 0)
    tier_dist = data.get("tier_distribution", {})
    predictions = data.get("predictions", [])

    print(f"[PASS] Successfully generated predictions for all {total_bins} bins.")
    print(f"[PASS] At-Risk Bins (High/Critical/Emergency): {at_risk}")
    print(f"[PASS] Risk Tier Breakdown: {tier_dist}")
    print(f"[PASS] Average Fill: Current={data.get('average_current_fill_pct')}% | Predicted 6h={data.get('average_predicted_fill_pct')}%")

    # 2. Validate Structure of Predictions
    assert len(predictions) == total_bins and total_bins > 0, "No predictions returned!"
    
    sample = predictions[0]
    expected_keys = [
        "bin_id", "latitude", "longitude", "locality", "collection_zone",
        "area_type", "bin_capacity_liters", "current_fill_level_pct",
        "predicted_fill_6h_pct", "overflow_probability_pct",
        "predicted_overflow", "priority_score", "urgency_tier",
        "recommended_action", "estimated_hours_to_full"
    ]
    for k in expected_keys:
        assert k in sample, f"Missing key '{k}' in prediction output!"

    print("\nTop 5 Prioritized Bins for Collection:")
    print("-" * 75)
    print(f"{'Bin ID':<8} | {'Zone':<6} | {'Area':<12} | {'Curr Fill':<10} | {'6h Pred':<9} | {'Ovf Prob':<9} | {'Priority':<9} | {'Tier'}")
    print("-" * 75)
    for p in predictions[:5]:
        print(f"{p['bin_id']:<8} | {p['collection_zone']:<6} | {p['area_type']:<12} | {p['current_fill_level_pct']:>8.1f}% | {p['predicted_fill_6h_pct']:>7.1f}% | {p['overflow_probability_pct']:>7.1f}% | {p['priority_score']:>8.2f} | {p['urgency_tier']}")
    print("-" * 75)

    print("\n[+] Verification 2 Passed Successfully!")
    print("=" * 60)

if __name__ == "__main__":
    test_phase2()
