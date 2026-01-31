#!/usr/bin/env python3
"""Replay captured OpenLineage events for testing.

Usage:
    python replay_events.py <captured_events_dir> [--endpoint http://localhost:8000/api/v1/lineage]
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import httpx
except ImportError:
    print("Error: httpx is required. Install with: pip install httpx")
    sys.exit(1)


def replay_events(
    events_dir: Path,
    endpoint: str = "http://localhost:8000/api/v1/lineage",
    delay_ms: int = 0,
) -> None:
    """Replay all captured events in chronological order."""
    import time
    
    if not events_dir.exists():
        print(f"Error: Directory not found: {events_dir}")
        sys.exit(1)
    
    # Get all JSON files sorted by filename (which includes timestamp)
    event_files = sorted(events_dir.glob("*.json"))
    
    if not event_files:
        print(f"No event files found in {events_dir}")
        return
    
    print(f"Found {len(event_files)} events to replay")
    print(f"Target endpoint: {endpoint}")
    print()
    
    client = httpx.Client(timeout=30.0)
    success_count = 0
    error_count = 0
    
    for event_file in event_files:
        try:
            with open(event_file) as f:
                event_data = json.load(f)
            
            print(f"Replaying: {event_file.name}...", end=" ")
            response = client.post(endpoint, json=event_data)
            response.raise_for_status()
            
            print(f"✓ {response.status_code}")
            success_count += 1
            
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)
                
        except httpx.HTTPError as exc:
            print(f"✗ HTTP Error: {exc}")
            error_count += 1
        except json.JSONDecodeError as exc:
            print(f"✗ Invalid JSON: {exc}")
            error_count += 1
        except Exception as exc:
            print(f"✗ Error: {exc}")
            error_count += 1
    
    print()
    print(f"Results: {success_count} succeeded, {error_count} failed")
    
    client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay captured OpenLineage events")
    parser.add_argument(
        "events_dir",
        type=Path,
        help="Directory containing captured event JSON files"
    )
    parser.add_argument(
        "--endpoint",
        default="http://localhost:8000/api/v1/lineage",
        help="OpenLineage collector endpoint (default: http://localhost:8000/api/v1/lineage)"
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=0,
        help="Delay in milliseconds between events (default: 0)"
    )
    
    args = parser.parse_args()
    
    replay_events(args.events_dir, args.endpoint, args.delay)


if __name__ == "__main__":
    main()

