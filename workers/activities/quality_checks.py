from typing import List, Dict, Any


def run_automated_quality_checks(
    validation_result: Dict[str, Any],
    annotations: List[Dict[str, Any]],
    confidence_threshold: float = 0.85
) -> Dict[str, Any]:
    """
    Automated multi-factor quality inspection:
    1. Checks technical video metrics (valid resolution, reasonable duration).
    2. Checks temporal consistency of action intervals.
    3. Evaluates AI model confidence.
    Returns decision: PASS, NEEDS_REVIEW, or FAIL.
    """
    if not validation_result.get("valid", False):
        return {
            "decision": "FAIL",
            "reason": validation_result.get("error", "Video validation failed"),
            "requires_human_review": False
        }

    if not annotations:
        return {
            "decision": "NEEDS_REVIEW",
            "reason": "No actions could be detected in video recording",
            "requires_human_review": True
        }

    # Verify temporal consistency
    for i, anno in enumerate(annotations):
        if anno["start_time_ms"] >= anno["end_time_ms"]:
            return {
                "decision": "FAIL",
                "reason": f"Invalid temporal bounds in annotation {i}: start >= end",
                "requires_human_review": False
            }
        
        # Check confidence
        conf = anno.get("confidence", 0.0)
        if conf < confidence_threshold:
            return {
                "decision": "NEEDS_REVIEW",
                "reason": f"Low AI confidence ({conf:.2f}) on action '{anno.get('label')}'",
                "requires_human_review": True
            }

    return {
        "decision": "PASS",
        "reason": "All automated quality and confidence checks passed successfully",
        "requires_human_review": False
    }
