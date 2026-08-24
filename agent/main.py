"""Heuristic AI Training Agent for Pokemon TCG AI Battle Challenge.

Strategy: Mega Lucario ex fighting-type deck with energy acceleration.
The agent uses context-aware heuristics to make decisions at each selection point,
prioritizing: setup -> energy acceleration -> high-damage attacks -> prize card racing.
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Card IDs in our deck
# ---------------------------------------------------------------------------
RIOLU_ID = 974
MEGA_LUCARIO_ID = 678
MEGA_SIGNAL_ID = 1145
POFFIN_ID = 1086
SALVATORE_ID = 1189
CYRANO_ID = 1205
ULTRA_BALL_ID = 1121
LILLIE_ID = 1227
WAITRESS_ID = 1235
CRISPIN_ID = 1198
TARRAGON_ID = 1238
SWITCH_ID = 1123
BOSS_ORDERS_ID = 1182
ENERGY_RETRIEVAL_ID = 1118
POWERGLASS_ID = 1163
MAXIMUM_BELT_ID = 1158
FIGHTING_ENERGY_ID = 6

# Attack names for Mega Lucario ex
AURA_JAB_NAME = "Aura Jab"
MEGA_BRAVE_NAME = "Mega Brave"

# Cards we always want to search for
SEARCH_POKEMON_EX_IDS = {MEGA_LUCARIO_ID}
SEARCH_BASIC_IDS = {RIOLU_ID}
SEARCH_MEGA_IDS = {MEGA_LUCARIO_ID}

# ---------------------------------------------------------------------------
# Try to import the engine API
# ---------------------------------------------------------------------------
try:
    from cg.api import (
        OptionType,
        SelectContext,
        SelectType,
        to_observation_class,
        all_attack,
        all_card_data,
        search_begin,
        search_step,
        search_end,
        search_release,
    )
    _CG_AVAILABLE = True
    _SEARCH_AVAILABLE = True
except Exception:
    _CG_AVAILABLE = False
    _SEARCH_AVAILABLE = False

    class _DummyEnum:
        def __init__(self, *pairs):
            for name, val in pairs:
                setattr(self, name, val)

        def __getattr__(self, name):
            return -1

    OptionType = _DummyEnum(
        ("NUMBER", 0), ("YES", 1), ("NO", 2), ("CARD", 3), ("TOOL_CARD", 4),
        ("ENERGY_CARD", 5), ("ENERGY", 6), ("PLAY", 7), ("ATTACH", 8),
        ("EVOLVE", 9), ("ABILITY", 10), ("DISCARD", 11), ("RETREAT", 12),
        ("ATTACK", 13), ("END", 14), ("SKILL", 15), ("SPECIAL_CONDITION", 16),
    )
    SelectType = _DummyEnum(
        ("MAIN", 0), ("CARD", 1), ("ATTACHED_CARD", 2),
        ("CARD_OR_ATTACHED_CARD", 3), ("ENERGY", 4), ("SKILL", 5),
        ("ATTACK", 6), ("EVOLVE", 7), ("COUNT", 8), ("YES_NO", 9),
        ("SPECIAL_CONDITION", 10),
    )
    SelectContext = _DummyEnum(
        ("MAIN", 0), ("SETUP_ACTIVE_POKEMON", 1), ("SETUP_BENCH_POKEMON", 2),
        ("SWITCH", 3), ("TO_ACTIVE", 4), ("TO_BENCH", 5), ("TO_FIELD", 6),
        ("TO_HAND", 7), ("DISCARD", 8), ("TO_DECK", 9), ("TO_DECK_BOTTOM", 10),
        ("TO_PRIZE", 11), ("NOT_MOVE", 12), ("DAMAGE_COUNTER", 13),
        ("DAMAGE_COUNTER_ANY", 14), ("DAMAGE", 15), ("REMOVE_DAMAGE_COUNTER", 16),
        ("HEAL", 17), ("EVOLVES_FROM", 18), ("EVOLVES_TO", 19), ("DEVOLVE", 20),
        ("ATTACH_FROM", 21), ("ATTACH_TO", 22), ("DETACH_FROM", 23),
        ("LOOK", 24), ("EFFECT_TARGET", 25), ("DISCARD_ENERGY_CARD", 26),
        ("DISCARD_TOOL_CARD", 27), ("SWITCH_ENERGY_CARD", 28),
        ("DISCARD_CARD_OR_ATTACHED_CARD", 29), ("DISCARD_ENERGY", 30),
        ("TO_HAND_ENERGY", 31), ("TO_DECK_ENERGY", 32), ("SWITCH_ENERGY", 33),
        ("SKILL_ORDER", 34), ("ATTACK", 35), ("DISABLE_ATTACK", 36),
        ("EVOLVE", 37), ("DRAW_COUNT", 38), ("DAMAGE_COUNTER_COUNT", 39),
        ("REMOVE_DAMAGE_COUNTER_COUNT", 40), ("IS_FIRST", 41),
        ("MULLIGAN", 42), ("ACTIVATE", 43), ("FIRST_EFFECT", 44),
        ("MORE_DEVOLVE", 45), ("COIN_HEAD", 46),
        ("AFFECT_SPECIAL_CONDITION", 47), ("RECOVER_SPECIAL_CONDITION", 48),
    )

    def to_observation_class(obs_dict):
        raise RuntimeError("cg module not available")

    def all_attack():
        return []

    def all_card_data():
        return []


# ---------------------------------------------------------------------------
# Attack info cache
# ---------------------------------------------------------------------------
_attack_cache: dict = {}
_card_data_cache: dict = {}


def _load_attack_info():
    """Load and cache attack information from the engine."""
    global _attack_cache
    if _attack_cache:
        return _attack_cache
    try:
        attacks = all_attack()
        for atk in attacks:
            _attack_cache[atk.attackId] = {
                "name": atk.name,
                "damage": atk.damage,
                "text": atk.text,
                "energies": atk.energies,
            }
    except Exception:
        pass
    return _attack_cache


def _load_card_data():
    """Load and cache card data from the engine."""
    global _card_data_cache
    if _card_data_cache:
        return _card_data_cache
    try:
        cards = all_card_data()
        for card in cards:
            _card_data_cache[card.cardId] = {
                "name": card.name,
                "cardType": card.cardType,
                "hp": card.hp,
                "energyType": card.energyType,
                "retreatCost": card.retreatCost,
                "weakness": card.weakness,
                "resistance": card.resistance,
                "attacks": card.attacks,
                "basic": card.basic,
                "stage1": card.stage1,
                "stage2": card.stage2,
                "ex": card.ex,
                "megaEx": card.megaEx,
            }
    except Exception:
        pass
    return _card_data_cache


# ---------------------------------------------------------------------------
# Deck loading
# ---------------------------------------------------------------------------
def read_deck_csv() -> list[int]:
    """Load the 60 card IDs from the submission directory."""
    candidates = [
        Path("/kaggle_simulations/agent/deck.csv"),
        Path("deck.csv"),
    ]
    module_file = globals().get("__file__")
    if module_file:
        candidates.insert(0, Path(module_file).resolve().with_name("deck.csv"))
    path = next((c for c in candidates if c.exists()), None)
    if path is None:
        raise FileNotFoundError("Could not locate deck.csv")
    deck = [int(line.strip()) for line in path.read_text().splitlines() if line.strip()]
    if len(deck) != 60:
        raise ValueError(f"Expected 60 cards, found {len(deck)}")
    return deck


# ---------------------------------------------------------------------------
# Game state helpers
# ---------------------------------------------------------------------------
def _get_my_state(obs) -> object:
    """Get our player's state from the observation."""
    if obs.current is None:
        return None
    my_idx = obs.current.yourIndex
    return obs.current.players[my_idx]


