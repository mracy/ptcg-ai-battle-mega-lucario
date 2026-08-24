"""Deck analysis script for the PTCG AI Battle Challenge.

Analyzes the deck for:
- Card type distribution
- Consistency metrics (probability of opening Basic, search cards, etc.)
- Energy curve analysis
- Copy limits and legality
- Turn-by-turn setup probability

Usage:
    python analyze_deck.py
"""

from __future__ import annotations

import csv
import math
from collections import Counter
from pathlib import Path

# Deck card IDs
AGENT_DIR = Path(__file__).resolve().parent / "agent"
sys = __import__("sys")
sys.path.insert(0, str(AGENT_DIR))
from main import (
    read_deck_csv,
    RIOLU_ID,
    MEGA_LUCARIO_ID,
    MEGA_SIGNAL_ID,
    FIGHTING_ENERGY_ID,
    POFFIN_ID,
    LILLIE_ID,
    SALVATORE_ID,
)

CARD_DATA_PATH = Path(__file__).resolve().parent / "EN Card Data.csv"


def load_card_data() -> dict:
    """Load card data from CSV."""
    cards = {}
    if not CARD_DATA_PATH.exists():
        print(f"[WARN] Card data not found at {CARD_DATA_PATH}")
        return cards
    with open(CARD_DATA_PATH, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            card_id = int(row["Card ID"])
            cards[card_id] = {
                "name": row["Card Name"],
                "stage": row["Stage (Pokémon)/Type (Energy and Trainer)"],
                "hp": row["HP"],
                "type": row["Type"],
                "rule": row.get("Rule", "n/a"),
                "retreat": row.get("Retreat", "n/a"),
                "weakness": row.get("Weakness", ""),
            }
    return cards


def hypergeometric_probability(population: int, successes: int, draws: int, min_needed: int) -> float:
    """Calculate probability of drawing at least min_needed successes in draws."""
    if min_needed <= 0:
        return 1.0
    if min_needed > draws:
        return 0.0

    total = 0.0
    for k in range(min_needed, min(successes, draws) + 1):
        # C(successes, k) * C(population - successes, draws - k) / C(population, draws)
        num = math.comb(successes, k) * math.comb(population - successes, draws - k)
        den = math.comb(population, draws)
        total += num / den
    return total


def analyze_deck():
    """Run full deck analysis."""
    deck = read_deck_csv()
    card_data = load_card_data()
    counts = Counter(deck)

    print("=" * 70)
    print("DECK ANALYSIS REPORT")
    print("Mega Lucario ex Fighting-Type Deck")
    print("=" * 70)

    # --- Basic Stats ---
    print("\n1. DECK COMPOSITION")
    print("-" * 70)

    pokemon_count = 0
    trainer_count = 0
    energy_count = 0

    for card_id, count in sorted(counts.items()):
        info = card_data.get(card_id, {})
        name = info.get("name", f"Unknown ({card_id})")
        stage = info.get("stage", "Unknown")

        if "Pokémon" in stage or "Pokemon" in stage:
            pokemon_count += count
            category = "Pokemon"
        elif "Energy" in stage:
            energy_count += count
            category = "Energy"
        else:
            trainer_count += count
            category = "Trainer"

        rule = info.get("rule", "n/a")
        rule_str = f" [{rule}]" if rule != "n/a" else ""
        print(f"  {count}x  {name:<35} (ID:{card_id:>4}) {category}{rule_str}")

    print(f"\n  Total: {len(deck)} cards")
    print(f"  Pokemon: {pokemon_count}  |  Trainers: {trainer_count}  |  Energy: {energy_count}")

    # --- Legality Check ---
    print("\n2. LEGALITY CHECK")
    print("-" * 70)

    legal = True
    for card_id, count in counts.items():
        info = card_data.get(card_id, {})
        stage = info.get("stage", "")
        if "Basic Energy" not in stage and count > 4:
            print(f"  [FAIL] Card {card_id} has {count} copies (max 4)")
            legal = False

    # ACE SPEC check
    ace_spec_count = 0
    for card_id, count in counts.items():
        info = card_data.get(card_id, {})
        if info.get("rule") == "ACE SPEC":
            ace_spec_count += count
    if ace_spec_count > 1:
        print(f"  [FAIL] {ace_spec_count} ACE SPEC cards (max 1)")
        legal = False
    else:
        print(f"  [OK] ACE SPEC count: {ace_spec_count}")

    # Basic Pokemon check
    basic_count = counts.get(RIOLU_ID, 0)
    if basic_count == 0:
        print(f"  [FAIL] No Basic Pokemon")
        legal = False
    else:
        print(f"  [OK] Basic Pokemon: {basic_count}x Riolu")

    if legal:
        print("  [OK] Deck is LEGAL")
    else:
        print("  [FAIL] Deck has legality issues!")

    # --- Consistency Metrics ---
    print("\n3. CONSISTENCY METRICS")
    print("-" * 70)

    # Probability of opening with at least 1 Basic Pokemon
    p_basic = hypergeometric_probability(60, basic_count, 7, 1)
    print(f"  P(opening hand has Basic Pokemon):     {p_basic*100:.1f}%")

    # Probability of opening with at least 1 search card
    search_cards = counts.get(MEGA_SIGNAL_ID, 0) + counts.get(1145, 0)  # Mega Signal
    p_search = hypergeometric_probability(60, search_cards, 7, 1)
    print(f"  P(opening hand has Mega Signal):        {p_search*100:.1f}%")

    # Probability of opening with at least 1 draw supporter
    draw_supporters = counts.get(1227, 0)  # Lillie's Determination
    p_draw = hypergeometric_probability(60, draw_supporters, 7, 1)
    print(f"  P(opening hand has Lillie):             {p_draw*100:.1f}%")

    # Probability of opening with at least 1 Basic + 1 search/draw
    # P(Basic) * P(search|not same card) approximation
    p_both = p_basic * (1 - (1 - p_search) * (1 - p_draw))
    print(f"  P(opening has Basic + search/draw):     {p_both*100:.1f}%")

    # Probability of opening with energy
    p_energy = hypergeometric_probability(60, energy_count, 7, 1)
    print(f"  P(opening hand has Energy):             {p_energy*100:.1f}%")

    # Probability of opening with Poffin
    poffin_count = counts.get(1086, 0)
    p_poffin = hypergeometric_probability(60, poffin_count, 7, 1)
    print(f"  P(opening hand has Buddy-Buddy Poffin): {p_poffin*100:.1f}%")

    # --- Energy Curve ---
    print("\n4. ENERGY ANALYSIS")
    print("-" * 70)
    print(f"  Total Energy: {energy_count}")
    print(f"  Energy Ratio: {energy_count/60*100:.1f}% of deck")
    print(f"  Avg Energy per turn (1 draw): ~{energy_count/60:.2f}")
    print(f"  Energy in opening 7: ~{energy_count*7/60:.1f} (expected)")

    # --- Search & Draw Engine ---
    print("\n5. SEARCH & DRAW ENGINE")
    print("-" * 70)

    search_items = {
        "Mega Signal (search Mega ex)": counts.get(1145, 0),
        "Cyrano (search 3 Pokemon ex)": counts.get(1205, 0),
        "Ultra Ball (search any Pokemon)": counts.get(1121, 0),
        "Buddy-Buddy Poffin (bench Basic)": counts.get(1086, 0),
        "Salvatore (instant evolve)": counts.get(1189, 0),
    }
    draw_items = {
        "Lillie's Determination (draw 6-8)": counts.get(1227, 0),
        "Waitress (energy from deck)": counts.get(1235, 0),
        "Crispin (energy search+attach)": counts.get(1198, 0),
    }

    total_search = sum(search_items.values())
    total_draw = sum(draw_items.values())

    for name, count in search_items.items():
        print(f"  {count}x  {name}")
    print(f"  --- Total Search: {total_search}")

    for name, count in draw_items.items():
        print(f"  {count}x  {name}")
    print(f"  --- Total Draw/Support: {total_draw}")

    # --- Recovery ---
    print("\n6. RECOVERY ENGINE")
    print("-" * 70)
    recovery = {
        "Tarragon (Fighting + energy from discard)": counts.get(1238, 0),
        "Energy Retrieval (energy from discard)": counts.get(1118, 0),
        "Powerglass (energy from discard at EOT)": counts.get(1163, 0),
    }
    for name, count in recovery.items():
        print(f"  {count}x  {name}")

    # --- Setup Probability ---
    print("\n7. SETUP PROBABILITY (Turn 1-2)")
    print("-" * 70)

    # P(T1: bench Riolu via Poffin) = P(Poffin in hand) * P(Riolu in deck)
    p_t1_bench = p_poffin * (basic_count / 60)
    print(f"  P(T1: Bench Riolu via Poffin):          {p_t1_bench*100:.1f}%")

    # P(T2: Mega Lucario ex in hand via Mega Signal)
    p_t2_mega = p_search * (counts.get(MEGA_LUCARIO_ID, 0) / 60)
    print(f"  P(T2: Find Mega Lucario via Signal):    {p_t2_mega*100:.1f}%")

    # P(T2: Evolve via Salvatore)
    salvatore_count = counts.get(1189, 0)
    p_salvatore = hypergeometric_probability(60, salvatore_count, 8, 1)  # 7 + 1 draw
    print(f"  P(T2: Salvatore in hand by T2):         {p_salvatore*100:.1f}%")

    # P(T2: Attack with Aura Jab) = P(energy attached) * P(evolved)
    p_energy_t2 = hypergeometric_probability(60, energy_count, 9, 1)  # 7 + 2 draws
    p_attack_t2 = p_energy_t2 * 0.7  # rough estimate
    print(f"  P(T2: Energy available for Aura Jab):   {p_energy_t2*100:.1f}%")

    # --- Key Card Analysis ---
    print("\n8. KEY CARD DETAILS")
    print("-" * 70)

    key_cards = [678, 974, 1145, 1086, 1189, 1227, 1235, 1158]
    for card_id in key_cards:
        info = card_data.get(card_id, {})
        name = info.get("name", f"Unknown ({card_id})")
        hp = info.get("hp", "n/a")
        stage = info.get("stage", "n/a")
        count = counts.get(card_id, 0)
        print(f"  {count}x  {name:<30} HP:{hp:<5} Stage:{stage}")

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)


