"""密立根油滴实验：由原始记录复算电荷量，并用平均值法、公约数法、多重差值法求 e。

计算链：U、l、t →（v=l/t）→ 未修正半径 r → 修正后电荷量 q（教材式 4-10-7）
        → 三种方法求 e → 平均值的 A 类标准不确定度 s/√N。
常量取数据处理软件“参数设置”中的值（与教材相同，仅空气黏滞系数为 1.83e-5）。
"""
from pathlib import Path
import json, math, statistics as st

ROOT = Path(__file__).resolve().parents[1]
raw = json.loads((ROOT / 'analysis/transcription.json').read_text(encoding='utf-8'))
P = {k: float(v) for k, v in raw['software_params'].items()}
RHO, G, D, ETA, B, PCM = P['rho_kg_m3'], P['g_m_s2'], P['d_m'], P['eta_Pa_s'], P['b_m_cmHg'], P['p_cmHg']
E0 = 1.602e-19          # 确定电荷数 n 所用的基本电荷参考值（与软件一致）
E_STD = 1.602176634e-19  # 公认值，仅用于比较

def charge(U, l, t, eta=ETA):
    v = l / t
    r = math.sqrt(9 * eta * v / (2 * RHO * G))
    q = 18 * math.pi / math.sqrt(2 * RHO * G) * (eta * l / (t * (1 + B / (PCM * r)))) ** 1.5 * D / U
    return q, r, v

sh = raw['sheet']; sw = raw['software']
rows = []
for i in range(10):
    U = float(sh['U_V'][i]); l = float(sh['l_mm'][i]) * 1e-3; t = float(sh['t_s'][i])
    q, r, v = charge(U, l, t)
    q182, _, _ = charge(U, l, t, eta=1.82e-5)
    # 与软件显示（三位有效数字）核对
    assert f'{q:.2e}'.replace('e-1', 'e-1') == sw['q_C'][i] or abs(q - float(sw['q_C'][i])) / q < 0.006, (i, q, sw['q_C'][i])
    assert round(q / E0) == sw['n'][i], (i, q / E0, sw['n'][i])
    rows.append(dict(i=i + 1, drop=sh['drop'][i], U=U, t=t, v=v, r=r, q=q, q182=q182))

# ---------- 方法二：公约数法（教材逐次相减法，软件同法） ----------
srt = sorted(rows, key=lambda x: x['q'])
qs = [x['q'] for x in srt]
dq1 = [qs[k + 1] - qs[k] for k in range(9)]
m2 = []
for x in srt:
    nc = x['q'] / E0; n = round(nc)
    m2.append(dict(i=x['i'], drop=x['drop'], q=x['q'], nc=nc, n=n, e=x['q'] / n))
e2 = [x['e'] for x in m2]

# ---------- 方法一：平均值法（同一油滴两次测量相邻，差值远小于组间差值，归为一组） ----------
groups = {}
for x in rows:
    groups.setdefault(x['drop'], []).append(x['q'])
m1 = []
for drop in sorted(groups, key=lambda k: st.mean(groups[k])):
    qbar = st.mean(groups[drop]); nc = qbar / E0; n = round(nc)
    m1.append(dict(drop=drop, qbar=qbar, nc=nc, n=n, e=qbar / n))
e1 = [x['e'] for x in m1]

# ---------- 方法三：多重差值法（一阶差 Δq1、二阶差 Δq2，各差值除以其电荷数 k） ----------
dq2 = [abs(dq1[k + 1] - dq1[k]) for k in range(8)]
m3 = []
for order, arr in ((1, dq1), (2, dq2)):
    for k, x in enumerate(arr):
        kk = round(x / E0)
        m3.append(dict(order=order, j=k + 1, dq=x, kc=x / E0, k=kk, e=x / kk if kk else None))
e3 = [x['e'] for x in m3 if x['e'] is not None]

def summarize(vals):
    n = len(vals); m = st.mean(vals); s = st.stdev(vals)
    return dict(N=n, mean=m, s=s, uA=s / math.sqrt(n), E=(m - E_STD * 1e19) / (E_STD * 1e19))

def round_pair(val, unc):
    exp = math.floor(math.log10(abs(unc))); first = int(unc / 10 ** exp)
    q = exp - (2 if first in (1, 2) else 1) + 1
    u_r = round(unc / 10 ** q) * 10 ** q
    if u_r >= 10 ** (exp + 1):
        return round_pair(val, u_r)
    nd = max(0, -q)
    return f'{round(val / 10 ** q) * 10 ** q:.{nd}f}', f'{u_r:.{nd}f}'

res = {}
for name, vals in (('平均值法', e1), ('公约数法', e2), ('多重差值法', e3)):
    sm = summarize([v * 1e19 for v in vals]); sm['rounded'] = round_pair(sm['mean'], sm['uA']); res[name] = sm

out = dict(rows=rows, sorted_q=qs, dq1=dq1, dq2=dq2, method1=m1, method2=m2, method3=m3, results=res,
           q_eta_ratio=st.mean(r['q'] / r['q182'] for r in rows),
           pair_dq=[abs(groups[d][0] - groups[d][1]) for d in sorted(groups)])
(ROOT / 'analysis/summary.json').write_text(json.dumps(out, ensure_ascii=False, indent=1, default=float), encoding='utf-8')

for x in rows:
    print(f"{x['i']:2d} drop{x['drop']} U={x['U']:.0f} t={x['t']:.2f} v={x['v']*1e3:.4f}mm/s r={x['r']*1e6:.3f}um q={x['q']*1e19:.3f}")
print('dq1', [f'{x*1e19:.2f}' for x in dq1]); print('dq2', [f'{x*1e19:.2f}' for x in dq2])
for x in m1: print('M1', x['drop'], f"{x['qbar']*1e19:.3f}", f"{x['nc']:.2f}", x['n'], f"{x['e']*1e19:.4f}")
for x in m2: print('M2', x['i'], f"{x['q']*1e19:.3f}", f"{x['nc']:.2f}", x['n'], f"{x['e']*1e19:.4f}")
for x in m3: print('M3', x['order'], x['j'], f"{x['dq']*1e19:.2f}", f"{x['kc']:.2f}", x['k'], f"{x['e']*1e19:.4f}" if x['e'] else '-')
for k, v in res.items(): print(k, {a: (round(b, 5) if isinstance(b, float) else b) for a, b in v.items()})
print('q(1.83)/q(1.82)=', out['q_eta_ratio'])