def _get_opp_state(obs) -> object:
    """Get opponent's player state."""
    if obs.current is None:
        return None
    my_idx = obs.current.yourIndex
    opp_idx = 1 - my_idx
    return obs.current.players[opp_idx]


def _get_active(player_state) -> object:
    """Get the active Pokemon (or None)."""
    if player_state is None:
        return None
    active_list = player_state.active
    if not active_list:
        return None
    return active_list[0]


def _get_bench(player_state) -> list:
    """Get bench Pokemon list."""
    if player_state is None:
        return []
    return list(player_state.bench) if player_state.bench else []


def _get_hand(player_state) -> list:
    """Get hand cards list."""
    if player_state is None:
        return []
    return list(player_state.hand) if player_state.hand else []


def _pokemon_hp_ratio(pokemon) -> float:
    """Get HP ratio (0.0 to 1.0)."""
    if pokemon is None:
        return 0.0
    try:
        max_hp = int(pokemon.maxHp)
        if max_hp <= 0:
            return 0.0
        return int(pokemon.hp) / max_hp
    except (TypeError, ValueError, AttributeError):
        return 0.5


def _pokemon_energy_count(pokemon) -> int:
    """Count energy attached to a Pokemon."""
    if pokemon is None:
        return 0
    try:
        return len(pokemon.energies)
    except (TypeError, AttributeError):
        return 0


def _pokemon_id(pokemon) -> int:
    """Get the card ID of a Pokemon."""
    if pokemon is None:
        return -1
    try:
        return int(pokemon.id)
    except (TypeError, AttributeError):
        return -1


def _card_id(card) -> int:
    """Get the card ID from a Card object."""
    if card is None:
        return -1
    try:
        return int(card.id)
    except (TypeError, AttributeError):
        return -1


def _is_mega_lucario(pokemon) -> bool:
    """Check if a Pokemon is Mega Lucario ex."""
    return _pokemon_id(pokemon) == MEGA_LUCARIO_ID


def _is_riolu(pokemon) -> bool:
    """Check if a Pokemon is Riolu."""
    return _pokemon_id(pokemon) == RIOLU_ID


def _has_energy_in_discard(player_state) -> bool:
    """Check if there's Fighting energy in the discard pile."""
    if player_state is None or not player_state.discard:
        return False
    for card in player_state.discard:
        if _card_id(card) == FIGHTING_ENERGY_ID:
            return True
    return False


def _count_bench_pokemon(player_state) -> int:
    """Count Pokemon on bench."""
    bench = _get_bench(player_state)
    return len([p for p in bench if p is not None])


def _bench_has_space(player_state) -> bool:
    """Check if bench has space for more Pokemon."""
    if player_state is None:
        return False
    return _count_bench_pokemon(player_state) < int(player_state.benchMax)


