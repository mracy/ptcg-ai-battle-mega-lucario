# Pokemon TCG AI Battle Challenge — Solution

## Competition
- **Simulation Category**: Build an AI agent + 60-card deck that plays PTCG on a ladder
- **Strategy Category**: Write a report explaining the strategic logic ($240,000 prize pool)

## Solution Overview

**Deck**: Mega Lucario ex Fighting-type deck with Aura Jab energy acceleration
**Agent**: Context-aware heuristic scoring engine with opponent tracking and search API lookahead

---

## Setup

### Prerequisites
- Python 3.8+ (tested on Python 3.14)
- No external dependencies required for local testing
- The competition's `cg` module is only available on Kaggle

### Clone the Repository
```bash
git clone https://github.com/mracy/ptcg-ai-battle-mega-lucario.git
cd ptcg-ai-battle-mega-lucario
```

### Verify Installation
```bash
python -c "from agent.main import agent; print(f'Deck: {len(agent(None))} cards loaded OK')"
```

Expected output:
```
Deck: 60 cards loaded OK
```

---

## Project Structure

```
ptcg-ai-battle-mega-lucario/
├── agent/
│   ├── main.py              # AI agent (heuristic scoring engine)
│   └── deck.csv             # 60-card deck list (card IDs, one per line)
├── test_agent.py            # Unit tests (51 tests)
├── run_battle.py            # Battle simulation script
├── analyze_deck.py          # Deck analysis with consistency metrics
├── package_submission.py    # Creates submission.tar.gz for Kaggle
├── generate_media.py        # Generates visualization images
├── strategy_writeup.md      # Strategy Category writeup (1787 words)
├── kaggle_writeup_body.md   # Writeup body for Kaggle form paste
├── README.md                # This file
└── media/                   # Generated charts and diagrams
    ├── 01_deck_composition.png
    ├── 02_archetype_comparison.png
    ├── 03_decision_pipeline.png
    ├── 04_scoring_heatmap.png
    ├── 05_energy_strategy.png
    ├── 06_matchup_table.png
    ├── 07_hypothesis_summary.png
    └── 08_consistency_chart.png
```

---

## How to Run

> **IMPORTANT**: Run all commands from the **project root directory**, NOT from inside `agent/`.

### 1. Run Unit Tests
```bash
python test_agent.py
```

Expected output:
```
Ran 51 tests in 0.0XXs
OK
```

### 2. Run Battle Simulation
```bash
# Self-play (agent vs agent) — 30 games
python run_battle.py --games 30 --opponent self

# vs random baseline — 20 games
python run_battle.py --games 20 --opponent random

# vs greedy (first-option) baseline — 20 games
python run_battle.py --games 20 --opponent greedy
```

### 3. Run Deck Analysis
```bash
python analyze_deck.py
```

This outputs:
- Card type distribution
- Legality check
- Consistency metrics (hypergeometric probabilities)
- Energy curve analysis
- Search & draw engine summary
- Setup probability for turns 1-2
- Generates `media/08_consistency_chart.png`

### 4. Generate Media Gallery Images
```bash
python generate_media.py
```

Generates 7 visualization PNGs in `media/` directory.

### 5. Package Kaggle Submission
```bash
python package_submission.py
```

Creates `submission.tar.gz` containing `main.py` + `deck.csv`.

### 6. Quick Test (Agent Loads Correctly)
```bash
python -c "from agent.main import agent; print(f'Deck: {len(agent(None))} cards loaded OK')"
```

---

## All Commands Summary

Run these from the project root (`ptcg-ai-battle-mega-lucario/`):

```bash
# Test
python test_agent.py

# Simulate
python run_battle.py --games 30 --opponent self

# Analyze
python analyze_deck.py

# Generate images
python generate_media.py

# Package for Kaggle
python package_submission.py
```

---

## Deck Composition

