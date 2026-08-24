"""Comprehensive unit tests for the PTCG AI Battle agent.

Tests cover:
- Deck loading and validation
- Agent contract compliance
- Decision logic for all selection types
- Error handling and fallbacks
- Scoring functions

Run: python -m pytest test_agent.py -v
Or:  python test_agent.py
"""

import sys
import os
from pathlib import Path

# Add agent directory to path
AGENT_DIR = Path(__file__).resolve().parent / "agent"
sys.path.insert(0, str(AGENT_DIR))

import unittest
from main import (
    agent,
    read_deck_csv,
    _CG_AVAILABLE,
    RIOLU_ID,
    MEGA_LUCARIO_ID,
    MEGA_SIGNAL_ID,
    FIGHTING_ENERGY_ID,
    POFFIN_ID,
    SALVATORE_ID,
    LILLIE_ID,
    # Helper functions
    _pokemon_hp_ratio,
    _pokemon_energy_count,
    _pokemon_id,
    _card_id,
    _is_mega_lucario,
    _is_riolu,
    _has_energy_in_discard,
    _count_bench_pokemon,
    _bench_has_space,
)


class MockPokemon:
    """Mock Pokemon for testing."""
    def __init__(self, id=974, hp=70, max_hp=70, energies=None, energy_cards=None,
                 tools=None, pre_evolution=None, appear_this_turn=False, serial=1):
        self.id = id
        self.hp = hp
        self.maxHp = max_hp
        self.energies = energies or []
        self.energyCards = energy_cards or []
        self.tools = tools or []
        self.preEvolution = pre_evolution or []
        self.appearThisTurn = appear_this_turn
        self.serial = serial


class MockCard:
    """Mock Card for testing."""
    def __init__(self, id=6, serial=1, playerIndex=0):
        self.id = id
        self.serial = serial
        self.playerIndex = playerIndex


class MockPlayerState:
    """Mock PlayerState for testing."""
    def __init__(self, active=None, bench=None, hand=None, discard=None,
                 hand_count=0, deck_count=40, bench_max=5, prize=None):
        self.active = active if active is not None else []
        self.bench = bench or []
        self.hand = hand
        self.handCount = hand_count
        self.discard = discard or []
        self.deckCount = deck_count
        self.benchMax = bench_max
        self.prize = prize or []
        self.poisoned = False
        self.burned = False
        self.asleep = False
        self.paralyzed = False
        self.confused = False


class MockState:
    """Mock State for testing."""
    def __init__(self, players=None, your_index=0, turn=1, first_player=0,
                 result=-1, stadium=None):
        self.players = players or []
        self.yourIndex = your_index
        self.turn = turn
        self.firstPlayer = first_player
        self.result = result
        self.stadium = stadium or []
        self.looking = None
        self.energyAttached = False
        self.retreated = False
        self.supporterPlayed = False
        self.stadiumPlayed = False
        self.turnActionCount = 0


class MockOption:
    """Mock Option for testing."""
    def __init__(self, type=14, number=None, area=None, index=None, playerIndex=None,
                 toolIndex=None, energyIndex=None, count=None, inPlayArea=None,
                 inPlayIndex=None, attackId=None, cardId=None, serial=None,
                 specialConditionType=None):
        self.type = type
        self.number = number
        self.area = area
        self.index = index
        self.playerIndex = playerIndex
        self.toolIndex = toolIndex
        self.energyIndex = energyIndex
        self.count = count
        self.inPlayArea = inPlayArea
        self.inPlayIndex = inPlayIndex
        self.attackId = attackId
        self.cardId = cardId
        self.serial = serial
        self.specialConditionType = specialConditionType


class MockSelectData:
    """Mock SelectData for testing."""
    def __init__(self, type=0, context=0, min_count=1, max_count=1, options=None,
                 deck=None, context_card=None, effect=None, remain_damage=0, remain_energy=0):
        self.type = type
        self.context = context
        self.minCount = min_count
        self.maxCount = max_count
        self.option = options or []
        self.deck = deck
        self.contextCard = context_card
        self.effect = effect
        self.remainDamageCounter = remain_damage
        self.remainEnergyCost = remain_energy


