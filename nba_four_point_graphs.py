"""Charts for the four-point line simulation.

1. four_point_breakeven.png - each player's 4P% vs their adjusted 3P%.
   The dashed line is the break-even point (4P% = 0.75 x Adj 3P%):
   players above it score more per shot from 30+ ft, players below it score less.
2. four_point_edge.png - points per shot gained or lost on a 4-point attempt
   compared with that player's 3-point attempt, ranked.
"""
import matplotlib.pyplot as plt
import numpy as np

from nba_four_point_datasets import MIN_4PA, career

HELPS = "#2a78d6"   # blue
HURTS = "#eb6834"   # orange
FEW = "#b9b8b3"     # gray: too few attempts to judge
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e6e5e0"
SURFACE = "#fcfcfb"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK_2,
    "xtick.color": INK_2, "ytick.color": INK_2,
    "font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
})


def pct(ax_axis):
    ax_axis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))


# ---------- 1. Break-even scatter ----------
d = career[career["4PA"] > 0]
fig, ax = plt.subplots(figsize=(9, 6.5))
ax.grid(color=GRID, linewidth=0.8)
ax.set_axisbelow(True)

x = np.linspace(d["Adj 3P%"].min() - 0.01, d["Adj 3P%"].max() + 0.01, 50)
ax.plot(x, 0.75 * x, ls="--", lw=1.5, color=INK_2)
ax.text(x[-1], 0.75 * x[-1], "  break-even\n  4P% = 0.75 × 3P%", color=INK_2, va="center", fontsize=9)

for verdict, color in [("Too few 4PA", FEW), ("Hurts", HURTS), ("Helps", HELPS)]:
    g = d[d["4PT Verdict"] == verdict]
    label = f"Too few attempts (<{MIN_4PA} 4PA)" if verdict == "Too few 4PA" else verdict
    ax.scatter(g["Adj 3P%"], g["4P%"], s=12 + g["4PA"] * 0.6, color=color,
               edgecolor=SURFACE, linewidth=1.5, alpha=0.9, label=label, zorder=3)

# Label the qualifying players furthest from the line, plus the highest-volume ones
q = d[d["4PA"] >= MIN_4PA]
to_label = set(q.nlargest(5, "4P% vs Break-even")["Player"]) \
    | set(q.nsmallest(5, "4P% vs Break-even")["Player"]) \
    | set(q.nlargest(4, "4PA")["Player"])
left = {"Austin Reaves"}  # label on the left to avoid overlapping neighbours
for _, r in q[q["Player"].isin(to_label)].iterrows():
    on_left = r["Player"] in left
    ax.annotate(r["Player"], (r["Adj 3P%"], r["4P%"]), xytext=(-6, -10) if on_left else (5, 4),
                ha="right" if on_left else "left",
                textcoords="offset points", fontsize=8, color=INK)

pct(ax.xaxis)
pct(ax.yaxis)
ax.set_xlabel("Adjusted 3P% (3-pointers inside 30 ft)")
ax.set_ylabel("4P% (shots from 30+ ft)")
ax.set_title("Would a 4-point line help these shooters?\n"
             "Above the line, a 30+ ft shot is worth more than their 3-pointer. Dot size = 4PA (2021-22 to 2025-26).",
             loc="left", fontsize=11, color=INK)
leg = ax.legend(loc="upper left", frameon=False, markerscale=0.7)
for h in leg.legend_handles:
    h.set_sizes([40])
fig.tight_layout()
fig.savefig("four_point_breakeven.png", dpi=150)

# ---------- 2. Ranked edge bars ----------
q = career[career["4PA"] >= MIN_4PA].sort_values("4PT Edge (pts/shot)")
fig, ax = plt.subplots(figsize=(8, 0.26 * len(q) + 1.4))
colors = [HELPS if v > 0 else HURTS for v in q["4PT Edge (pts/shot)"]]
ax.barh(q["Player"], q["4PT Edge (pts/shot)"], color=colors, height=0.7)
ax.axvline(0, color=INK_2, lw=1)
ax.grid(axis="x", color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
ax.tick_params(axis="y", length=0, labelsize=8, labelcolor=INK)
ax.set_ylim(-0.6, len(q) - 0.4)
ax.set_xlabel("Points per shot: 4-point attempt minus 3-point attempt")
ax.set_title(f"4-point edge by player (min {MIN_4PA} attempts from 30+ ft)\n"
             "Blue = helps, orange = hurts", loc="left", fontsize=11, color=INK)
fig.tight_layout()
fig.savefig("four_point_edge.png", dpi=150)

print("Saved four_point_breakeven.png and four_point_edge.png")
