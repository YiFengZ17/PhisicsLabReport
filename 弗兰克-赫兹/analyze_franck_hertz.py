from pathlib import Path
import csv,json,math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
BASE=Path(__file__).resolve().parent
ASSET=BASE/'assets'; ASSET.mkdir(exist_ok=True)
# 逐电压行转录；保留原记录末位，不使用教材范例。
rows=[
[0,0,0,0,0,0,0,0,0,0],
[0,1,1,2,4,5,7,9,12,14],
[18,21,26,31,35,39,44,50,55,61],
[65,69,73,77,81,84,88,93,98,104],
[109,116,123,132,137,144,150,155,162,166],
[170,173,177,180,182,183,178,171,170,166],
[167,178,188,195,207,221,229,240,248,256],
[261,266,269,272,274,276,275,274,270,262],
[248,236,223,224,233,246,265,283,301,312],
[322,333,340,346,349,351,352,352,350,349],
[346,341,331,320,300,287,283,287,300,312],
[332,350,366,383,391,403,413,418,419,421],
[421,421,419,417,412,405,393,378,365,357],
[355,360,368,383,399,414,428,445,455,466],
[475,482,485,487,490,490,489,486,481,474],
[462,450,443,438,436,439,445,454,466,478],
[491,503,514,525,532,540,547,553,557,560],
[562,561,559,554,549,542,536,532,530,531],
[535,541,548,558,567,577,588,602,611,621],
[630,638,646,650,665,659,660,659,656,655],
]
x=np.arange(1,201,dtype=float)/2; y=np.asarray(rows,dtype=float).ravel()
assert len(y)==200
before=np.array([27.5,38.4,48.8,60.3,72.9,85.6,98.8])
after=np.array([27.4,38.5,48.8,60.3,72.7,85.6,98.8])
ib=np.array([205,314,415,510,604,708,837])
ia=np.array([133,203,274,351,433,526,642])
# 在七个明显峰簇内找最大值，平顶区间用中点；完整区间供审查。
windows=[(25,29),(35,40),(46,51),(58,62),(70,75),(83,88),(95,100)]
peaks=[]
for j,(lo,hi) in enumerate(windows,1):
 ix=np.flatnonzero((x>=lo)&(x<=hi)); ymax=y[ix].max(); ids=ix[y[ix]==ymax]
 assert np.all(np.diff(ids)==1)
 left,right=x[ids[0]],x[ids[-1]]
 assert y[ids[0]-1]<ymax and y[ids[-1]+1]<ymax
 peaks.append(dict(n=j,low=left,high=right,U=(left+right)/2,I=ymax))
manual=np.array([p['U'] for p in peaks]); n=np.arange(1,8,dtype=float)
def fit(U):
 dx=n-n.mean();dy=U-U.mean();sxx=float(dx@dx);syy=float(dy@dy);sxy=float(dx@dy)
 b=sxy/sxx;a=float(U.mean()-b*n.mean());r=sxy/math.sqrt(sxx*syy)
 resid=U-a-b*n;sse=float(resid@resid)
 se=math.sqrt(sse/(len(U)-2)/sxx)
 ur=abs(b)*math.sqrt((1/r**2-1)/(len(U)-2))
 coef=np.linalg.lstsq(np.column_stack([np.ones(7),n]),U,rcond=None)[0]
 assert np.allclose(coef,[a,b],rtol=0,atol=1e-12)
 assert math.isclose(se,ur,abs_tol=1e-12)
 return dict(A=a,slope=b,r=r,R2=r*r,u=se,relative_u=100*se/abs(b),error=100*abs(b-11.61)/11.61,
             Snn=sxx,SUU=syy,SnU=sxy,SSE=sse,residuals=resid.tolist())
res={k:fit(U) for k,U in [('before',before),('manual',manual),('after',after)]}
res['peaks']=peaks
res['drift']={'dU':(after-before).tolist(),'dI':(ia-ib).tolist(),'current_pct':(100*(ia-ib)/ib).tolist(),
              'mean_U':float((after-before).mean()),'mean_current_pct':float((100*(ia-ib)/ib).mean()),
              'slope_change':res['after']['slope']-res['before']['slope']}
