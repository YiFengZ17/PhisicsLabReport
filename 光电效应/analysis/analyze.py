from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'analysis/verified-data.json').read_text())
# 宋体：优先 Windows SimSun，云端 Linux 回退到 TeX Live 自带的 FandolSong
CJK_FONT=next(p for p in ['/mnt/c/Windows/Fonts/simsun.ttc','/usr/share/texlive/texmf-dist/fonts/opentype/public/fandol/FandolSong-Regular.otf','/usr/local/texlive/texmf-dist/fonts/opentype/public/fandol/FandolSong-Regular.otf'] if Path(p).exists())
font_manager.fontManager.addfont(CJK_FONT)
plt.rcParams.update({'font.family':font_manager.FontProperties(fname=CJK_FONT).get_name(),'axes.unicode_minus':False,'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white'})
c=299792458.; e=1.602176634e-19; h0=6.62607015e-34
w=np.array(d['wavelength_nm']); U=-np.array(d['cutoff_signed_V']); mean=U.mean(0); ua=U.std(0,ddof=1)/np.sqrt(3); x=c/(w*1e-9)/1e14

def fit(x,y):
 X=np.column_stack([x,np.ones_like(x)]); coef=np.linalg.lstsq(X,y,rcond=None)[0];res=y-X@coef
 cov=(res@res)/(len(x)-2)*np.linalg.inv(X.T@X)
 return coef,cov,res,1-res@res/np.sum((y-y.mean())**2)
(a,b),cov,res,r2=fit(x,mean);sa,sb=np.sqrt(np.diag(cov));v0=-b/a;sv0=np.sqrt(cov[1,1]/a**2+b*b*cov[0,0]/a**4-2*b*cov[0,1]/a**3)
L=np.array(d['distance_mm'])/1000; IL=np.array(d['distance_current_1e10A']); D=np.array(d['aperture_mm']); ID=np.array(d['aperture_current_1e10A'])
coefL,covL,resL,r2L=fit(1/L**2,IL); coefD,covD,resD,r2D=fit(D**2,ID)
out={'frequency_1e14Hz':x.tolist(),'mean_cutoff_V':mean.tolist(),'uA_mean_V':ua.tolist(),'a_V':a,'b_V':b,'u_a_V':sa,'u_b_V':sb,'cov_ab_V2':cov[0,1],'residual_V':res.tolist(),'sse_V2':float(res@res),'r2':r2,'r':np.sqrt(r2),'h_Js':e*a/1e14,'u_h_Js':e*sa/1e14,'W_eV':-b,'u_W_eV':sb,'W_J':-e*b,'u_W_J':e*sb,'nu0_Hz':v0*1e14,'u_nu0_Hz':sv0*1e14,'relative_error_percent':abs(e*a/1e14/h0-1)*100,'relative_fit_uncertainty_percent':sa/a*100,'distance_fit':{'slope':coefL[0],'intercept':coefL[1],'r2':r2L},'aperture_fit':{'slope':coefD[0],'intercept':coefD[1],'r2':r2D}}
# 独立中心化公式交叉核对最小二乘及斜率标准误差。
ac=np.sum((x-x.mean())*(mean-mean.mean()))/np.sum((x-x.mean())**2)
assert np.isclose(ac,a)
assert np.isclose(sa,np.sqrt(sum(res**2)/(5-2)/sum((x-x.mean())**2)))
assert len(x)==5 and U.shape==(3,5)
(ROOT/'analysis/results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(out,ensure_ascii=False,indent=2))
def save(fig,name):
 fig.savefig(ROOT/'assets'/f'{name}.png',dpi=220,bbox_inches='tight');plt.close(fig)
fig,axs=plt.subplots(2,1,figsize=(7.5,5.4),height_ratios=[3,1],sharex=True,layout='constrained')
xx=np.linspace(5,8.4,200)
axs[0].errorbar(x,mean,yerr=ua,fmt='o',color='#24578a',capsize=4,label='三次平均值 ± 平均值A类标准不确定度')
axs[0].plot(xx,a*xx+b,color='#333333',label='五点普通最小二乘拟合')
axs[0].text(.04,.76, f'$U_s/\\mathrm{{V}}={a:.6f}x{b:+.6f}$\n$x=ν/(10^{{14}}\,\mathrm{{Hz}})$', transform=axs[0].transAxes, fontsize=10);axs[0].set_ylabel('截止电压 $U_s$ / V');axs[0].legend(fontsize=9);axs[0].grid(alpha=.2)
axs[1].axhline(0,color='#888888',lw=1);axs[1].plot(x,res*1000,'o',color='#24578a');axs[1].set_ylabel('残差 / mV');axs[1].set_xlabel('频率 $ν$ / $10^{14}$ Hz');axs[1].grid(alpha=.2)
save(fig,'cutoff_fit')
fig,ax=plt.subplots(figsize=(7.5,4.6),layout='constrained')
for wv,row,color,m in zip(w,d['current_1e10A'],['#24578a','#c17b27','#846aa7','#527748','#b85170'],['o','s','^','D','v']):
 ax.plot(d['voltage_V'],row,marker=m,ms=3,lw=1,label=f'{wv} nm',color=color)
ax.axhline(0,color='#aaa',lw=.6);ax.set_xlabel('$U_{AK}$ / V');ax.set_ylabel('电流 $i$ / $10^{-10}$ A');ax.legend();ax.grid(alpha=.2);save(fig,'iv_curves')
fig,axs=plt.subplots(1,2,figsize=(9,3.9),layout='constrained')
for ax,z,y,coef,xlabel in [(axs[0],1/L**2,IL,coefL,'$1/L^2$ / m$^{-2}$'),(axs[1],D**2,ID,coefD,'孔径平方 $Φ^2$ / mm$^2$')]:
 zz=np.linspace(0,max(z)*1.08,100);ax.plot(zz,np.polyval(coef,zz),color='#333333',lw=1,label='带截距线性拟合');ax.scatter(z,y,color='#24578a',s=25,label='20.00 V实测电流');ax.set_xlabel(xlabel);ax.set_ylabel('$i$ / $10^{-10}$ A');ax.text(.04,.68, f'$y={coef[0]:.6f}x{coef[1]:+.6f}$\n$y=i/(10^{{-10}}\,\mathrm{{A}})$', transform=ax.transAxes,fontsize=9);ax.set_xlim(left=0);ax.set_ylim(bottom=0);ax.grid(alpha=.2);ax.legend(fontsize=8)
save(fig,'intensity_relations')