# ---------------------------------------------------------------------------
# Option evaluation for MAIN selection
# ---------------------------------------------------------------------------
def _score_play_option(option, obs, my_state) -> float:
    """Score a PLAY option based on which card is being played."""
    hand = _get_hand(my_state)
    hand_idx = int(getattr(option, "index", -1))
    if hand_idx < 0 or hand_idx >= len(hand):
        return 30.0
    card_id = _card_id(hand[hand_idx])

    my_active = _get_active(my_state)
    my_bench = _get_bench(my_state)
    bench_space = _bench_has_space(my_state)
    has_mega_in_hand = any(_card_id(c) == MEGA_LUCARIO_ID for c in hand)
    has_riolu_in_play = any(
        _is_riolu(p) for p in [my_active] + my_bench if p is not None
    )
    has_mega_in_play = any(
        _is_mega_lucario(p) for p in [my_active] + my_bench if p is not None
    )
    hand_count = len(hand)

    if card_id == SALVATORE_ID:
        # Instant evolve - highest priority if we have Riolu in play
        if has_riolu_in_play:
            return 98.0
        return 20.0

    if card_id == MEGA_SIGNAL_ID:
        # Search for Mega Lucario ex
        if not has_mega_in_hand:
            return 92.0
        return 15.0

    if card_id == POFFIN_ID:
        # Search for Basic Pokemon (Riolu, 70 HP)
        if bench_space:
            return 88.0
        return 10.0

    if card_id == CYRANO_ID:
        # Search for up to 3 Pokemon ex
        if not has_mega_in_hand:
            return 85.0
        return 20.0

    if card_id == LILLIE_ID:
        # Draw 6-8 cards - good when hand is small
        if hand_count <= 3:
            return 82.0
        elif hand_count <= 5:
            return 65.0
        return 30.0

    if card_id == WAITRESS_ID:
        # Energy from deck - good early game
        my_active_pokemon = my_active
        if my_active_pokemon is not None and _pokemon_energy_count(my_active_pokemon) < 2:
            return 78.0
        return 50.0

    if card_id == CRISPIN_ID:
        # Energy search + attach
        my_active_pokemon = my_active
        if my_active_pokemon is not None and _pokemon_energy_count(my_active_pokemon) < 2:
            return 75.0
        return 45.0

    if card_id == ULTRA_BALL_ID:
        # Search any Pokemon, discard 2
        if not has_mega_in_hand and not has_riolu_in_play:
            return 70.0
        if not has_mega_in_hand:
            return 55.0
        return 15.0

    if card_id == TARRAGON_ID:
        # Recovery from discard (Fighting Pokemon + energy)
        if _has_energy_in_discard(my_state):
            return 60.0
        return 25.0

    if card_id == SWITCH_ID:
        # Switch active with bench
        if my_active is not None and _pokemon_hp_ratio(my_active) < 0.3:
            # Active is low HP - check if bench has a better option
            bench_pokemon = [p for p in my_bench if p is not None]
            if any(_is_mega_lucario(p) and _pokemon_energy_count(p) > 0 for p in bench_pokemon):
                return 72.0
        return 8.0

    if card_id == BOSS_ORDERS_ID:
        # Gust opponent's benched Pokemon
        opp_state = _get_opp_state(obs)
        opp_active = _get_active(opp_state)
        opp_bench = _get_bench(opp_state)
        # Use if opponent has a weak benched Pokemon we can KO
        if opp_active and _pokemon_hp_ratio(opp_active) > 0.8:
            # Active is healthy, maybe gust something weak
            for p in opp_bench:
                if p is not None and _pokemon_hp_ratio(p) < 0.3:
                    return 55.0
        return 12.0

    if card_id == ENERGY_RETRIEVAL_ID:
        if _has_energy_in_discard(my_state):
            return 50.0
        return 10.0

    if card_id == MAXIMUM_BELT_ID:
        # Attach tool to increase damage
        if has_mega_in_play:
            return 58.0
        return 15.0

    if card_id == POWERGLASS_ID:
        # Attach tool for energy from discard
        if has_mega_in_play:
            return 52.0
        return 12.0

    # Unknown card - low priority
    return 25.0


def _score_evolve_option(option, obs, my_state) -> float:
    """Score an EVOLVE option."""
    # EVOLVE options have inPlayArea/inPlayIndex for the target Pokemon
    # and area/index for the evolution card in hand
    in_play_area = getattr(option, "inPlayArea", None)
    in_play_index = getattr(option, "inPlayIndex", -1)

    # Determine which Pokemon is being evolved
    my_active = _get_active(my_state)
    my_bench = _get_bench(my_state)

    target_pokemon = None
    if in_play_area == 4:  # ACTIVE
        target_pokemon = my_active
    elif in_play_area == 5:  # BENCH
        if 0 <= in_play_index < len(my_bench):
            target_pokemon = my_bench[in_play_index]

    if target_pokemon is None:
        return 50.0

    # Evolving Riolu to Mega Lucario ex is very high priority
    if _is_riolu(target_pokemon):
        return 96.0

    return 40.0


def _score_attach_option(option, obs, my_state) -> float:
    """Score an ATTACH option."""
    in_play_area = getattr(option, "inPlayArea", None)
    in_play_index = getattr(option, "inPlayIndex", -1)

    my_active = _get_active(my_state)
    my_bench = _get_bench(my_state)

    target_pokemon = None
    if in_play_area == 4:  # ACTIVE
        target_pokemon = my_active
    elif in_play_area == 5:  # BENCH
        if 0 <= in_play_index < len(my_bench):
            target_pokemon = my_bench[in_play_index]

    if target_pokemon is None:
        return 30.0

    target_energy = _pokemon_energy_count(target_pokemon)

    # Prioritize attaching to active Mega Lucario ex
    if _is_mega_lucario(target_pokemon) and in_play_area == 4:
        if target_energy < 2:
            return 90.0
        return 40.0

    # Attaching to active Riolu (before evolution)
    if _is_riolu(target_pokemon) and in_play_area == 4:
        return 80.0

    # Attaching to benched Mega Lucario ex
    if _is_mega_lucario(target_pokemon):
        if target_energy < 2:
            return 65.0
        return 30.0

    # Attaching to benched Riolu
    if _is_riolu(target_pokemon):
        return 50.0

    return 35.0


def _score_attack_option(option, obs, my_state) -> float:
    """Score an ATTACK option based on damage and game state."""
    attack_id = getattr(option, "attackId", -1)
    attack_info = _load_attack_info()
    atk = attack_info.get(attack_id, {})
    atk_name = atk.get("name", "")
    atk_damage = atk.get("damage", 0)

    opp_state = _get_opp_state(obs)
    opp_active = _get_active(opp_state)

    # Base score on damage
    if atk_damage > 0:
        score = min(60.0, atk_damage / 5.0)
    else:
        score = 30.0

    # Bonus if can KO opponent's active
    if opp_active is not None:
        try:
            opp_hp = int(opp_active.hp)
            if atk_damage >= opp_hp:
                score += 40.0  # KO bonus
        except (TypeError, ValueError, AttributeError):
            pass

    # Aura Jab is preferred for energy acceleration
    if AURA_JAB_NAME in atk_name:
        if _has_energy_in_discard(my_state) and _count_bench_pokemon(my_state) > 0:
            score += 15.0  # Energy acceleration bonus

    # Mega Brave is high damage but can't use next turn
    if MEGA_BRAVE_NAME in atk_name:
        # Prefer if it can KO or if opponent has high HP
        if opp_active is not None:
            try:
                opp_hp = int(opp_active.hp)
                if atk_damage >= opp_hp:
                    score += 10.0  # KO is always good
                elif opp_hp > 130:
                    score += 5.0  # Need big damage
            except (TypeError, ValueError, AttributeError):
                pass

    # Opponent aggression adjustment — if opponent is aggressive, prefer KOs
    aggression = _get_opponent_aggression()
    if aggression > 0.6 and opp_active is not None:
        try:
            opp_hp = int(opp_active.hp)
            if atk_damage >= opp_hp:
                score += 10.0  # Extra KO bonus vs aggressive opponents
        except (TypeError, ValueError, AttributeError):
            pass

    # If opponent is passive, prefer energy ramp (Aura Jab) over big damage
    if aggression < 0.3 and AURA_JAB_NAME in atk_name:
        score += 8.0  # Ramp more vs passive opponents

    return min(score, 95.0)