(BASE/'fit_results.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n')
with (BASE/'手动测量数据.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['U_G2K_V','I_A_nA']);w.writerows(zip(x,y))
with (BASE/'自动峰值数据.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['n','before_U_V','before_I_nA','after_U_V','after_I_nA']);w.writerows(zip(n.astype(int),before,ib,after,ia))
# 宋体：优先 Windows SimSun，云端 Linux 回退到 TeX Live 自带的 FandolSong
font=FontProperties(fname=next(p for p in ['/mnt/c/Windows/Fonts/simsun.ttc','/usr/share/texlive/texmf-dist/fonts/opentype/public/fandol/FandolSong-Regular.otf','/usr/local/texlive/texmf-dist/fonts/opentype/public/fandol/FandolSong-Regular.otf'] if Path(p).exists()))
plt.rcParams.update({'font.family':font.get_name(),'axes.unicode_minus':False,'font.size':11,'figure.dpi':150})
# Explicit font application avoids font-cache dependence.
def cn(ax):
 for item in [ax.title,ax.xaxis.label,ax.yaxis.label,*ax.get_xticklabels(),*ax.get_yticklabels()]: item.set_fontproperties(font)
 if ax.get_legend():
  for item in ax.get_legend().get_texts(): item.set_fontproperties(font)
fig,ax=plt.subplots(figsize=(9,4.8))
ax.plot(x,y,'o-',ms=2.5,lw=1,color='#22577a',label='手动测量（200 个采样点，连线引导视线）')
ax.scatter(manual,[p['I'] for p in peaks],color='#bc4749',s=32,zorder=5,label='判定的七个峰')
for p in peaks:
 ax.annotate(f"{p['n']}: {p['U']:g} V",(p['U'],p['I']),xytext=(0,14),textcoords='offset points',ha='center',fontproperties=font,fontsize=9)
ax.set(xlabel='加速电压 $U_{G_2K}$ / V',ylabel='板极电流 $I_A$ / nA',xlim=(0,103),ylim=(-10,735))
ax.grid(alpha=.2);ax.legend(loc='upper left');cn(ax);fig.tight_layout();fig.savefig(ASSET/'manual_curve.png',dpi=240);plt.close(fig)
fig,axes=plt.subplots(2,1,figsize=(8.5,7),sharex=True,gridspec_kw={'height_ratios':[3,1]})
for k,U,c,mark,label in [('before',before,'#22577a','o','自动（手动前）'),('manual',manual,'#bc4749','s','手动'),('after',after,'#6a994e','^','自动（手动后）')]:
 v=res[k]; axes[0].plot(n,U,mark,color=c,ms=6,label=f"{label}：斜率 {v['slope']:.5f} V")
 axes[0].plot(n,v['A']+n*v['slope'],color=c,lw=1.2)
 axes[1].plot(n,v['residuals'],mark+'-',color=c,ms=4)
axes[0].set(ylabel='峰位 $U_n$ / V');axes[0].legend();axes[1].set(xlabel='峰序 n',ylabel='残差 / V',xticks=n);axes[1].axhline(0,color='gray',lw=.8)
for ax in axes:ax.grid(alpha=.2);cn(ax)
fig.tight_layout();fig.savefig(ASSET/'peak_linear_fit.png',dpi=240);plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(9,3.8))
axes[0].plot(n,ib,'o-',color='#22577a',label='手动前');axes[0].plot(n,ia,'s-',color='#bc4749',label='手动后')
axes[0].set(xlabel='峰序 n',ylabel='自动测量峰电流 / nA',xticks=n);axes[0].legend()
axes[1].bar(n,after-before,color='#6a994e');axes[1].axhline(0,color='gray',lw=.8);axes[1].set(xlabel='峰序 n',ylabel='峰位变化（后 - 前）/ V',xticks=n,ylim=(-.25,.15))
for ax in axes:ax.grid(alpha=.2);cn(ax)
fig.tight_layout();fig.savefig(ASSET/'drift_comparison.png',dpi=240);plt.close(fig)
print(json.dumps(res,ensure_ascii=False,indent=2))