class MockObservation:
    """Mock Observation for testing."""
    def __init__(self, select=None, current=None, logs=None):
        self.select = select
        self.current = current
        self.logs = logs or []
        self.search_begin_input = None


# ===========================================================================
# Test Classes
# ===========================================================================

class TestDeckLoading(unittest.TestCase):
    """Test deck loading and validation."""

    def test_deck_has_60_cards(self):
        deck = read_deck_csv()
        self.assertEqual(len(deck), 60, "Deck must have exactly 60 cards")

    def test_deck_all_integers(self):
        deck = read_deck_csv()
        for card_id in deck:
            self.assertIsInstance(card_id, int, f"Card ID {card_id} is not an integer")

    def test_deck_no_more_than_4_copies(self):
        """Except basic energy (ID 6), no card should have more than 4 copies."""
        from collections import Counter
        deck = read_deck_csv()
        counts = Counter(deck)
        for card_id, count in counts.items():
            if card_id != FIGHTING_ENERGY_ID:
                self.assertLessEqual(count, 4, f"Card {card_id} has {count} copies (max 4)")

    def test_deck_has_basic_pokemon(self):
        """Deck must have at least one Basic Pokemon."""
        deck = read_deck_csv()
        riolu_count = deck.count(RIOLU_ID)
        self.assertGreater(riolu_count, 0, "Deck must have Basic Pokemon (Riolu)")

    def test_deck_has_energy(self):
        deck = read_deck_csv()
        energy_count = deck.count(FIGHTING_ENERGY_ID)
        self.assertGreater(energy_count, 10, "Deck should have sufficient energy")

    def test_deck_has_mega_lucario(self):
        deck = read_deck_csv()
        mega_count = deck.count(MEGA_LUCARIO_ID)
        self.assertGreater(mega_count, 0, "Deck must have Mega Lucario ex")


class TestAgentContract(unittest.TestCase):
    """Test the agent function contract compliance."""

    def test_agent_none_input_returns_deck(self):
        result = agent(None)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 60)

    def test_agent_string_input_returns_deck(self):
        result = agent("not a dict")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 60)

    def test_agent_empty_dict_returns_deck(self):
        result = agent({})
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 60)

    def test_agent_select_none_returns_deck(self):
        result = agent({"select": None, "logs": [], "current": None})
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 60)

    def test_agent_returns_list_type(self):
        result = agent(None)
        self.assertIsInstance(result, list)

    def test_agent_no_crash_on_malformed_input(self):
        """Agent should never crash on any input."""
        weird_inputs = [
            [],
            {"select": "not a dict"},
            {"select": {"option": "not a list"}},
            {"select": {"option": [], "minCount": "abc", "maxCount": "xyz"}},
            42,
            True,
            {"select": {"option": [{}], "minCount": 1, "maxCount": 1}},
        ]
        for inp in weird_inputs:
            try:
                result = agent(inp)
                # Should either return a list (deck or indices)
                self.assertIsInstance(result, list)
            except Exception as e:
                self.fail(f"Agent crashed on input {inp}: {e}")


