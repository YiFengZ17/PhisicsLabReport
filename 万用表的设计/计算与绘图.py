from pathlib import Path
import json, math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
ROOT=Path(__file__).resolve().parent
A=ROOT/'assets'
font='/mnt/c/Windows/Fonts/simsun.ttc'
plt.rcParams['font.family']=FontProperties(fname=font).get_name()
from matplotlib import font_manager
font_manager.fontManager.addfont(font)
plt.rcParams.update({'axes.unicode_minus':False,'font.size':11,'axes.spines.top':False,'axes.spines.right':False})
G=np.array([1,2,3,4,5.]); IB=np.array([1,1.9,2.9,3.9,5]);VB=np.array([1,1.9,2.9,3.9,5])
R=np.array([3300,1300,600,500,400,300,250,200,100,50.]);I=np.array([.08,.20,.33,.38,.41,.50,.56,.62,.78,.88])
dI=np.round(G-IB,2);dV=np.round(G-VB,2)
assert np.allclose(dI,[0,.1,.1,.1,0]) and np.allclose(dV,[0,.1,.1,.1,0])
levels=[.1,.2,.5,1,1.5,2.5,5]
ki=max(abs(dI))/5*100;kv=max(abs(dV))/5*100
out={'IG_mA':G.tolist(),'IB_mA':IB.tolist(),'VG_V':G.tolist(),'VB_V':VB.tolist(),'deltaI_mA':dI.tolist(),'deltaV_V':dV.tolist(),'Rx_ohm':R.tolist(),'Ix_mA':I.tolist(),'kI_percent':ki,'kV_percent':kv,'gradeI':next(x for x in levels if x>=ki),'gradeV':next(x for x in levels if x>=kv),'Rg_substitution':243,'Rg_half':233.5,'R1_calibrated':59,'Rg_from_R1':4*59,'Rg_equivalent_from_calibrated':236*59/(236+59),'R3_calibrated':954,'R1_design':243/4,'R3_design':1000-243/5,'R0_half':300,'R0_from_supply':1.5/.005,'I_theory_mA':(300/(300+R)).tolist()}
assert math.isclose(out['R0_half'],out['R0_from_supply'])
(ROOT/'计算结果.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
fig,axs=plt.subplots(1,2,figsize=(9.2,3.6),layout='constrained')
for ax,ref,unit,sym,title in [(axs[0],IB,'mA','I','电流表校验'),(axs[1],VB,'V','V','电压表校验')]:
 ax.plot([0,5.2],[0,5.2],'--',color='#888888',lw=1,label='理想关系')
 ax.plot(ref,G,'o-',color='#176b87',lw=1.4,label='实测校验点')
 ax.set(xlim=(0,5.3),ylim=(0,5.3),xlabel=f'标准表示值 ${sym}_B$ / {unit}',ylabel=f'改装表示值 ${sym}_G$ / {unit}',title=title)
 ax.grid(alpha=.2);ax.legend(loc='upper left',fontsize=9)
fig.savefig(A/'calibration.pdf');fig.savefig(A/'calibration.png',dpi=200);plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(9.2,3.6),layout='constrained')
for ax,lim,title in [(axs[0],3500,'全范围'),(axs[1],650,'低阻区展开')]:
 xx=np.linspace(0,lim,500);ax.plot(xx,300/(300+xx),color='#176b87',label='参考曲线：$I_x=[300/(300+R_x)]$ mA')
 ax.scatter(R,I,color='#bf5b23',s=28,zorder=3,label='实测点')
 ax.set(xlim=(0,lim),ylim=(0,1.04),xlabel='$R_x$ / Ω',ylabel='电流计示值 $I_x$ / mA',title=title)
 ax.grid(alpha=.2);ax.legend(fontsize=8)
fig.savefig(A/'ohm-curve.pdf');fig.savefig(A/'ohm-curve.png',dpi=200);plt.close(fig)
fig,ax=plt.subplots(figsize=(9.2,1.6),layout='constrained');ax.set_axis_off()
ax.plot([0,1],[0,0],color='black',lw=1)
for i in np.arange(0,1.01,.1):
 ax.plot([i,i],[0,.13],color='black',lw=1)
 label='∞' if i==0 else f'{300*(1/i-1):.0f}'
 ax.text(i,.17,label,ha='center',fontsize=10);ax.text(i,-.12,f'{i:.1f}',ha='center',fontsize=10)
ax.text(-.07,.17,'Ω',ha='right');ax.text(-.07,-.12,'$I_x$/mA',ha='right');ax.set(xlim=(-.13,1.05),ylim=(-.3,.45))
fig.savefig(A/'ohm-scale.pdf');fig.savefig(A/'ohm-scale.png',dpi=200);plt.close(fig)
print(json.dumps(out,ensure_ascii=False,indent=2))