| Card | ID | Count | Role |
|------|----|-------|------|
| Riolu (70 HP) | 974 | 4 | Basic Pokemon |
| Mega Lucario ex | 678 | 4 | Main attacker (340 HP) |
| Mega Signal | 1145 | 4 | Search Mega Evolution ex |
| Buddy-Buddy Poffin | 1086 | 3 | Bench Basic Pokemon (≤70 HP) |
| Salvatore | 1189 | 2 | Same-turn evolution |
| Cyrano | 1205 | 2 | Search up to 3 Pokemon ex |
| Ultra Ball | 1121 | 2 | Search any Pokemon |
| Lillie's Determination | 1227 | 4 | Draw 6-8 cards |
| Waitress | 1235 | 3 | Energy from top 6 of deck |
| Crispin | 1198 | 2 | Energy search + attach |
| Tarragon | 1238 | 2 | Recovery from discard |
| Switch | 1123 | 2 | Switch active with bench |
| Boss's Orders | 1182 | 1 | Gust opponent's benched |
| Energy Retrieval | 1118 | 1 | Energy from discard |
| Powerglass | 1163 | 1 | Tool: energy from discard EOT |
| Maximum Belt | 1158 | 1 | ACE SPEC: +50 damage |
| Basic Fighting Energy | 6 | 22 | Energy |

**Total**: 8 Pokemon + 30 Trainers + 22 Energy = 60 cards

## Key Strategy

1. **Setup**: Use Buddy-Buddy Poffin to bench Riolu, Mega Signal to find Mega Lucario ex
2. **Evolve**: Use Salvatore for same-turn evolution (Riolu → Mega Lucario ex)
3. **Attack**: Aura Jab (1 energy, 130 damage + ramp 3 energy to bench)
4. **Finish**: Mega Brave (2 energy, 270 damage) for KOs
5. **Recover**: Tarragon recovers Fighting Pokemon + energy from discard

## How to Submit

### Simulation Category
```bash
python package_submission.py
# Upload submission.tar.gz to https://www.kaggle.com/competitions/pokemon-tcg-ai-battle/submissions
```

### Strategy Category
1. Go to https://www.kaggle.com/competitions/pokemon-tcg-ai-battle-challenge-strategy
2. Click "New Writeup"
3. Fill in:
   - **Title**: `Fighting Spirit: A Heuristic Energy-Acceleration Agent for Mega Lucario ex`
   - **URL**: `fighting-spirit-mega-lucario-ex`
   - **Subtitle**: `Context-Aware Decision-Making with Aura Jab Energy Ramp in the PTCG AI Battle Challenge`
4. Paste content from `kaggle_writeup_body.md` into Project Description
5. Upload images from `media/` to Media Gallery
6. Select "Main Track"
7. Click "Submit"

## Agent Architecture

The agent uses a **scoring-based heuristic system**:
- Every legal option at each selection point is scored (0-100)
- The highest-scoring option is selected
- Scores are context-aware (based on game state, HP, energy, etc.)
- Opponent behavior tracking across turns
- Search API 1-ply lookahead for MAIN selections
- Board state evaluation (-100 to +100)

### Selection Handlers
- **MAIN**: Scores PLAY/EVOLVE/ATTACH/ATTACK/RETREAT/END options
- **ATTACK**: Chooses between Aura Jab and Mega Brave based on KO potential
- **CARD**: Context-specific (setup, search, discard, switch, etc.)
- **YES_NO**: Mulligan (NO), go first (YES), activate effects (YES)
- **COUNT**: Maximizes draw/damage counter counts
- **ENERGY/ATTACHED_CARD**: Targets opponent's cards when possible

## Technical Notes

- No external dependencies beyond the competition's `cg` module
- Lazy-loaded attack/card data caches for performance
- Graceful degradation if `cg` module is unavailable (falls back to deck loading)
- Comprehensive error handling with fallback to first valid option
- 51 unit tests, all passing
- Deterministic (no randomness in decision logic)
