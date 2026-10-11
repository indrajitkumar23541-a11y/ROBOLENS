#!/usr/bin/env python3
"""
ROBOLENS Operational CLI
Controlled command-line tooling for internal platform operations and data management.
As defined in ROBOLENS architecture: no web admin portal is exposed; all internal
operations execute through secured CLI tools and backend services.
"""

import argparse
import os
import sys
import json
from typing import Optional

# Ensure backend root is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.task import Task, TaskStatus
from app.models.submission import Submission, SubmissionStatus, MediaAsset
from app.models.annotation import Annotation, AnnotationSource
from app.models.review import QualityReview, ReviewDecision
from app.models.dataset import Dataset, DatasetVersion, DatasetVersionStatus
from app.models.user import User, UserRole
from app.services.dataset_export_service import dataset_export_service


def cmd_status(args):
    """Check health and print stats of the platform."""
    db: Session = SessionLocal()
    try:
        tasks_count = db.query(Task).count()
        submissions_count = db.query(Submission).count()
        approved_count = db.query(Submission).filter(Submission.status == SubmissionStatus.APPROVED).count()
        pending_review_count = db.query(Submission).filter(Submission.status == SubmissionStatus.IN_REVIEW).count()
        datasets_count = db.query(Dataset).count()
        users_count = db.query(User).count()

        print("=" * 55)
        print("          ROBOLENS PLATFORM OPERATIONAL STATUS          ")
        print("=" * 55)
        print(f" Registered Users:           {users_count}")
        print(f" Active Tasks:               {tasks_count}")
        print(f" Total Submissions:          {submissions_count}")
        print(f"   - Pending Review:         {pending_review_count}")
        print(f"   - Approved (Released):    {approved_count}")
        print(f" Benchmark Datasets:         {datasets_count}")
        print("=" * 55)
    finally:
        db.close()


def cmd_list_tasks(args):
    """List collection tasks."""
    db: Session = SessionLocal()
    try:
        tasks = db.query(Task).all()
        print(f"\n{'ID':<38} | {'CATEGORY':<14} | {'STATUS':<8} | {'TITLE'}")
        print("-" * 80)
        for t in tasks:
            print(f"{t.id:<38} | {t.category:<14} | {t.status.value:<8} | {t.title}")
    finally:
        db.close()


def cmd_review_queue(args):
    """List submissions waiting for human quality review."""
    db: Session = SessionLocal()
    try:
        subs = (
            db.query(Submission)
            .filter(Submission.status.in_([SubmissionStatus.IN_REVIEW, SubmissionStatus.PROCESSING]))
            .order_by(Submission.created_at.asc())
            .all()
        )
        print(f"\nPending Review Queue ({len(subs)} submissions):")
        print(f"{'SUBMISSION ID':<38} | {'STATUS':<12} | {'TASK ID':<38}")
        print("-" * 92)
        for s in subs:
            print(f"{s.id:<38} | {s.status.value:<12} | {s.task_id:<38}")
    finally:
        db.close()


def cmd_review_approve(args):
    """Approve a submission for inclusion in training datasets."""
    db: Session = SessionLocal()
    try:
        sub = db.query(Submission).filter(Submission.id == args.submission_id).first()
        if not sub:
            print(f"Error: Submission {args.submission_id} not found.")
            sys.exit(1)

        sub.status = SubmissionStatus.APPROVED
        review = QualityReview(
            submission_id=sub.id,
            reviewer_id="cli-operator",
            decision=ReviewDecision.APPROVED,
            feedback_notes=args.notes or "Approved via ROBOLENS operational CLI"
        )
        db.add(review)
        db.commit()
        print(f"Successfully APPROVED submission {sub.id} (Episode {sub.episode_id}).")
    finally:
        db.close()


def cmd_review_reject(args):
    """Reject a submission with a documented reason."""
    db: Session = SessionLocal()
    try:
        sub = db.query(Submission).filter(Submission.id == args.submission_id).first()
        if not sub:
            print(f"Error: Submission {args.submission_id} not found.")
            sys.exit(1)

        sub.status = SubmissionStatus.REJECTED
        sub.rejection_reason = args.reason
        review = QualityReview(
            submission_id=sub.id,
            reviewer_id="cli-operator",
            decision=ReviewDecision.REJECTED,
            rejection_reason=args.reason,
            feedback_notes=args.notes or "Rejected via ROBOLENS operational CLI"
        )
        db.add(review)
        db.commit()
        print(f"Successfully REJECTED submission {sub.id}. Reason: {args.reason}")
    finally:
        db.close()