def _score_retreat_option(option, obs, my_state) -> float:
    """Score a RETREAT option."""
    my_active = _get_active(my_state)
    if my_active is None:
        return 5.0

    hp_ratio = _pokemon_hp_ratio(my_active)

    # Retreat if active is low HP and bench has a ready attacker
    if hp_ratio < 0.25:
        my_bench = _get_bench(my_state)
        for p in my_bench:
            if p is not None and _is_mega_lucario(p) and _pokemon_energy_count(p) > 0:
                return 78.0
        # Any benched Pokemon with energy
        for p in my_bench:
            if p is not None and _pokemon_energy_count(p) > 0:
                return 55.0

    # Retreat if active is Riolu and bench has Mega Lucario ex
    if _is_riolu(my_active):
        my_bench = _get_bench(my_state)
        for p in my_bench:
            if p is not None and _is_mega_lucario(p) and _pokemon_energy_count(p) > 0:
                return 70.0

    return 8.0


def _score_ability_option(option, obs, my_state) -> float:
    """Score an ABILITY option."""
    # Abilities are generally useful
    return 55.0


def _score_discard_option(option, obs, my_state) -> float:
    """Score a DISCARD option (from play, not from hand)."""
    return 20.0


def _score_main_option(option, obs, my_state) -> float:
    """Score any MAIN option based on its type."""
    opt_type = getattr(option, "type", None)

    if opt_type == OptionType.EVOLVE:
        return _score_evolve_option(option, obs, my_state)
    elif opt_type == OptionType.PLAY:
        return _score_play_option(option, obs, my_state)
    elif opt_type == OptionType.ATTACH:
        return _score_attach_option(option, obs, my_state)
    elif opt_type == OptionType.ATTACK:
        return _score_attack_option(option, obs, my_state)
    elif opt_type == OptionType.ABILITY:
        return _score_ability_option(option, obs, my_state)
    elif opt_type == OptionType.RETREAT:
        return _score_retreat_option(option, obs, my_state)
    elif opt_type == OptionType.DISCARD:
        return _score_discard_option(option, obs, my_state)
    elif opt_type == OptionType.END:
        return 3.0
    else:
        return 20.0


# ---------------------------------------------------------------------------
# Selection handlers for different contexts
# ---------------------------------------------------------------------------
def _handle_main_selection(obs) -> list[int]:
    """Handle MAIN selection - choose the best action."""
    select = obs.select
    options = list(select.option)
    if not options:
        return []

    my_state = _get_my_state(obs)

    # Score each option and pick the best
    best_idx = 0
    best_score = -1.0
    for i, opt in enumerate(options):
        score = _score_main_option(opt, obs, my_state)
        if score > best_score:
            best_score = score
            best_idx = i

    # Determine how many to select
    required = max(0, int(select.minCount))
    requested = max(required, min(1, int(select.maxCount)))
    count = min(requested, len(options))

    if count == 1:
        return [best_idx]
    else:
        # Select multiple - sort by score and take top N
        scored = [(i, _score_main_option(opt, obs, my_state)) for i, opt in enumerate(options)]
        scored.sort(key=lambda x: -x[1])
        return [idx for idx, _ in scored[:count]]


def _handle_attack_selection(obs) -> list[int]:
    """Handle ATTACK selection - choose the best attack."""
    select = obs.select
    options = list(select.option)
    if not options:
        return []

    my_state = _get_my_state(obs)
    attack_info = _load_attack_info()
    opp_state = _get_opp_state(obs)
    opp_active = _get_active(opp_state)
    opp_hp = 0
    if opp_active is not None:
        try:
            opp_hp = int(opp_active.hp)
        except (TypeError, ValueError, AttributeError):
            pass

    has_energy_discard = _has_energy_in_discard(my_state)
    bench_count = _count_bench_pokemon(my_state)

    best_idx = 0
    best_score = -1.0

    for i, opt in enumerate(options):
        attack_id = getattr(opt, "attackId", -1)
        atk = attack_info.get(attack_id, {})
        atk_name = atk.get("name", "")
        atk_damage = atk.get("damage", 0)

        score = float(atk_damage) if atk_damage > 0 else 30.0

        # KO bonus
        if opp_hp > 0 and atk_damage >= opp_hp:
            score += 100.0

        # Aura Jab: prefer for energy acceleration
        if AURA_JAB_NAME in atk_name:
            if has_energy_discard and bench_count > 0:
                score += 30.0
            # If can't KO with Aura Jab but could with Mega Brave, prefer Mega Brave
            if opp_hp > atk_damage:
                score -= 20.0

        # Mega Brave: prefer for high damage
        if MEGA_BRAVE_NAME in atk_name:
            if opp_hp > 0 and atk_damage >= opp_hp:
                score += 20.0  # KO with Mega Brave is great
            elif opp_hp > 130:
                score += 10.0  # Need the big damage

        if score > best_score:
            best_score = score
            best_idx = i

    return [best_idx]


