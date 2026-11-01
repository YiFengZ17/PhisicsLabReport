from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MultipleLocator


ROOT = Path(__file__).resolve().parent

t = np.array([25.0, 30.0, 35.1, 40.0, 45.0, 50.0, 55.1, 60.1])
u = np.array([33.5, 39.6, 45.3, 51.1, 56.8, 62.7, 68.3, 74.2])

slope, intercept = np.polyfit(t, u, 1)
t_fit = np.linspace(t.min(), t.max(), 300)
u_fit = slope * t_fit + intercept

alpha_0 = 0.004280
epsilon = 1.3
t_theory = np.linspace(0.0, 65.0, 400)
u_theory = 1000 * alpha_0 * epsilon * t_theory / (4 + 2 * alpha_0 * t_theory)

fig, ax = plt.subplots(figsize=(12.78, 8.10), dpi=100)
ax.scatter(t, u, s=125, color="#225e9b", edgecolor="#225e9b",
           zorder=4, label="Measured data")
ax.plot(t_fit, u_fit, color="#225e9b", linewidth=3.0, zorder=3,
        label=f"Measured linear fit: U={slope:.4g}t+{intercept:.4g}")
ax.plot(t_theory, u_theory, color="#cc5633", linewidth=3.0,
        linestyle="--", zorder=3,
        label=r"Textbook expectation ($\alpha_0=0.004280$)")

for index, (temperature, voltage) in enumerate(zip(t, u)):
    is_last = index == len(t) - 1
    ax.annotate(
        f"({temperature:.1f}, {voltage:.1f})",
        xy=(temperature, voltage),
        xytext=((-7 if is_last else 7), 8),
        textcoords="offset points",
        ha=("right" if is_last else "left"),
        va="bottom",
        fontsize=13.5,
        color="#263238",
        bbox={"boxstyle": "round,pad=0.15", "fc": "white", "ec": "none", "alpha": 0.78},
        zorder=5,
    )

ax.set_xlim(0, 65)
ax.set_ylim(0, 85)
ax.xaxis.set_major_locator(MultipleLocator(10))
ax.yaxis.set_major_locator(MultipleLocator(10))
ax.xaxis.set_minor_locator(MultipleLocator(2.5))
ax.yaxis.set_minor_locator(MultipleLocator(2.5))

# 主网格标示十单位尺度，小网格将每个主格细分为四份。
ax.set_axisbelow(True)
ax.grid(which="major", color="#9aa0a6", linewidth=0.65, alpha=0.48)
ax.grid(which="minor", color="#b8bdc3", linewidth=0.32, alpha=0.32)

ax.set_title("Cu50 Non-equilibrium Bridge: U-t Characteristic", fontsize=21)
ax.set_xlabel("Temperature, t (°C)", fontsize=18)
ax.set_ylabel("Bridge output, U (mV)", fontsize=18)
ax.tick_params(axis="both", which="major", labelsize=17, length=7, width=1.2)
ax.tick_params(axis="both", which="minor", length=3, width=0.6)
ax.legend(loc="upper left", frameon=False, fontsize=15)
for spine in ax.spines.values():
    spine.set_linewidth(1.3)

fig.tight_layout()
for output in (
    ROOT / "assets" / "cu50_u_t_curve.png",
    ROOT / "latex-report" / "assets" / "cu50-u-t.png",
):
    fig.savefig(output, dpi=100)
plt.close(fig)
