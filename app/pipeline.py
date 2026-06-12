"""Main pipeline orchestrator.

Usage:
    python -m app.pipeline              # full pipeline: scan + transcripts + predictions
    python -m app.pipeline --scan-only  # only ingest new videos from YouTube
    python -m app.pipeline --seed       # load demo data (no API key needed)
"""

from __future__ import annotations

import argparse
import sys

from app.extraction.predictions import extract_predictions
from app.extraction.transcript import extract_transcript
from app.ingestion.channel_scanner import ChannelScanner
from app.models.domain import VideoStatus
from app.storage import get_repo
from app.utils.logger import get_logger

logger = get_logger(__name__)


def run_ingestion() -> int:
    repo = get_repo()
    scanner = ChannelScanner(repo)
    return scanner.scan_all()


def run_transcripts() -> int:
    repo = get_repo()
    pending = repo.list_videos(status=VideoStatus.PENDING)
    count = 0
    for video in pending:
        transcript = extract_transcript(video.video_id, video.language or "en")
        repo.upsert_transcript(transcript)
        new_status = (
            VideoStatus.TRANSCRIPT_FETCHED
            if transcript.status in ("available", "auto_generated")
            else VideoStatus.TRANSCRIPT_UNAVAILABLE
        )
        repo.update_video_status(video.video_id, new_status)
        count += 1
    logger.info(f"Transcripts processed: {count}")
    return count


def run_predictions() -> int:
    repo = get_repo()
    videos = repo.list_videos(status=VideoStatus.TRANSCRIPT_FETCHED)
    count = 0
    for video in videos:
        transcript = repo.get_transcript(video.video_id)
        if not transcript or not transcript.raw_text:
            continue
        prediction = extract_predictions(
            transcript.raw_text,
            video.video_id,
            video.channel_id,
            video.language or "en",
        )
        repo.save_prediction(prediction)
        repo.update_video_status(video.video_id, VideoStatus.PREDICTIONS_EXTRACTED)
        count += 1
    logger.info(f"Predictions extracted: {count}")
    return count


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="SatisGraph pipeline")
    parser.add_argument("--scan-only", action="store_true", help="Only scan YouTube for new videos")
    parser.add_argument("--transcripts-only", action="store_true", help="Only fetch transcripts")
    parser.add_argument("--predictions-only", action="store_true", help="Only extract predictions")
    parser.add_argument("--seed", action="store_true", help="Load demo data")
    args = parser.parse_args(argv)

    if args.seed:
        from data.demo.seed_data import seed
        seed()
        return

    if args.scan_only:
        run_ingestion()
    elif args.transcripts_only:
        run_transcripts()
    elif args.predictions_only:
        run_predictions()
    else:
        logger.info("Running full pipeline…")
        run_ingestion()
        run_transcripts()
        run_predictions()
        stats = get_repo().stats()
        logger.info(f"Pipeline complete. Stats: {stats}")


if __name__ == "__main__":
    main()
