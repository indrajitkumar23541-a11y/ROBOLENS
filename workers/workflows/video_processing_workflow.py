from typing import Dict, Any
from workers.activities.video_validation import validate_video_file
from workers.activities.ai_annotation import generate_candidate_annotations
from workers.activities.quality_checks import run_automated_quality_checks


class VideoProcessingPipeline:
    """
    Standard asynchronous video processing pipeline orchestrator.
    Can be run as a standalone worker or inside a Temporal workflow.
    """

    @staticmethod
    def process_submission(
        submission_id: str,
        video_file_path: str,
        task_category: str = "general_manipulation",
        min_duration: int = 5,
        max_duration: int = 180
    ) -> Dict[str, Any]:
        # Stage 1: Technical Validation
        validation = validate_video_file(
            file_path=video_file_path,
            min_duration=min_duration,
            max_duration=max_duration
        )
        if not validation["valid"]:
            return {
                "submission_id": submission_id,
                "status": "FAILED",
                "validation": validation,
                "annotations": [],
                "quality": {
                    "decision": "FAIL",
                    "reason": validation.get("error")
                }
            }

        # Stage 2: AI Action Segmentation
        duration = validation.get("duration_seconds", 10.0)
        annotations = generate_candidate_annotations(
            task_category=task_category,
            duration_seconds=duration
        )

        # Stage 3: Automated Quality Checks
        quality = run_automated_quality_checks(
            validation_result=validation,
            annotations=annotations
        )

        # Stage 4: Determine Final Status
        if quality["decision"] == "PASS":
            next_status = "APPROVED"
        elif quality["decision"] == "NEEDS_REVIEW":
            next_status = "IN_REVIEW"
        else:
            next_status = "FAILED"

        return {
            "submission_id": submission_id,
            "status": next_status,
            "validation": validation,
            "annotations": annotations,
            "quality": quality
        }