def _handle_card_selection(obs) -> list[int]:
    """Handle CARD selection based on context."""
    select = obs.select
    options = list(select.option)
    if not options:
        return []

    context = getattr(select, "context", None)
    my_state = _get_my_state(obs)

    # Setup: choose active Pokemon (prefer Riolu)
    if context == SelectContext.SETUP_ACTIVE_POKEMON:
        for i, opt in enumerate(options):
            card_id = getattr(opt, "cardId", -1)
            if card_id == RIOLU_ID:
                return [i]
        # Fallback: first option
        return [0]

    # Setup: choose bench Pokemon (prefer Riolu)
    if context == SelectContext.SETUP_BENCH_POKEMON:
        # Select all Riolu options, up to maxCount
        riolu_indices = []
        for i, opt in enumerate(options):
            card_id = getattr(opt, "cardId", -1)
            if card_id == RIOLU_ID:
                riolu_indices.append(i)

        if riolu_indices:
            max_count = int(select.maxCount)
            return riolu_indices[:max_count]
        return [0] if options else []

    # Switch: choose benched Mega Lucario ex with most energy
    if context == SelectContext.SWITCH:
        my_bench = _get_bench(my_state)
        best_idx = 0
        best_energy = -1
        for i, opt in enumerate(options):
            in_play_index = getattr(opt, "index", -1)
            if 0 <= in_play_index < len(my_bench):
                p = my_bench[in_play_index]
                if p is not None:
                    energy = _pokemon_energy_count(p)
                    is_mega = _is_mega_lucario(p)
                    # Prefer Mega Lucario ex with energy
                    score = energy + (100 if is_mega else 0)
                    if score > best_energy:
                        best_energy = score
                        best_idx = i
        return [best_idx]

    # Attach energy to a Pokemon
    if context == SelectContext.ATTACH_FROM:
        my_active = _get_active(my_state)
        my_bench = _get_bench(my_state)

        # Prefer active Mega Lucario ex, then active Riolu, then benched Mega Lucario ex
        best_idx = 0
        best_score = -1
        for i, opt in enumerate(options):
            area = getattr(opt, "area", None)
            index = getattr(opt, "index", -1)

            target = None
            if area == 4:  # ACTIVE
                target = my_active
            elif area == 5:  # BENCH
                if 0 <= index < len(my_bench):
                    target = my_bench[index]

            if target is None:
                continue

            score = 10.0
            if _is_mega_lucario(target) and area == 4:
                score = 90.0
            elif _is_riolu(target) and area == 4:
                score = 80.0
            elif _is_mega_lucario(target):
                score = 65.0
            elif _is_riolu(target):
                score = 50.0

            if score > best_score:
                best_score = score
                best_idx = i
        return [best_idx]

    # Evolve: choose Riolu to evolve
    if context == SelectContext.EVOLVES_FROM:
        my_active = _get_active(my_state)
        my_bench = _get_bench(my_state)

        # Prefer active Riolu, then benched Riolu
        for i, opt in enumerate(options):
            area = getattr(opt, "area", None)
            index = getattr(opt, "index", -1)
            target = None
            if area == 4:
                target = my_active
            elif area == 5 and 0 <= index < len(my_bench):
                target = my_bench[index]
            if target is not None and _is_riolu(target):
                return [i]
        return [0]

    # Evolve target: choose Mega Lucario ex
    if context == SelectContext.EVOLVES_TO:
        for i, opt in enumerate(options):
            card_id = getattr(opt, "cardId", -1)
            if card_id == MEGA_LUCARIO_ID:
                return [i]
        return [0]

    # Discard: prefer energy cards, then less useful cards
    if context == SelectContext.DISCARD:
        my_state_local = my_state
        hand = _get_hand(my_state_local)

        # Score each option - prefer to discard energy, then duplicate cards
        best_indices = []
        for i, opt in enumerate(options):
            card_id = getattr(opt, "cardId", -1)
            # Energy is safest to discard (we can retrieve it)
            if card_id == FIGHTING_ENERGY_ID:
                best_indices.append((i, 90))
            elif card_id == RIOLU_ID:
                best_indices.append((i, 50))
            else:
                best_indices.append((i, 30))

        # Sort by score descending and take required count
        best_indices.sort(key=lambda x: -x[1])
        required = max(1, int(select.minCount))
        count = min(required, int(select.maxCount), len(best_indices))
        return [idx for idx, _ in best_indices[:count]]

    # Damage counter: target opponent's active
    if context in (SelectContext.DAMAGE_COUNTER, SelectContext.DAMAGE_COUNTER_ANY,
                   SelectContext.DAMAGE):
        opp_state = _get_opp_state(obs)
        opp_active = _get_active(opp_state)
        opp_bench = _get_bench(opp_state)

        # Prefer to damage opponent's active, or benched Pokemon with low HP
        best_idx = 0
        best_score = -1
        for i, opt in enumerate(options):
            player_idx = getattr(opt, "playerIndex", -1)
            area = getattr(opt, "area", None)
            index = getattr(opt, "index", -1)

            my_idx = obs.current.yourIndex if obs.current else 0

            # Only target opponent
            if player_idx == my_idx:
                continue

            score = 10.0
            if area == 4:  # Active
                score = 80.0
                if opp_active is not None:
                    hp_ratio = _pokemon_hp_ratio(opp_active)
                    if hp_ratio < 0.3:
                        score = 95.0  # Can KO
            elif area == 5:  # Bench
                if 0 <= index < len(opp_bench):
                    p = opp_bench[index]
                    if p is not None:
                        hp_ratio = _pokemon_hp_ratio(p)
                        if hp_ratio < 0.2:
                            score = 85.0  # Can KO benched
                        else:
                            score = 40.0

            if score > best_score:
                best_score = score
                best_idx = i
        return [best_idx]

    # Heal: prefer active Mega Lucario ex
    if context == SelectContext.HEAL:
        my_active = _get_active(my_state)
        for i, opt in enumerate(options):
            area = getattr(opt, "area", None)
            if area == 4 and my_active is not None and _is_mega_lucario(my_active):
                return [i]
        return [0]

    # Remove damage counter: prefer our active
    if context == SelectContext.REMOVE_DAMAGE_COUNTER:
        my_active = _get_active(my_state)
        for i, opt in enumerate(options):
            area = getattr(opt, "area", None)
            if area == 4:
                return [i]
        return [0]

    # To hand: prefer Mega Lucario ex or Riolu
    if context == SelectContext.TO_HAND:
        for i, opt in enumerate(options):
            card_id = getattr(opt, "cardId", -1)
            if card_id == MEGA_LUCARIO_ID:
                return [i]
        for i, opt in enumerate(options):
            card_id = getattr(opt, "cardId", -1)
            if card_id == RIOLU_ID:
                return [i]
        return [0]

    # To bench: prefer Riolu
    if context in (SelectContext.TO_BENCH, SelectContext.TO_FIELD):
        for i, opt in enumerate(options):
            card_id = getattr(opt, "cardId", -1)
            if card_id == RIOLU_ID:
                return [i]
        return [0]

    # To active: prefer Mega Lucario ex with energy
    if context == SelectContext.TO_ACTIVE:
        my_bench = _get_bench(my_state)
        best_idx = 0
        best_score = -1
        for i, opt in enumerate(options):
            index = getattr(opt, "index", -1)
            if 0 <= index < len(my_bench):
                p = my_bench[index]
                if p is not None:
                    score = _pokemon_energy_count(p)
                    if _is_mega_lucario(p):
                        score += 100
                    if score > best_score:
                        best_score = score
                        best_idx = i
        return [best_idx]

    # Effect target: prefer opponent's active
    if context == SelectContext.EFFECT_TARGET:
        opp_state = _get_opp_state(obs)
        for i, opt in enumerate(options):
            player_idx = getattr(opt, "playerIndex", -1)
            my_idx = obs.current.yourIndex if obs.current else 0
            area = getattr(opt, "area", None)
            if player_idx != my_idx and area == 4:
                return [i]
        return [0]

    # Look: first option
    if context == SelectContext.LOOK:
        required = max(0, int(select.minCount))
        count = max(required, min(1, int(select.maxCount)))
        return list(range(min(count, len(options))))

    # Default: take first option(s)
    required = max(0, int(select.minCount))
    requested = max(required, min(1, int(select.maxCount)))
    count = min(requested, len(options))
    return list(range(count))