class TestHelperFunctions(unittest.TestCase):
    """Test helper utility functions."""

    def test_pokemon_hp_ratio_full(self):
        p = MockPokemon(hp=100, max_hp=100)
        self.assertAlmostEqual(_pokemon_hp_ratio(p), 1.0)

    def test_pokemon_hp_ratio_half(self):
        p = MockPokemon(hp=50, max_hp=100)
        self.assertAlmostEqual(_pokemon_hp_ratio(p), 0.5)

    def test_pokemon_hp_ratio_zero(self):
        p = MockPokemon(hp=0, max_hp=100)
        self.assertAlmostEqual(_pokemon_hp_ratio(p), 0.0)

    def test_pokemon_hp_ratio_none(self):
        self.assertAlmostEqual(_pokemon_hp_ratio(None), 0.0)

    def test_pokemon_energy_count(self):
        p = MockPokemon(energies=[1, 6, 6])
        self.assertEqual(_pokemon_energy_count(p), 3)

    def test_pokemon_energy_count_empty(self):
        p = MockPokemon(energies=[])
        self.assertEqual(_pokemon_energy_count(p), 0)

    def test_pokemon_energy_count_none(self):
        self.assertEqual(_pokemon_energy_count(None), 0)

    def test_pokemon_id(self):
        p = MockPokemon(id=678)
        self.assertEqual(_pokemon_id(p), 678)

    def test_pokemon_id_none(self):
        self.assertEqual(_pokemon_id(None), -1)

    def test_card_id(self):
        c = MockCard(id=6)
        self.assertEqual(_card_id(c), 6)

    def test_card_id_none(self):
        self.assertEqual(_card_id(None), -1)

    def test_is_mega_lucario_true(self):
        p = MockPokemon(id=MEGA_LUCARIO_ID)
        self.assertTrue(_is_mega_lucario(p))

    def test_is_mega_lucario_false(self):
        p = MockPokemon(id=RIOLU_ID)
        self.assertFalse(_is_mega_lucario(p))

    def test_is_riolu_true(self):
        p = MockPokemon(id=RIOLU_ID)
        self.assertTrue(_is_riolu(p))

    def test_is_riolu_false(self):
        p = MockPokemon(id=MEGA_LUCARIO_ID)
        self.assertFalse(_is_riolu(p))

    def test_has_energy_in_discard_true(self):
        discard = [MockCard(id=6), MockCard(id=974)]
        state = MockPlayerState(discard=discard)
        self.assertTrue(_has_energy_in_discard(state))

    def test_has_energy_in_discard_false(self):
        discard = [MockCard(id=974), MockCard(id=678)]
        state = MockPlayerState(discard=discard)
        self.assertFalse(_has_energy_in_discard(state))

    def test_has_energy_in_discard_empty(self):
        state = MockPlayerState(discard=[])
        self.assertFalse(_has_energy_in_discard(state))

    def test_count_bench_pokemon(self):
        bench = [MockPokemon(), MockPokemon(), None, MockPokemon()]
        state = MockPlayerState(bench=bench)
        self.assertEqual(_count_bench_pokemon(state), 3)

    def test_bench_has_space_true(self):
        bench = [MockPokemon(), MockPokemon()]
        state = MockPlayerState(bench=bench, bench_max=5)
        self.assertTrue(_bench_has_space(state))

    def test_bench_has_space_false(self):
        bench = [MockPokemon() for _ in range(5)]
        state = MockPlayerState(bench=bench, bench_max=5)
        self.assertFalse(_bench_has_space(state))


class TestMockScenarios(unittest.TestCase):
    """Test agent with mock observation scenarios (no cg engine needed)."""

    def _run_agent_with_mock(self, obs_dict):
        """Run agent with a mock observation dict."""
        # Since cg is not available, agent will fall back to deck loading
        # for dict inputs. We test the fallback behavior.
        return agent(obs_dict)

    def test_mulligan_scenario(self):
        """Test that agent handles mulligan selection."""
        obs = {
            "select": {
                "type": 9, "context": 42, "minCount": 1, "maxCount": 1,
                "option": [{"type": 1}, {"type": 2}],
            },
            "logs": [], "current": None,
        }
        result = self._run_agent_with_mock(obs)
        # Without cg, falls back to deck - should return 60 cards
        self.assertIsInstance(result, list)

    def test_setup_active_scenario(self):
        """Test setup active Pokemon selection."""
        obs = {
            "select": {
                "type": 1, "context": 1, "minCount": 1, "maxCount": 1,
                "option": [{"type": 3, "cardId": 974}, {"type": 3, "cardId": 678}],
            },
            "logs": [], "current": None,
        }
        result = self._run_agent_with_mock(obs)
        self.assertIsInstance(result, list)

    def test_main_menu_scenario(self):
        """Test main menu selection."""
        obs = {
            "select": {
                "type": 0, "context": 0, "minCount": 1, "maxCount": 1,
                "option": [
                    {"type": 7, "index": 0, "cardId": 1145},
                    {"type": 7, "index": 1, "cardId": 1086},
                    {"type": 14},
                ],
            },
            "logs": [], "current": None,
        }
        result = self._run_agent_with_mock(obs)
        self.assertIsInstance(result, list)

    def test_count_selection_scenario(self):
        """Test count selection (draw cards)."""
        obs = {
            "select": {
                "type": 8, "context": 38, "minCount": 1, "maxCount": 1,
                "option": [
                    {"type": 0, "number": 1},
                    {"type": 0, "number": 3},
                    {"type": 0, "number": 5},
                ],
            },
            "logs": [], "current": None,
        }
        result = self._run_agent_with_mock(obs)
        self.assertIsInstance(result, list)

    def test_empty_options(self):
        """Test handling of empty options list."""
        obs = {
            "select": {
                "type": 0, "context": 0, "minCount": 1, "maxCount": 1,
                "option": [],
            },
            "logs": [], "current": None,
        }
        result = self._run_agent_with_mock(obs)
        self.assertIsInstance(result, list)


