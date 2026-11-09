"""液体表面张力系数测定：由原始转录数据复算全部派生量并作图。

计算链：
  砝码质量 → 重力（核对记录值）→ 增/减重读数平均（核对记录值）→ F–U 线性拟合得 K、s_K；
  环径 6 次 → 平均值、A 类、B 类（游标卡尺允差 0.02 mm，均匀分布）→ 合成；
  U_max − U_环 → ΔU（核对记录值）→ 平均值、A 类、B 类（课堂给出电压允差 0.1 mV）→ 合成；
  δ = K·ΔU / [π(d1+d2)]，相对不确定度按课堂传播律合成。
"""
from pathlib import Path
from decimal import Decimal
import json, math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[1]
raw = json.loads((ROOT / 'analysis/transcription.json').read_text(encoding='utf-8'))
D = Decimal

# ---------- 1. 原始记录内部一致性核对 ----------
cal = raw['table1_calibration']
g = D(cal['g_m_s2'])
for m, w, a, r, avg in zip(cal['mass_mg'], cal['weight_N'], cal['U_add_mV'], cal['U_remove_mV'], cal['U_mean_mV']):
    assert D(m) / D(1000000) * g == D(w), (m, w)          # mg → kg → N
    assert (D(a) + D(r)) / 2 == D(avg), (a, r, avg)
for blk in raw['pulloff']:
    for umax, uring, du in zip(blk['Umax_mV'], blk['Uring_mV'], blk['dU_mV']):
        assert D(umax) - D(uring) == D(du), (blk['table'], umax, du)
    assert len(blk['dU_mV']) == 6

# ---------- 2. 力敏传感器定标：F = K·U + b ----------
U = np.array([float(x) for x in cal['U_mean_mV']])
F = np.array([float(x) for x in cal['weight_N']])
n = len(U)
K, b = np.polyfit(U, F, 1)
res = F - (K * U + b)
s_y = math.sqrt((res ** 2).sum() / (n - 2))
Sxx = ((U - U.mean()) ** 2).sum()
s_K = s_y / math.sqrt(Sxx)
s_b = s_y * math.sqrt(1 / n + U.mean() ** 2 / Sxx)
r = np.corrcoef(U, F)[0, 1]
u_K = 3 * s_K                                          # 课件：以 3 倍标准差估计系数不确定度
# 交叉核验：教材式最小二乘斜率
K_alt = ((U - U.mean()) * (F - F.mean())).sum() / Sxx
assert abs(K_alt - K) < 1e-15

# ---------- 3. 圆环直径 ----------
DELTA_CALIPER = 0.02  # mm，绪论：分度值 0.02 mm 游标卡尺允许误差；课堂允差表同
def stats(vals, delta_B):
    x = np.array([float(v) for v in vals]); k = len(x)
    mean = x.mean(); s = x.std(ddof=1); uA = s / math.sqrt(k); uB = delta_B / math.sqrt(3)
    return dict(n=k, mean=mean, s=s, uA=uA, uB=uB, u=math.hypot(uA, uB))
d1 = stats(raw['table2_diameter']['d1_inner_mm'], DELTA_CALIPER)
d2 = stats(raw['table2_diameter']['d2_outer_mm'], DELTA_CALIPER)
dsum = d1['mean'] + d2['mean']  # mm

# ---------- 4. 各温度表面张力系数 ----------
DELTA_V = 0.1  # mV，课堂允差表“系统灵敏度 0.1 mV”
STD_T = [10, 20, 25, 30, 35, 40, 45]                       # 教材表 2-10-2
STD_D = [74.22, 72.75, 71.97, 71.18, 70.38, 69.56, 68.74]  # 10^-3 N/m
results = []
for blk in raw['pulloff']:
    st = stats(blk['dU_mV'], 0.0)
    uB_V = math.sqrt(2) * DELTA_V / math.sqrt(3)   # ΔU 为 U_max 与 U_环 两次读数之差
    st['uB'] = uB_V; st['u'] = math.hypot(st['uA'], uB_V)
    delta = K * st['mean'] / (math.pi * dsum * 1e-3)          # N/m
    rel = math.sqrt((u_K / K) ** 2 + (st['u'] / st['mean']) ** 2
                    + (d1['u'] / dsum) ** 2 + (d2['u'] / dsum) ** 2)
    T = float(blk['T_C'])
    d0 = float(np.interp(T, STD_T, STD_D)) * 1e-3
    results.append(dict(table=blk['table'], T=T, dU=st, delta=delta, rel=rel, u_delta=rel * delta,
                        rel_terms=dict(K=u_K / K, dU=st['u'] / st['mean'], d1=d1['u'] / dsum, d2=d2['u'] / dsum),
                        delta0=d0, E=(delta - d0) / d0))

