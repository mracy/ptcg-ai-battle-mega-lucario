# Pokemon TCG AI Battle Challenge — Solution

## Competition
- **Simulation Category**: Build an AI agent + 60-card deck that plays PTCG on a ladder
- **Strategy Category**: Write a report explaining the strategic logic ($240,000 prize pool)

## Solution Overview

**Deck**: Mega Lucario ex Fighting-type deck with Aura Jab energy acceleration
**Agent**: Context-aware heuristic scoring engine

## Files

| File | Description |
|------|-------------|
| `agent/main.py` | AI agent (~600 lines, pure Python) |
| `agent/deck.csv` | 60-card deck list (card IDs, one per line) |
| `strategy_writeup.md` | Strategy Category Kaggle Writeup (1787 words) |
| `package_submission.py` | Script to create submission.tar.gz |

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
# Upload submission.tar.gz to Kaggle
```

### Strategy Category
1. Go to https://www.kaggle.com/competitions/pokemon-tcg-ai-battle-challenge-strategy
2. Click "New Writeup"
3. Copy the content of `strategy_writeup.md`
4. Select the "Main Track"
5. Click "Submit"

## Agent Architecture

The agent uses a **scoring-based heuristic system**:
- Every legal option at each selection point is scored (0-100)
- The highest-scoring option is selected
- Scores are context-aware (based on game state, HP, energy, etc.)

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
- Graceful degradation if `cg` module is unavailable
- Comprehensive error handling with fallback to first valid option