def _handle_yes_no_selection(obs) -> list[int]:
    """Handle YES_NO selection based on context."""
    select = obs.select
    options = list(select.option)
    if not options:
        return []

    context = getattr(select, "context", None)

    # Find YES and NO options
    yes_idx = None
    no_idx = None
    for i, opt in enumerate(options):
        opt_type = getattr(opt, "type", None)
        if opt_type == OptionType.YES:
            yes_idx = i
        elif opt_type == OptionType.NO:
            no_idx = i

    # MULLIGAN: say NO (we have Basic Pokemon)
    if context == SelectContext.MULLIGAN:
        return [no_idx] if no_idx is not None else [0]

    # IS_FIRST: say YES (go first)
    if context == SelectContext.IS_FIRST:
        return [yes_idx] if yes_idx is not None else [0]

    # ACTIVATE: say YES (activate beneficial effects)
    if context == SelectContext.ACTIVATE:
        return [yes_idx] if yes_idx is not None else [0]

    # FIRST_EFFECT: say YES
    if context == SelectContext.FIRST_EFFECT:
        return [yes_idx] if yes_idx is not None else [0]

    # COIN_HEAD: say YES (heads)
    if context == SelectContext.COIN_HEAD:
        return [yes_idx] if yes_idx is not None else [0]

    # MORE_DEVOLVE: say NO
    if context == SelectContext.MORE_DEVOLVE:
        return [no_idx] if no_idx is not None else [0]

    # Default: say YES
    return [yes_idx] if yes_idx is not None else ([0] if options else [])


