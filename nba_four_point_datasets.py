"""Four-point line simulation.

Treat every 3-point attempt from 30+ ft as a hypothetical 4-point attempt.
For each player we split their current 3PA/3PM into:
  * 4-point range  (30+ ft)
  * new 3-point range (everything inside 30 ft that is currently a three)
and recompute shooting percentages and points per shot.

Source: dataset2_top50_3pm_summary.csv (top 50 3PM per season, 2021-22 to 2025-26).
Its distance bins (22-24, 25-27, 28-29, 30+) sum exactly to 3PM/3PA; heaves are
tracked separately and are not part of those totals.
"""
import pandas as pd

FOUR_PT_DISTANCE = 30  # ft

# Minimum 4-point attempts before a 4P% (and a helps/hurts verdict) is considered meaningful
MIN_4PA = 25

summary = pd.read_csv("dataset2_top50_3pm_summary.csv")


def add_four_point_columns(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()

    # Shots in the new 4-point range (30+ ft)
    d["4PM"] = d["30+ ft 3PM"]
    d["4PA"] = d["30+ ft 3PA"]
    d["4P Misses"] = d["4PA"] - d["4PM"]
    d["4P%"] = (d["4PM"] / d["4PA"]).where(d["4PA"] > 0)
    d["4PA Share"] = d["4PA"] / d["3PA"]  # fraction of current threes that become fours

    # Remaining 3-point range once 4-point shots are removed
    d["Adj 3PM"] = d["3PM"] - d["4PM"]
    d["Adj 3PA"] = d["3PA"] - d["4PA"]
    d["3P%"] = d["3PM"] / d["3PA"]
    d["Adj 3P%"] = d["Adj 3PM"] / d["Adj 3PA"]
    d["3P% Change"] = d["Adj 3P%"] - d["3P%"]

    # Efficiency: points per shot on all shots beyond the arc
    d["Pts/Shot (current)"] = 3 * d["3PM"] / d["3PA"]
    d["Pts/Shot (with 4PT)"] = (3 * d["Adj 3PM"] + 4 * d["4PM"]) / d["3PA"]
    d["Extra Pts from 4PT"] = d["4PM"]  # each made 30+ footer is worth one extra point
    d["Pts/Shot Change"] = d["Pts/Shot (with 4PT)"] - d["Pts/Shot (current)"]

    # Helps or hurts? Compare what one 4-point attempt is worth with what one
    # (sub-30 ft) 3-point attempt is worth for the same player.
    #   4 * 4P%  >  3 * Adj 3P%   <=>   4P%  >  0.75 * Adj 3P%
    d["Pts per 4PA"] = 4 * d["4P%"]
    d["Pts per Adj 3PA"] = 3 * d["Adj 3P%"]
    d["Break-even 4P%"] = 0.75 * d["Adj 3P%"]
    d["4P% vs Break-even"] = d["4P%"] - d["Break-even 4P%"]
    d["4PT Edge (pts/shot)"] = d["Pts per 4PA"] - d["Pts per Adj 3PA"]
    d["4PT Verdict"] = "Too few 4PA"
    enough = d["4PA"] >= MIN_4PA
    d.loc[enough & (d["4PT Edge (pts/shot)"] > 0), "4PT Verdict"] = "Helps"
    d.loc[enough & (d["4PT Edge (pts/shot)"] <= 0), "4PT Verdict"] = "Hurts"
    return d


OUTPUT_COLS = [
    "3PM", "3PA", "3P%",
    "4PM", "4PA", "4P Misses", "4P%", "4PA Share",
    "Adj 3PM", "Adj 3PA", "Adj 3P%", "3P% Change",
    "Pts/Shot (current)", "Pts/Shot (with 4PT)", "Extra Pts from 4PT", "Pts/Shot Change",
    "Pts per 4PA", "Pts per Adj 3PA", "Break-even 4P%", "4P% vs Break-even",
    "4PT Edge (pts/shot)", "4PT Verdict",
]

# Per player-season
df = add_four_point_columns(summary)[["Season", "Player ID", "Player", "Team", "GP"] + OUTPUT_COLS]

# Per player, all seasons combined (sum the counts, then recompute the rates)
career_counts = summary.groupby(["Player ID", "Player"], as_index=False).agg(
    Seasons=("Season", "nunique"),
    GP=("GP", "sum"),
    **{c: (c, "sum") for c in ["3PM", "3PA", "30+ ft 3PM", "30+ ft 3PA"]},
)
career = add_four_point_columns(career_counts)[["Player", "Seasons", "GP"] + OUTPUT_COLS]


if __name__ == "__main__":
    df.to_csv("four_point_by_season.csv", index=False)
    career.to_csv("four_point_by_player.csv", index=False)

    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 20)
    fmt = {c: "{:.3f}".format for c in ["3P%", "4P%", "4PA Share", "Adj 3P%", "3P% Change",
                                         "Pts/Shot (current)", "Pts/Shot (with 4PT)", "Pts/Shot Change"]}
    show = ["Player", "Seasons", "3PA", "3P%", "4PM", "4PA", "4P%", "Adj 3P%", "3P% Change",
            "Pts/Shot (current)", "Pts/Shot (with 4PT)"]

    print(f"Biggest gainers in points per shot (min {MIN_4PA} career 4PA):")
    top = career[career["4PA"] >= MIN_4PA].sort_values("Pts/Shot Change", ascending=False)
    print(top[show].head(15).to_string(index=False, formatters=fmt))

    print(f"\nWould shooting from 30+ ft help or hurt? (career, min {MIN_4PA} 4PA)")
    verdict_cols = ["Player", "4PA", "4P%", "Adj 3P%", "Break-even 4P%", "4PT Edge (pts/shot)", "4PT Verdict"]
    fmt2 = {**fmt, "Break-even 4P%": "{:.3f}".format, "4PT Edge (pts/shot)": "{:+.3f}".format}
    ranked = career[career["4PA"] >= MIN_4PA].sort_values("4PT Edge (pts/shot)", ascending=False)
    print(ranked[verdict_cols].to_string(index=False, formatters=fmt2))
    print(career["4PT Verdict"].value_counts().to_string())

    print("\nLeague-wide (all top-50 player-seasons):")
    tot = add_four_point_columns(summary[["3PM", "3PA", "30+ ft 3PM", "30+ ft 3PA"]].sum().to_frame().T)
    print(tot[OUTPUT_COLS].to_string(index=False, formatters=fmt))
