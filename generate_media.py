"""Generate media gallery images for the Kaggle Strategy Writeup."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# Color palette
FIGHTING_COLOR = "#C03028"
ENERGY_COLOR = "#F08030"
TRAINER_COLOR = "#6890F0"
ACCENT = "#78C850"
DARK = "#2C2C2C"
LIGHT_BG = "#F8F8F8"

plt.rcParams.update({
    "font.size": 12,
    "font.family": "DejaVu Sans",
    "figure.facecolor": "white",
    "axes.facecolor": LIGHT_BG,
})

OUTPUT_DIR = r"C:\Internal\pokemon-tcg-ai-battle-challenge-strategy\media"


# ===========================================================================
# Image 1: Deck Composition Pie Chart
# ===========================================================================
def create_deck_composition():
    fig, ax = plt.subplots(figsize=(10, 7))

    categories = [
        "Basic Fighting Energy (22)",
        "Supporters (14)",
        "Items (7)",
        "Pokemon Tools (2)",
        "Riolu (4)",
        "Mega Lucario ex (4)",
    ]
    sizes = [22, 14, 7, 2, 4, 4]
    colors = [ENERGY_COLOR, TRAINER_COLOR, "#5B9BD5", "#9B59B6", "#F39C12", FIGHTING_COLOR]
    explode = (0.03, 0.03, 0.03, 0.03, 0.05, 0.08)

    wedges, texts, autotexts = ax.pie(
        sizes, explode=explode, labels=categories, colors=colors,
        autopct="%1.1f%%", shadow=True, startangle=90,
        textprops={"fontsize": 11, "fontweight": "bold"},
    )
    for autotext in autotexts:
        autotext.set_color("white")
        autotext.set_fontsize(10)
        autotext.set_fontweight("bold")

    ax.set_title("Deck Composition — Mega Lucario ex (60 Cards)", fontsize=16, fontweight="bold", pad=20)

    # Add summary text
    fig.text(0.5, 0.02, "Pokemon: 8  |  Trainers: 30  |  Energy: 22",
             ha="center", fontsize=13, fontweight="bold", color=DARK)

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/01_deck_composition.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("[OK] 01_deck_composition.png")


# ===========================================================================
# Image 2: Archetype Comparison Bar Chart
# ===========================================================================
def create_archetype_comparison():
    fig, ax = plt.subplots(figsize=(12, 7))

    categories = ["HP", "Cheapest Attack\nDamage", "Big Attack\nDamage", "Retreat Cost"]
    mega_lucario = [340, 130, 270, 2]
    mega_abomasnow = [350, 100, 200, 4]
    mega_starmie = [330, 120, 210, 2]

    x = np.arange(len(categories))
    width = 0.25

    bars1 = ax.bar(x - width, mega_lucario, width, label="Mega Lucario ex", color=FIGHTING_COLOR, edgecolor="white", linewidth=1.5)
    bars2 = ax.bar(x, mega_abomasnow, width, label="Mega Abomasnow ex", color="#4A90D9", edgecolor="white", linewidth=1.5)
    bars3 = ax.bar(x + width, mega_starmie, width, label="Mega Starmie ex", color="#9B59B6", edgecolor="white", linewidth=1.5)

    # Add value labels on bars
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f"{int(height)}",
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 5), textcoords="offset points",
                        ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax.set_xlabel("Metric", fontsize=13, fontweight="bold")
    ax.set_ylabel("Value", fontsize=13, fontweight="bold")
    ax.set_title("Archetype Comparison — Stage 1 Mega Evolution Attackers", fontsize=16, fontweight="bold", pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=11)
    ax.legend(fontsize=11, loc="upper right")
    ax.grid(axis="y", alpha=0.3)

    # Add note about Aura Jab
    ax.annotate("+ Ramp 3 Energy\nto Bench!",
                xy=(1 - width, 130), xytext=(0.5, 180),
                fontsize=10, fontweight="bold", color=FIGHTING_COLOR,
                arrowprops=dict(arrowstyle="->", color=FIGHTING_COLOR, lw=2),
                ha="center")

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/02_archetype_comparison.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("[OK] 02_archetype_comparison.png")


# ===========================================================================
# Image 3: Agent Decision Pipeline Flowchart
# ===========================================================================
def create_decision_pipeline():
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis("off")
    ax.set_title("Agent Decision Pipeline — Context-Aware Scoring Engine", fontsize=16, fontweight="bold", pad=10)

    boxes = [
        (1, 6, 2.5, 1, "Observation\n(dict)", "#E8E8E8", DARK),
        (4, 6, 2.5, 1, "to_observation_class()\n-> Observation", "#D5E8D4", DARK),
        (7, 6, 2.8, 1, "Dispatch by\nSelectType + Context", "#DAE8FC", DARK),
        (10.5, 6, 2.5, 1, "Score Each\nOption (0-100)", "#FFF2CC", DARK),
        (10.5, 3.5, 2.5, 1, "Pick Highest\nScore", "#D5E8D4", DARK),
        (10.5, 1, 2.5, 1, "Return\n[option_indices]", "#E8E8E8", DARK),
    ]

    for x, y, w, h, text, fc, tc in boxes:
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                             facecolor=fc, edgecolor=DARK, linewidth=2)
        ax.add_patch(box)
        ax.text(x + w/2, y + h/2, text, ha="center", va="center",
                fontsize=10, fontweight="bold", color=tc)

    # Arrows between main flow
    arrow_props = dict(arrowstyle="->", color=DARK, lw=2)
    ax.annotate("", xy=(4, 6.5), xytext=(3.5, 6.5), arrowprops=arrow_props)
    ax.annotate("", xy=(7, 6.5), xytext=(6.5, 6.5), arrowprops=arrow_props)
    ax.annotate("", xy=(10.5, 6.5), xytext=(9.8, 6.5), arrowprops=arrow_props)
    ax.annotate("", xy=(11.75, 4.5), xytext=(11.75, 6), arrowprops=arrow_props)
    ax.annotate("", xy=(11.75, 2), xytext=(11.75, 3.5), arrowprops=arrow_props)

    # Selection type branches
    branches = [
        (8.4, 5, 2, 4, "MAIN\nAction", "#FFD6D6", FIGHTING_COLOR),
        (8.4, 3.5, 2, 1, "ATTACK\nChoice", "#D6E5FF", "#4A90D9"),
        (8.4, 2, 2, 1, "CARD\nTarget", "#D6FFD6", ACCENT),
        (8.4, 0.5, 2, 1, "YES_NO /\nCOUNT", "#FFF2D6", "#E69500"),
    ]

    for x, y, w, h, text, fc, tc in branches:
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                             facecolor=fc, edgecolor=tc, linewidth=1.5)
        ax.add_patch(box)
        ax.text(x + w/2, y + h/2, text, ha="center", va="center",
                fontsize=9, fontweight="bold", color=tc)
        ax.annotate("", xy=(x, y + h/2), xytext=(8.4, 5.5), arrowprops=dict(arrowstyle="->", color=tc, lw=1.5))

    # Fallback note
    ax.text(5, 1, "Fallback: First valid option\n(error handling on every path)",
            ha="center", va="center", fontsize=9, style="italic", color="#888888",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#F0F0F0", edgecolor="#CCCCCC"))

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/03_decision_pipeline.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("[OK] 03_decision_pipeline.png")


# ===========================================================================
# Image 4: MAIN Action Scoring Heatmap
# ===========================================================================
def create_scoring_heatmap():
    fig, ax = plt.subplots(figsize=(12, 7))

    actions = ["EVOLVE\n(Riolu->Mega)", "PLAY\n(Salvatore)", "PLAY\n(Mega Signal)",
               "PLAY\n(Poffin)", "PLAY\n(Lillie)", "ATTACH\n(to Active)",
               "ATTACK\n(Aura Jab)", "ATTACK\n(Mega Brave)", "RETREAT\n(Low HP)",
               "ABILITY", "END"]
    scores = [96, 98, 92, 88, 82, 90, 75, 60, 78, 55, 3]

    colors_gradient = []
    for s in scores:
        if s >= 90:
            colors_gradient.append("#2ECC71")  # Green
        elif s >= 70:
            colors_gradient.append("#F1C40F")  # Yellow
        elif s >= 50:
            colors_gradient.append("#E67E22")  # Orange
        else:
            colors_gradient.append("#E74C3C")  # Red

    bars = ax.barh(range(len(actions)), scores, color=colors_gradient, edgecolor="white", linewidth=1.5)

    for i, (bar, score) in enumerate(zip(bars, scores)):
        ax.text(score + 1, i, f"{score}", va="center", fontsize=11, fontweight="bold")

    ax.set_yticks(range(len(actions)))
    ax.set_yticklabels(actions, fontsize=10)
    ax.set_xlabel("Score (0-100)", fontsize=13, fontweight="bold")
    ax.set_title("MAIN Action Scoring — Higher = More Likely Selected", fontsize=16, fontweight="bold", pad=15)
    ax.set_xlim(0, 110)
    ax.grid(axis="x", alpha=0.3)

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor="#2ECC71", label="Critical (90+)"),
        mpatches.Patch(facecolor="#F1C40F", label="High (70-89)"),
        mpatches.Patch(facecolor="#E67E22", label="Medium (50-69)"),
        mpatches.Patch(facecolor="#E74C3C", label="Low (<50)"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=10)

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/04_scoring_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("[OK] 04_scoring_heatmap.png")


# ===========================================================================
# Image 5: Energy Acceleration Strategy Diagram
# ===========================================================================
def create_energy_strategy():
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis("off")
    ax.set_title("Energy Acceleration Strategy — Aura Jab Self-Sustaining Ramp", fontsize=16, fontweight="bold", pad=10)

    # Turn sequence
    turns = [
        (1, 6.5, "Turn 1", "Bench Riolu\n(Poffin)", "#FFF2D6"),
        (3.5, 6.5, "Turn 2", "Evolve -> Mega Lucario ex\n(Salvatore/Mega Signal)", "#D6E5FF"),
        (6, 6.5, "Turn 3", "Attach {F} Energy\n(Manual + Waitress)", "#D6FFD6"),
        (8.5, 6.5, "Turn 4", "Aura Jab!\n130 dmg + Ramp 3 {F}", "#FFD6D6"),
        (11, 6.5, "Turn 5+", "Mega Brave!\n270 dmg (KO)", "#FFD6D6"),
    ]

    for x, y, title, desc, color in turns:
        box = FancyBboxPatch((x, y - 0.8), 2.2, 1.6, boxstyle="round,pad=0.15",
                             facecolor=color, edgecolor=DARK, linewidth=2)
        ax.add_patch(box)
        ax.text(x + 1.1, y + 0.4, title, ha="center", va="center", fontsize=11, fontweight="bold")
        ax.text(x + 1.1, y - 0.3, desc, ha="center", va="center", fontsize=9)

    # Arrows between turns
    for i in range(4):
        x_start = turns[i][0] + 2.2
        x_end = turns[i + 1][0]
        ax.annotate("", xy=(x_end, y), xytext=(x_start, y),
                    arrowprops=dict(arrowstyle="->", color=DARK, lw=2))

    # Ramp cycle diagram (bottom)
    ax.text(7, 4.5, "Self-Sustaining Ramp Cycle", ha="center", fontsize=14, fontweight="bold", color=FIGHTING_COLOR)

    cycle = [
        (2.5, 2.5, "Attack with\nAura Jab"),
        (5.5, 2.5, "Energy goes\nto discard"),
        (8.5, 2.5, "Ramp 3 {F} to\nBenched Pokemon"),
        (11.5, 2.5, "Next attacker\nready!"),
    ]

    for i, (x, y, text) in enumerate(cycle):
        box = FancyBboxPatch((x - 1, y - 0.6), 2, 1.2, boxstyle="round,pad=0.1",
                             facecolor=ENERGY_COLOR, edgecolor="white", linewidth=2, alpha=0.85)
        ax.add_patch(box)
        ax.text(x, y, text, ha="center", va="center", fontsize=9, fontweight="bold", color="white")

    # Circular arrows
    for i in range(3):
        ax.annotate("", xy=(cycle[i+1][0] - 1, cycle[i+1][1]), xytext=(cycle[i][0] + 1, cycle[i][1]),
                    arrowprops=dict(arrowstyle="->", color=ENERGY_COLOR, lw=2.5, connectionstyle="arc3,rad=0.2"))

    # Loop back arrow
    ax.annotate("", xy=(cycle[0][0] + 1, cycle[0][1] - 0.7), xytext=(cycle[3][0] - 1, cycle[3][1] - 0.7),
                arrowprops=dict(arrowstyle="->", color=ENERGY_COLOR, lw=2.5, connectionstyle="arc3,rad=-0.3", linestyle="dashed"))
    ax.text(7, 0.8, "Repeat cycle", ha="center", fontsize=10, fontweight="bold", color=ENERGY_COLOR, style="italic")

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/05_energy_strategy.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("[OK] 05_energy_strategy.png")


# ===========================================================================
# Image 6: Matchup Coverage Table
# ===========================================================================
def create_matchup_table():
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.axis("off")
    ax.set_title("Matchup Coverage & Strategy", fontsize=16, fontweight="bold", pad=15)

    columns = ["Opponent Type", "Weakness Risk", "Our Strategy", "Advantage"]
    rows = [
        ["Water (Lightning-weak)", "None", "Trade favorably — no shared weakness", "HIGH"],
        ["Psychic (Fighting-weak)", "Mega Lucario ex weak to Psychic", "340 HP tanking + fast KOs", "MEDIUM"],
        ["Fire (Water-weak)", "None", "Race prizes with energy ramp", "HIGH"],
        ["Mirror (Fighting)", "Mutual weakness", "Faster setup wins — Salvatore edge", "EVEN"],
        ["Darkness", "None", "Out-damage with Aura Jab ramp", "HIGH"],
        ["Metal", "None", "Consistent prize trading", "HIGH"],
    ]

    cell_colors = []
    for row in rows:
        adv = row[3]
        if adv == "HIGH":
            cell_colors.append(["#D6FFD6"] * 4)
        elif adv == "MEDIUM":
            cell_colors.append(["#FFF2D6"] * 4)
        elif adv == "EVEN":
            cell_colors.append(["#FFD6D6"] * 4)
        else:
            cell_colors.append(["#F0F0F0"] * 4)

    table = ax.table(cellText=rows, colLabels=columns, cellColours=cell_colors,
                     colWidths=[0.22, 0.25, 0.33, 0.12], loc="center",
                     cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 2)

    # Style header
    for j in range(len(columns)):
        table[0, j].set_facecolor(TRAINER_COLOR)
        table[0, j].set_text_props(color="white", fontweight="bold", fontsize=12)

    # Style advantage column
    for i in range(1, len(rows) + 1):
        table[i, 3].set_text_props(fontweight="bold", fontsize=12)

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/06_matchup_table.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("[OK] 06_matchup_table.png")


# ===========================================================================
# Image 7: Hypothesis Testing Summary
# ===========================================================================
def create_hypothesis_summary():
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.axis("off")
    ax.set_title("Hypotheses Tested — Results Summary", fontsize=16, fontweight="bold", pad=15)

    hypotheses = [
        ("H1", "Energy Acceleration\n> Raw Damage", "CONFIRMED", "#2ECC71",
         "Aura Jab ramp reduces setup gap\nfrom 2-3 turns to 0-1 turns"),
        ("H2", "Context-Aware Scoring\n> Fixed Priority", "CONFIRMED", "#2ECC71",
         "Avoids wasted supporters,\nbad attack timing, poor retreats"),
        ("H3", "Salvatore Enables\nFaster Setup", "CONFIRMED", "#2ECC71",
         "Same-turn evolution skips\nthe 1-turn wait entirely"),
        ("H4", "22 Energy Is\nOptimal Count", "CONFIRMED", "#2ECC71",
         "16 = whiff attachments\n28 = dead draws\n22 = sweet spot"),
    ]

    for i, (hid, title, result, color, detail) in enumerate(hypotheses):
        y = 5.5 - i * 1.4

        # H label
        box = FancyBboxPatch((0.5, y - 0.4), 1.2, 0.8, boxstyle="round,pad=0.1",
                             facecolor=color, edgecolor="white", linewidth=2)
        ax.add_patch(box)
        ax.text(1.1, y, hid, ha="center", va="center", fontsize=14, fontweight="bold", color="white")

        # Title
        ax.text(2.2, y + 0.15, title, ha="left", va="center", fontsize=11, fontweight="bold")

        # Detail
        ax.text(2.2, y - 0.25, detail, ha="left", va="center", fontsize=9, color="#555555")

        # Result badge
        badge = FancyBboxPatch((9.5, y - 0.3), 2, 0.6, boxstyle="round,pad=0.1",
                               facecolor=color, edgecolor="white", linewidth=2)
        ax.add_patch(badge)
        ax.text(10.5, y, result, ha="center", va="center", fontsize=10, fontweight="bold", color="white")

    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7)

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/07_hypothesis_summary.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("[OK] 07_hypothesis_summary.png")


# ===========================================================================
# Run all
# ===========================================================================
if __name__ == "__main__":
    create_deck_composition()
    create_archetype_comparison()
    create_decision_pipeline()
    create_scoring_heatmap()
    create_energy_strategy()
    create_matchup_table()
    create_hypothesis_summary()
    print("\n=== All 7 images generated ===")