def _handle_count_selection(obs) -> list[int]:
    """Handle COUNT selection - choose the best number."""
    select = obs.select
    options = list(select.option)
    if not options:
        return []

    context = getattr(select, "context", None)

    # DRAW_COUNT: draw as many as possible
    if context == SelectContext.DRAW_COUNT:
        # Pick the option with the highest number
        best_idx = 0
        best_num = -1
        for i, opt in enumerate(options):
            num = getattr(opt, "number", 0) or 0
            if num > best_num:
                best_num = num
                best_idx = i
        return [best_idx]

    # DAMAGE_COUNTER_COUNT: place as many as possible
    if context == SelectContext.DAMAGE_COUNTER_COUNT:
        best_idx = 0
        best_num = -1
        for i, opt in enumerate(options):
            num = getattr(opt, "number", 0) or 0
            if num > best_num:
                best_num = num
                best_idx = i
        return [best_idx]

    # REMOVE_DAMAGE_COUNTER_COUNT: remove as many as possible
    if context == SelectContext.REMOVE_DAMAGE_COUNTER_COUNT:
        best_idx = 0
        best_num = -1
        for i, opt in enumerate(options):
            num = getattr(opt, "number", 0) or 0
            if num > best_num:
                best_num = num
                best_idx = i
        return [best_idx]

    # Default: pick the middle option
    return [len(options) // 2]


def _handle_energy_selection(obs) -> list[int]:
    """Handle ENERGY selection - choose energy to detach/discard/return."""
    select = obs.select
    options = list(select.option)
    if not options:
        return []

    context = getattr(select, "context", None)

    # DISCARD_ENERGY: discard from opponent's Pokemon if possible
    if context == SelectContext.DISCARD_ENERGY:
        my_idx = obs.current.yourIndex if obs.current else 0
        best_idx = 0
        best_score = -1
        for i, opt in enumerate(options):
            player_idx = getattr(opt, "playerIndex", -1)
            score = 50.0
            if player_idx != my_idx:
                score = 80.0  # Prefer discarding opponent's energy
            if score > best_score:
                best_score = score
                best_idx = i
        return [best_idx]

    # Default: first option
    required = max(0, int(select.minCount))
    requested = max(required, min(1, int(select.maxCount)))
    count = min(requested, len(options))
    return list(range(count))


def _handle_attached_card_selection(obs) -> list[int]:
    """Handle ATTACHED_CARD selection - choose tool/energy to discard/remove."""
    select = obs.select
    options = list(select.option)
    if not options:
        return []

    context = getattr(select, "context", None)

    # DISCARD_TOOL_CARD: discard opponent's tool
    if context == SelectContext.DISCARD_TOOL_CARD:
        my_idx = obs.current.yourIndex if obs.current else 0
        for i, opt in enumerate(options):
            player_idx = getattr(opt, "playerIndex", -1)
            if player_idx != my_idx:
                return [i]
        return [0]

    # DISCARD_ENERGY_CARD: discard opponent's energy
    if context == SelectContext.DISCARD_ENERGY_CARD:
        my_idx = obs.current.yourIndex if obs.current else 0
        for i, opt in enumerate(options):
            player_idx = getattr(opt, "playerIndex", -1)
            if player_idx != my_idx:
                return [i]
        return [0]

    # Default: first option
    required = max(0, int(select.minCount))
    requested = max(required, min(1, int(select.maxCount)))
    count = min(requested, len(options))
    return list(range(count))


def _handle_skill_selection(obs) -> list[int]:
    """Handle SKILL selection - choose which skill to activate."""
    select = obs.select
    options = list(select.option)
    if not options:
        return []
    # Default: first option
    return [0]


def _handle_special_condition_selection(obs) -> list[int]:
    """Handle SPECIAL_CONDITION selection."""
    select = obs.select
    options = list(select.option)
    if not options:
        return []

    context = getattr(select, "context", None)

    # AFFECT_SPECIAL_CONDITION: choose the most damaging condition
    if context == SelectContext.AFFECT_SPECIAL_CONDITION:
        # Prefer Poison (0), then Burn (1), then Confuse (4), then Sleep (2), then Paralyze (3)
        priority = {0: 5, 1: 4, 4: 3, 2: 2, 3: 1}
        best_idx = 0
        best_score = -1
        for i, opt in enumerate(options):
            sc_type = getattr(opt, "specialConditionType", -1)
            score = priority.get(sc_type, 0)
            if score > best_score:
                best_score = score
                best_idx = i
        return [best_idx]

    # RECOVER_SPECIAL_CONDITION: recover from all conditions
    if context == SelectContext.RECOVER_SPECIAL_CONDITION:
        # Recover from the most debilitating condition first
        priority = {3: 5, 2: 4, 4: 3, 0: 2, 1: 1}  # Paralyze > Sleep > Confuse > Poison > Burn
        best_idx = 0
        best_score = -1
        for i, opt in enumerate(options):
            sc_type = getattr(opt, "specialConditionType", -1)
            score = priority.get(sc_type, 0)
            if score > best_score:
                best_score = score
                best_idx = i
        return [best_idx]

    return [0]


# ---------------------------------------------------------------------------
# Opponent modeling — track opponent patterns across turns
# ---------------------------------------------------------------------------
_opponent_tracker: dict = {
    "turns_observed": 0,
    "opponent_attacks": [],
    "opponent_retreats": 0,
    "opponent_energy_attached": 0,
    "opponent_supporters_played": [],
    "opponent_prizes_taken": 0,
    "last_opp_prize_count": 6,
    "last_opp_active_id": -1,
}


def _update_opponent_tracker(obs) -> None:
    """Track opponent behavior across turns for modeling."""
    opp_state = _get_opp_state(obs)
    if opp_state is None:
        return

    current = obs.current
    if current is None:
        return

    # Track prize count changes
    try:
        opp_prize = len(opp_state.prize) if opp_state.prize else 6
        if opp_prize < _opponent_tracker["last_opp_prize_count"]:
            _opponent_tracker["opponent_prizes_taken"] += (
                _opponent_tracker["last_opp_prize_count"] - opp_prize
            )
        _opponent_tracker["last_opp_prize_count"] = opp_prize
    except (TypeError, AttributeError):
        pass

    # Track active Pokemon changes (retreats)
    opp_active = _get_active(opp_state)
    if opp_active is not None:
        active_id = _pokemon_id(opp_active)
        if (
            _opponent_tracker["last_opp_active_id"] != -1
            and active_id != _opponent_tracker["last_opp_active_id"]
        ):
            _opponent_tracker["opponent_retreats"] += 1
        _opponent_tracker["last_opp_active_id"] = active_id

    _opponent_tracker["turns_observed"] = current.turn


def _get_opponent_aggression() -> float:
    """Estimate opponent aggression level (0.0 = passive, 1.0 = aggressive)."""
    if _opponent_tracker["turns_observed"] == 0:
        return 0.5  # Unknown — assume neutral

    # Aggression = prizes taken per turn + retreat frequency
    prizes_per_turn = (
        _opponent_tracker["opponent_prizes_taken"]
        / max(1, _opponent_tracker["turns_observed"])
    )
    retreat_rate = (
        _opponent_tracker["opponent_retreats"]
        / max(1, _opponent_tracker["turns_observed"])
    )

    aggression = min(1.0, prizes_per_turn * 3.0 + retreat_rate * 0.5)
    return aggression


# ---------------------------------------------------------------------------
# Search API lookahead — simulate future game states
# ---------------------------------------------------------------------------
def _evaluate_board_state(obs) -> float:
    """Evaluate the current board state from our perspective (-100 to +100)."""
    my_state = _get_my_state(obs)
    opp_state = _get_opp_state(obs)
    if my_state is None or opp_state is None:
        return 0.0

    score = 0.0

    # Prize card advantage
    my_prizes = len(my_state.prize) if my_state.prize else 6
    opp_prizes = len(opp_state.prize) if opp_state.prize else 6
    score += (opp_prizes - my_prizes) * 15.0  # Each prize difference = 15 points

    # Active Pokemon HP advantage
    my_active = _get_active(my_state)
    opp_active = _get_active(opp_state)
    if my_active is not None:
        score += _pokemon_hp_ratio(my_active) * 10.0
    if opp_active is not None:
        score -= _pokemon_hp_ratio(opp_active) * 10.0

    # Bench development
    my_bench = _count_bench_pokemon(my_state)
    opp_bench = _count_bench_pokemon(opp_state)
    score += (my_bench - opp_bench) * 5.0

    # Energy development
    my_energy = 0
    if my_active is not None:
        my_energy += _pokemon_energy_count(my_active)
    for p in _get_bench(my_state):
        if p is not None:
            my_energy += _pokemon_energy_count(p)

    opp_energy = 0
    if opp_active is not None:
        opp_energy += _pokemon_energy_count(opp_active)
    for p in _get_bench(opp_state):
        if p is not None:
            opp_energy += _pokemon_energy_count(p)

    score += (my_energy - opp_energy) * 3.0

    # Mega Lucario ex in play bonus
    if my_active is not None and _is_mega_lucario(my_active):
        score += 10.0
    for p in _get_bench(my_state):
        if p is not None and _is_mega_lucario(p):
            score += 5.0

    # Hand size advantage
    my_hand = len(_get_hand(my_state))
    opp_hand = opp_state.handCount if hasattr(opp_state, "handCount") else 0
    score += (my_hand - opp_hand) * 1.0

    return max(-100.0, min(100.0, score))


def _try_search_lookahead(obs, candidate_indices: list[int]) -> list[int]:
    """Use the search API to evaluate candidate actions via 1-ply lookahead.

    If the search API is not available or fails, returns the original candidates.
    """
    if not _SEARCH_AVAILABLE or not candidate_indices:
        return candidate_indices

    # Only use lookahead for MAIN selections with few candidates
    select = obs.select
    select_type = getattr(select, "type", None)
    if select_type != SelectType.MAIN:
        return candidate_indices

    # Limit to top 3 candidates to avoid excessive search
    candidates = candidate_indices[:3]
    if len(candidates) <= 1:
        return candidates

    best_candidate = candidates[0]
    best_score = -float("inf")

    for cand_idx in candidates:
        try:
            search_id = search_begin([cand_idx])
            if search_id is None or search_id < 0:
                continue

            # Step through the simulation
            step_result = search_step(search_id, [cand_idx])
            if step_result is not None:
                # Evaluate the resulting state
                simulated_obs = step_result
                if hasattr(simulated_obs, "current"):
                    board_score = _evaluate_board_state(simulated_obs)
                else:
                    board_score = 0.0

                # Add the original heuristic score as a tiebreaker
                options = list(select.option)
                if cand_idx < len(options):
                    heuristic_score = _score_main_option(options[cand_idx], obs, _get_my_state(obs))
                else:
                    heuristic_score = 0.0

                total_score = board_score + heuristic_score * 0.3

                if total_score > best_score:
                    best_score = total_score
                    best_candidate = cand_idx

            search_end()
            search_release(search_id)
        except Exception:
            # Search API failed — fall back to heuristic
            try:
                search_end()
                search_release(search_id)
            except Exception:
                pass
            continue

    return [best_candidate]


# ---------------------------------------------------------------------------
# Main agent function
# ---------------------------------------------------------------------------
def _choose_indices(obs) -> list[int]:
    """Return the best legal indices for the current selection."""
    select = obs.select
    if select is None:
        return []

    options = list(select.option)
    if not options:
        return []

    select_type = getattr(select, "type", None)
    context = getattr(select, "context", None)

    # Dispatch based on selection type
    if select_type == SelectType.MAIN or context == SelectContext.MAIN:
        return _handle_main_selection(obs)

    if select_type == SelectType.ATTACK or context == SelectContext.ATTACK:
        return _handle_attack_selection(obs)

    if select_type == SelectType.YES_NO:
        return _handle_yes_no_selection(obs)

    if select_type == SelectType.COUNT:
        return _handle_count_selection(obs)

    if select_type == SelectType.ENERGY:
        return _handle_energy_selection(obs)

    if select_type == SelectType.ATTACHED_CARD:
        return _handle_attached_card_selection(obs)

    if select_type == SelectType.SKILL:
        return _handle_skill_selection(obs)

    if select_type == SelectType.SPECIAL_CONDITION:
        return _handle_special_condition_selection(obs)

    if select_type == SelectType.CARD or select_type == SelectType.CARD_OR_ATTACHED_CARD:
        return _handle_card_selection(obs)

    if select_type == SelectType.EVOLVE:
        return _handle_card_selection(obs)

    # Fallback: select first valid option(s)
    required = max(0, int(select.minCount))
    requested = max(required, min(1, int(select.maxCount)))
    count = min(requested, len(options))
    return list(range(count))


def agent(obs_dict: dict) -> list[int]:
    """Return a legal deck or the best action for an observation.

    When called with a non-dict or when select is None, returns the 60-card deck.
    Otherwise, returns a list of option indices for the current selection.

    Enhanced with:
    - Opponent behavior tracking across turns
    - Search API lookahead (1-ply simulation) for MAIN selections
    - Board state evaluation
    """
    # Deck selection phase
    if not isinstance(obs_dict, dict):
        return read_deck_csv()

    # Try to convert to Observation class
    try:
        obs = to_observation_class(obs_dict)
    except Exception:
        return read_deck_csv()

    # If no selection data, return deck
    if obs.select is None:
        return read_deck_csv()

    # Update opponent tracker for modeling
    try:
        _update_opponent_tracker(obs)
    except Exception:
        pass

    # Make a selection
    try:
        result = _choose_indices(obs)
        if result:
            # Try search API lookahead for MAIN selections
            select = obs.select
            select_type = getattr(select, "type", None)
            if select_type == SelectType.MAIN and len(result) == 1:
                result = _try_search_lookahead(obs, result)
            return result
    except Exception:
        pass

    # Ultimate fallback: select first valid option(s)
    try:
        select = obs.select
        options = list(select.option)
        required = max(0, int(select.minCount))
        requested = max(required, min(1, int(select.maxCount)))
        count = min(requested, len(options))
        return list(range(count))
    except Exception:
        return [0]
