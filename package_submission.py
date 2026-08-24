#!/usr/bin/env python3
"""Package the agent submission into submission.tar.gz for Kaggle.

Usage:
    python package_submission.py

This creates a submission.tar.gz containing:
    - main.py   (the AI agent)
    - deck.csv  (the 60-card deck)

The resulting archive can be submitted directly to the
Pokemon TCG AI Battle Challenge Simulation competition on Kaggle.
"""

import tarfile
import hashlib
from pathlib import Path


def main():
    agent_dir = Path(__file__).resolve().parent / "agent"
    main_py = agent_dir / "main.py"
    deck_csv = agent_dir / "deck.csv"

    # Validate files exist
    if not main_py.exists():
        raise FileNotFoundError(f"main.py not found at {main_py}")
    if not deck_csv.exists():
        raise FileNotFoundError(f"deck.csv not found at {deck_csv}")

    # Validate deck
    deck = [int(line.strip()) for line in deck_csv.read_text().splitlines() if line.strip()]
    if len(deck) != 60:
        raise ValueError(f"Deck must have exactly 60 cards, found {len(deck)}")

    # Validate agent syntax
    import py_compile
    py_compile.compile(str(main_py), doraise=True)
    print(f"[OK] main.py syntax valid")
    print(f"[OK] deck.csv has {len(deck)} cards")

    # Create submission.tar.gz
    output_path = agent_dir.parent / "submission.tar.gz"
    with tarfile.open(output_path, "w:gz") as tar:
        tar.add(main_py, arcname="main.py")
        tar.add(deck_csv, arcname="deck.csv")

    # Compute hash for verification
    file_hash = hashlib.sha256(output_path.read_bytes()).hexdigest()
    file_size = output_path.stat().st_size

    print(f"\n[OK] Submission packaged: {output_path}")
    print(f"     Size: {file_size:,} bytes")
    print(f"     SHA256: {file_hash}")
    print(f"\nSubmit this file to: https://www.kaggle.com/competitions/pokemon-tcg-ai-battle/submissions")


if __name__ == "__main__":
    main()