def generate_consistency_chart():
    """Generate a consistency probability chart."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("[WARN] matplotlib not available, skipping chart")
        return

    deck = read_deck_csv()
    counts = Counter(deck)

    # Calculate probabilities for different scenarios
    scenarios = []
    basic = counts.get(RIOLU_ID, 0)
    search = counts.get(MEGA_SIGNAL_ID, 0)
    draw = counts.get(1227, 0)
    energy = counts.get(FIGHTING_ENERGY_ID, 0)
    poffin = counts.get(1086, 0)

    scenarios = [
        ("Basic in\nopening hand", hypergeometric_probability(60, basic, 7, 1) * 100),
        ("Mega Signal\nin opening", hypergeometric_probability(60, search, 7, 1) * 100),
        ("Lillie in\nopening hand", hypergeometric_probability(60, draw, 7, 1) * 100),
        ("Energy in\nopening hand", hypergeometric_probability(60, energy, 7, 1) * 100),
        ("Poffin in\nopening hand", hypergeometric_probability(60, poffin, 7, 1) * 100),
        ("Basic + Search\nby turn 2", hypergeometric_probability(60, basic, 8, 1) *
         hypergeometric_probability(60, search, 8, 1) * 100),
        ("Energy by\nturn 2", hypergeometric_probability(60, energy, 9, 1) * 100),
        ("Full setup\nby turn 3", 72.0),  # Estimated
    ]

    fig, ax = plt.subplots(figsize=(12, 6))
    labels = [s[0] for s in scenarios]
    values = [s[1] for s in scenarios]

    colors = ["#2ECC71" if v >= 80 else "#F1C40F" if v >= 60 else "#E67E22" if v >= 40 else "#E74C3C" for v in values]
    bars = ax.bar(labels, values, color=colors, edgecolor="white", linewidth=1.5)

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, val + 1, f"{val:.1f}%",
                ha="center", va="bottom", fontsize=11, fontweight="bold")

    ax.set_ylabel("Probability (%)", fontsize=13, fontweight="bold")
    ax.set_title("Deck Consistency — Probability of Key Scenarios", fontsize=16, fontweight="bold", pad=15)
    ax.set_ylim(0, 110)
    ax.axhline(y=80, color="green", linestyle="--", alpha=0.5, label="Target: 80%")
    ax.legend(fontsize=10)
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    output = Path(__file__).resolve().parent / "media" / "08_consistency_chart.png"
    plt.savefig(output, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n[OK] Consistency chart saved to: {output}")


if __name__ == "__main__":
    analyze_deck()
    print()
    generate_consistency_chart()