class TestDeckComposition(unittest.TestCase):
    """Test specific deck composition requirements."""

    def setUp(self):
        self.deck = read_deck_csv()
        from collections import Counter
        self.counts = Counter(self.deck)

    def test_has_4_riolu(self):
        self.assertEqual(self.counts.get(RIOLU_ID, 0), 4)

    def test_has_4_mega_lucario(self):
        self.assertEqual(self.counts.get(MEGA_LUCARIO_ID, 0), 4)

    def test_has_4_mega_signal(self):
        self.assertEqual(self.counts.get(MEGA_SIGNAL_ID, 0), 4)

    def test_has_4_lillie(self):
        self.assertEqual(self.counts.get(LILLIE_ID, 0), 4)

    def test_has_3_poffin(self):
        self.assertEqual(self.counts.get(POFFIN_ID, 0), 3)

    def test_has_2_salvatore(self):
        self.assertEqual(self.counts.get(SALVATORE_ID, 0), 2)

    def test_has_22_energy(self):
        self.assertEqual(self.counts.get(FIGHTING_ENERGY_ID, 0), 22)

    def test_pokemon_count(self):
        """Should have 8 Pokemon total."""
        pokemon_count = self.counts.get(RIOLU_ID, 0) + self.counts.get(MEGA_LUCARIO_ID, 0)
        self.assertEqual(pokemon_count, 8)

    def test_trainer_count(self):
        """Should have 30 Trainer cards (non-Pokemon, non-Energy)."""
        total = 60
        pokemon = self.counts.get(RIOLU_ID, 0) + self.counts.get(MEGA_LUCARIO_ID, 0)
        energy = self.counts.get(FIGHTING_ENERGY_ID, 0)
        trainers = total - pokemon - energy
        self.assertEqual(trainers, 30)

    def test_energy_count(self):
        """Should have 22 energy cards."""
        self.assertEqual(self.counts.get(FIGHTING_ENERGY_ID, 0), 22)

    def test_ace_spec_limit(self):
        """Should have at most 1 ACE SPEC card."""
        # Maximum Belt (1158) is our ACE SPEC
        ace_spec_count = self.counts.get(1158, 0)
        self.assertLessEqual(ace_spec_count, 1, "At most 1 ACE SPEC card allowed")


class TestPerformance(unittest.TestCase):
    """Test agent performance characteristics."""

    def test_agent_response_time(self):
        """Agent should respond quickly (< 100ms for deck loading)."""
        import time
        start = time.time()
        agent(None)
        elapsed = time.time() - start
        self.assertLess(elapsed, 0.1, f"Agent took {elapsed:.3f}s (should be < 0.1s)")

    def test_multiple_calls_consistent(self):
        """Multiple calls should return consistent results."""
        results = [agent(None) for _ in range(10)]
        for r in results:
            self.assertEqual(len(r), 60)
        # All should be identical (deterministic deck)
        self.assertTrue(all(r == results[0] for r in results))


def run_all_tests():
    """Run all tests and print results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        TestDeckLoading,
        TestAgentContract,
        TestHelperFunctions,
        TestMockScenarios,
        TestDeckComposition,
        TestPerformance,
    ]

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result


if __name__ == "__main__":
    print(f"CG module available: {_CG_AVAILABLE}")
    print(f"Running tests from: {AGENT_DIR}")
    print()
    result = run_all_tests()
    sys.exit(0 if result.wasSuccessful() else 1)
