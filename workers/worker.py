import os
import sys
import time
import argparse
import logging
from typing import Optional

# Add root directory to python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from app.core.database import SessionLocal
from app.models.submission import Submission, SubmissionStatus, MediaAsset, AssetType, AssetStatus
from app.models.task import Task
from app.models.annotation import Annotation, AnnotationSource
from app.models.review import QualityReview, ReviewDecision
from app.services.s3_service import s3_service
from workers.workflows.video_processing_workflow import VideoProcessingPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [AI-WORKER]: %(message)s"
)
logger = logging.getLogger("robolens_worker")


def create_synthetic_demo_video(output_path: str, duration_sec: int = 15, fps: int = 30) -> str:
    """
    Generate synthetic demonstration video for development/testing
    when camera stream or S3 video is in offline development mode.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    try:
        import cv2
        import numpy as np

        width, height = 1280, 720
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        total_frames = duration_sec * fps
        for i in range(total_frames):
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            # Draw synthetic tabletop environment
            cv2.rectangle(frame, (100, 300), (1180, 700), (45, 52, 58), -1)
            # Draw cup moving across frame
            x_pos = int(200 + (800 * (i / total_frames)))
            cv2.circle(frame, (x_pos, 450), 40, (0, 229, 255), -1)
            cv2.putText(
                frame,
                f"ROBOLENS AI TRAINING CAPTURE - Frame {i}/{total_frames}",
                (50, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (255, 255, 255),
                2
            )
            out.write(frame)

        out.release()
        return output_path
    except Exception as e:
        logger.warning(f"Could not synthesize video via cv2 ({e}), creating dummy file")
        with open(output_path, "wb") as f:
            f.write(b"ROBOLENS_SYNTHETIC_VIDEO_BYTES" * 1024)
        return output_path


def process_single_submission(
    submission_id: str,
    scratch_dir: str = "./scratch/worker_media",
    db_session=None
) -> bool:
    """Process an individual submission currently queued in PROCESSING status."""
    should_close_db = False
    if db_session is None:
        db = SessionLocal()
        should_close_db = True
    else:
        db = db_session
    try:
        submission = db.query(Submission).filter(
            Submission.id == submission_id,
            Submission.status == SubmissionStatus.PROCESSING
        ).first()

        if not submission:
            logger.info(f"Submission {submission_id} not found or not in PROCESSING status.")
            return False

        task = db.query(Task).filter(Task.id == submission.task_id).first()
        task_category = task.category if task else "general_manipulation"
        min_dur = task.expected_duration_min if task else 5
        max_dur = task.expected_duration_max if task else 180

        raw_asset = db.query(MediaAsset).filter(
            MediaAsset.submission_id == submission.id,
            MediaAsset.asset_type == AssetType.RAW_VIDEO
        ).first()

        logger.info(f"==> Processing Submission: {submission.id} (Task: {task_category})")

        # 1. Obtain local file to process
        os.makedirs(scratch_dir, exist_ok=True)
        local_video_path = os.path.join(scratch_dir, f"{submission.id}_video.mp4")

        downloaded_from_s3 = False
        if raw_asset and raw_asset.s3_key:
            try:
                logger.info(f"Attempting download from S3: {raw_asset.s3_bucket}/{raw_asset.s3_key}")
                s3_service.client.download_file(raw_asset.s3_bucket, raw_asset.s3_key, local_video_path)
                downloaded_from_s3 = True
            except Exception as e:
                logger.warning(f"Could not download from S3 ({e}); using synthetic video for development testing.")

        if not downloaded_from_s3 and not os.path.exists(local_video_path):
            create_synthetic_demo_video(local_video_path, duration_sec=16)

        # 2. Run Pipeline Orchestrator
        pipeline_result = VideoProcessingPipeline.process_submission(
            submission_id=submission.id,
            video_file_path=local_video_path,
            task_category=task_category,
            min_duration=min_dur,
            max_duration=max_dur
        )

        validation = pipeline_result["validation"]
        annotations_data = pipeline_result["annotations"]
        quality = pipeline_result["quality"]

        # 3. Update MediaAsset technical metadata
        if raw_asset and validation.get("valid"):
            raw_asset.width = validation.get("width")
            raw_asset.height = validation.get("height")
            raw_asset.fps = validation.get("fps")
            raw_asset.duration_seconds = validation.get("duration_seconds")
            raw_asset.status = AssetStatus.VERIFIED

        # 4. Save Candidate AI Annotations
        for anno in annotations_data:
            annotation_record = Annotation(
                submission_id=submission.id,
                label=anno["label"],
                start_time_ms=anno["start_time_ms"],
                end_time_ms=anno["end_time_ms"],
                confidence=anno.get("confidence"),
                source=AnnotationSource.AI_GENERATED,
                model_name=anno.get("model_name", "robolens-action-segmenter-v1"),
                model_version=anno.get("model_version", "1.0.0"),
                revision=1
            )
            db.add(annotation_record)

        # 5. Save Automated Quality Review Record
        review_decision = ReviewDecision.PASS if quality["decision"] == "PASS" else (
            ReviewDecision.NEEDS_REVIEW if quality["decision"] == "NEEDS_REVIEW" else ReviewDecision.FAIL
        )

        quality_review = QualityReview(
            submission_id=submission.id,
            reviewer_id=None,  # Automated check
            decision=review_decision,
            rejection_reason=quality.get("reason") if review_decision == ReviewDecision.FAIL else None,
            feedback_notes=f"Automated Quality Gate: {quality.get('reason')}"
        )
        db.add(quality_review)

        # 6. Update Final Submission State
        final_status_str = pipeline_result["status"]
        if final_status_str == "APPROVED":
            submission.status = SubmissionStatus.APPROVED
        elif final_status_str == "IN_REVIEW":
            submission.status = SubmissionStatus.IN_REVIEW
        else:
            submission.status = SubmissionStatus.FAILED
            submission.rejection_reason = quality.get("reason")

        db.commit()
        logger.info(
            f" [COMPLETED] Submission {submission.id} transitioned to {submission.status} "
            f"({len(annotations_data)} action annotations generated)"
        )
        return True

    except Exception as e:
        db.rollback()
        logger.error(f"Error processing submission {submission_id}: {e}", exc_info=True)
        return False
    finally:
        if should_close_db:
            db.close()


def run_worker_loop(poll_interval_sec: int = 5, run_once: bool = False):
    """Worker polling loop to continuously process incoming submissions."""
    logger.info("ROBOLENS AI Video Worker started. Polling for PROCESSING submissions...")
    
    while True:
        db = SessionLocal()
        try:
            pending_submissions = db.query(Submission).filter(
                Submission.status == SubmissionStatus.PROCESSING
            ).all()
        finally:
            db.close()

        if pending_submissions:
            logger.info(f"Found {len(pending_submissions)} submission(s) pending processing.")
            for sub in pending_submissions:
                process_single_submission(sub.id)
        else:
            if not run_once:
                time.sleep(poll_interval_sec)

        if run_once:
            logger.info("Single-pass execution completed.")
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ROBOLENS Video Processing & AI Worker")
    parser.add_argument("--once", action="store_true", help="Process currently queued jobs once and exit")
    parser.add_argument("--interval", type=int, default=5, help="Polling interval in seconds")
    parser.add_argument("--submission-id", type=str, default=None, help="Process a specific submission ID")
    args = parser.parse_args()

    if args.submission_id:
        process_single_submission(args.submission_id)
    else:
        run_worker_loop(poll_interval_sec=args.interval, run_once=args.once)