# ---------- 5. 修约：不确定度首位 1/2 留两位，否则一位；测量值末位对齐 ----------
def round_pair(val, unc):
    exp = math.floor(math.log10(abs(unc)))
    first = int(unc / 10 ** exp)
    keep = 2 if first in (1, 2) else 1
    q = exp - keep + 1
    u_r = round(unc / 10 ** q) * 10 ** q
    if u_r >= 10 ** (exp + 1):            # 进位后首位变化时重新判定
        return round_pair(val, u_r)
    v_r = round(val / 10 ** q) * 10 ** q
    nd = max(0, -q)
    return f'{v_r:.{nd}f}', f'{u_r:.{nd}f}'

summary = dict(
    K=K, b=b, s_K=s_K, s_b=s_b, r=r, u_K=u_K, K_rounded=round_pair(K * 1e5, u_K * 1e5),
    d1=d1, d2=d2, dsum=dsum,
    d1_rounded=round_pair(d1['mean'], d1['u']), d2_rounded=round_pair(d2['mean'], d2['u']),
    results=[dict(**x, rounded_mN=round_pair(x['delta'] * 1e3, x['u_delta'] * 1e3)) for x in results],
    slope_meas_mN_per_C=float(np.polyfit([x['T'] for x in results], [x['delta'] * 1e3 for x in results], 1)[0]),
    slope_std_mN_per_C=float((np.interp(35, STD_T, STD_D) - np.interp(18.8, STD_T, STD_D)) / (35 - 18.8)),
)
(ROOT / 'analysis/summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=float), encoding='utf-8')

# ---------- 6. 作图 ----------
CJK = next(p for p in ['/mnt/c/Windows/Fonts/simsun.ttc',
                       '/usr/share/texlive/texmf-dist/fonts/opentype/public/fandol/FandolSong-Regular.otf',
                       '/usr/local/texlive/texmf-dist/fonts/opentype/public/fandol/FandolSong-Regular.otf']
           if Path(p).exists())
font_manager.fontManager.addfont(CJK)
plt.rcParams.update({'font.family': font_manager.FontProperties(fname=CJK).get_name(),
                     'mathtext.fontset': 'stix', 'axes.unicode_minus': False, 'font.size': 10,
                     'axes.edgecolor': '#555555', 'xtick.color': '#333333', 'ytick.color': '#333333'})
BLUE, ORANGE, INK = '#2a78d6', '#eb6834', '#333333'
fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.9), layout='constrained')

xs = np.linspace(0, 850, 2)
a1.plot(xs, (K * xs + b) * 1e3, color=BLUE, lw=1.6, label='线性拟合')
a1.plot(U, F * 1e3, 'o', ms=6, color=BLUE, mec='white', mew=1.5, label='增减重平均读数')
a1.set(xlabel='电压读数 $U$ / mV', ylabel='砝码重力 $F$ / mN', xlim=(-20, 850), ylim=(-1, 36))
a1.text(0.04, 0.95, f'$K={K*1e5:.4f}\\times10^{{-5}}$ N/mV\n$r={r:.6f}$', transform=a1.transAxes,
        va='top', color=INK, fontsize=9.5)
a1.set_title('(a) 力敏传感器定标', fontsize=10.5, color=INK)

Ts = np.linspace(10, 45, 200)
a2.plot(Ts, np.interp(Ts, STD_T, STD_D), color=ORANGE, lw=1.6, label='标准值（教材表 2-10-2）')
a2.plot(STD_T, STD_D, 's', ms=5, color=ORANGE, mec='white', mew=1.2)
a2.errorbar([x['T'] for x in results], [x['delta'] * 1e3 for x in results],
            yerr=[x['u_delta'] * 1e3 for x in results], fmt='o-', ms=6, color=BLUE, lw=1.6,
            mec='white', mew=1.5, capsize=3, elinewidth=1.2, label='本次测量值')
for x in results:
    a2.annotate(f"{x['delta']*1e3:.2f}", (x['T'], x['delta'] * 1e3), textcoords='offset points',
                xytext=(0, -16), ha='center', fontsize=9, color=INK)
a2.set(xlabel='水温 $T$ / ℃', ylabel=r'$\delta$ / (mN$\cdot$m$^{-1}$)', xlim=(8, 47), ylim=(50, 77))
a2.set_title(r'(b) $\delta$–$T$ 曲线对比', fontsize=10.5, color=INK)
for ax in (a1, a2):
    ax.grid(alpha=0.18, lw=0.6); ax.spines[['top', 'right']].set_visible(False)
    ax.legend(frameon=False, fontsize=9, loc='lower right' if ax is a1 else 'center right')
fig.savefig(ROOT / 'assets/surface_tension.png', dpi=220)
print(json.dumps(summary, ensure_ascii=False, indent=1, default=float))