def cmd_datasets_list(args):
    """List datasets and published versions."""
    db: Session = SessionLocal()
    try:
        datasets = db.query(Dataset).all()
        print(f"\n{'DATASET ID':<38} | {'SLUG':<25} | {'NAME'}")
        print("-" * 80)
        for d in datasets:
            versions = db.query(DatasetVersion).filter(DatasetVersion.dataset_id == d.id).all()
            ver_str = ", ".join(f"{v.version_tag} ({v.status.value})" for v in versions)
            print(f"{d.id:<38} | {d.slug:<25} | {d.name}")
            print(f"  Versions: {ver_str or 'None'}")
    finally:
        db.close()


def cmd_dataset_export(args):
    """Export dataset manifest in LeRobot, RLDS, or JSON format."""
    db: Session = SessionLocal()
    try:
        dataset = db.query(Dataset).filter((Dataset.id == args.dataset_id) | (Dataset.slug == args.dataset_id)).first()
        if not dataset:
            print(f"Error: Dataset {args.dataset_id} not found.")
            sys.exit(1)

        version = (
            db.query(DatasetVersion)
            .filter(
                DatasetVersion.dataset_id == dataset.id,
                DatasetVersion.status == DatasetVersionStatus.PUBLISHED
            )
            .order_by(DatasetVersion.created_at.desc())
            .first()
        )
        if not version:
            print(f"Error: No published version found for dataset {dataset.slug}.")
            sys.exit(1)

        manifest = dataset_export_service.generate_export_manifest(
            db=db,
            dataset=dataset,
            version=version,
            format_type=args.format.upper()
        )

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
            print(f"Manifest written to {args.output}")
        else:
            print(json.dumps(manifest, indent=2))
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="ROBOLENS Operational CLI — Controlled platform administration"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # status
    p_status = subparsers.add_parser("status", help="Show system status and metrics")
    p_status.set_defaults(func=cmd_status)

    # tasks
    p_tasks = subparsers.add_parser("tasks", help="Manage recording tasks")
    p_tasks_sub = p_tasks.add_subparsers(dest="subcommand", required=True)
    p_tasks_list = p_tasks_sub.add_parser("list", help="List active collection tasks")
    p_tasks_list.set_defaults(func=cmd_list_tasks)

    # reviews
    p_reviews = subparsers.add_parser("reviews", help="Manage quality review operations")
    p_reviews_sub = p_reviews.add_subparsers(dest="subcommand", required=True)
    p_rev_queue = p_reviews_sub.add_parser("queue", help="List review queue")
    p_rev_queue.set_defaults(func=cmd_review_queue)

    p_rev_approve = p_reviews_sub.add_parser("approve", help="Approve submission")
    p_rev_approve.add_argument("submission_id", help="Submission UUID")
    p_rev_approve.add_argument("--notes", help="Optional reviewer feedback notes")
    p_rev_approve.set_defaults(func=cmd_review_approve)

    p_rev_reject = p_reviews_sub.add_parser("reject", help="Reject submission")
    p_rev_reject.add_argument("submission_id", help="Submission UUID")
    p_rev_reject.add_argument("--reason", required=True, help="Rejection rationale")
    p_rev_reject.add_argument("--notes", help="Optional internal notes")
    p_rev_reject.set_defaults(func=cmd_review_reject)

    # datasets
    p_datasets = subparsers.add_parser("datasets", help="Manage datasets & releases")
    p_datasets_sub = p_datasets.add_subparsers(dest="subcommand", required=True)
    p_ds_list = p_datasets_sub.add_parser("list", help="List datasets")
    p_ds_list.set_defaults(func=cmd_datasets_list)

    p_ds_export = p_datasets_sub.add_parser("export", help="Generate export manifest")
    p_ds_export.add_argument("dataset_id", help="Dataset ID or slug")
    p_ds_export.add_argument("--format", default="LEROBOT", choices=["LEROBOT", "RLDS", "JSON_MANIFEST"], help="Export schema format")
    p_ds_export.add_argument("-o", "--output", help="Output file path (default: stdout)")
    p_ds_export.set_defaults(func=cmd_dataset_export)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
