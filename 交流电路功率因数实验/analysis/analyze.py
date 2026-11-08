from pathlib import Path
import json,csv
from decimal import Decimal
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties, fontManager
ROOT=Path(__file__).resolve().parents[1]
s=json.loads((ROOT/'analysis/transcription.json').read_text())
# 最新原始PDF及用户确认：45 Hz C7为0.173 A。
s['data']['45']['I'][7]='0.173'
C=np.array([0]+[float(v) for _,v in s['combinations']])
for combo,v in s['combinations']:
 assert sum(Decimal(s['capacitors_uF'][x]) for x in combo.split('+'))==Decimal(v)
rows=[]; summary=[]
for f in ['45','50','55']:
 d=s['data'][f]
 for k in range(8):
  I,U,P=map(Decimal,[d['I'][k],d['U'][k],d['P'][k]])
  pf=P/(U*I)
  assert abs(float(pf)-float(P)/float(U)/float(I))<1e-12
  rows.append([f,k,str(C[k]),str(I),str(U),str(P),d['pf_record'][k],str(pf),str(Decimal(d['pf_record'][k])-pf)])
 j=int(np.argmax(list(map(float,d['pf_record']))))
 summary.append({'f':int(f),'j':j,'C':C[j],'pf':float(d['pf_record'][j]),'pf_calc':float(Decimal(d['P'][j])/Decimal(d['I'][j])/Decimal(d['U'][j])),'I0':float(d['I'][0]),'Iopt':float(d['I'][j]),'Pmin':min(map(float,d['P'])),'Pmax':max(map(float,d['P']))})
with (ROOT/'analysis/recalculated.csv').open('w') as o:
 w=csv.writer(o);w.writerow(['f_Hz','index','C_uF','I_A','U_V','P_W','pf_measured','P_div_UI','difference']);w.writerows(rows)
(ROOT/'analysis/confirmed.json').write_text(json.dumps(s,ensure_ascii=False,indent=2))
(ROOT/'analysis/summary.json').write_text(json.dumps(summary,indent=2))
fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
font=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family':font.get_name(),'axes.unicode_minus':False,'font.size':10})
fig,axs=plt.subplots(1,2,figsize=(10,3.8),layout='constrained')
for f,color,marker in [('45','#2563a8','o'),('50','#d16b20','s'),('55','#258563','^')]:
 d=s['data'][f]
 axs[0].plot(C,list(map(float,d['pf_record'])),marker=marker,color=color,label=f'{f} Hz',lw=1)
 axs[1].plot(C,list(map(float,d['I'])),marker=marker,color=color,label=f'{f} Hz',lw=1)
axs[0].set(ylabel='记录的功率因数',ylim=(0.25,1.05))
axs[1].set(ylabel='总电流 / A',ylim=(0.08,.34))
for ax in axs:
 ax.set_xlabel('实际并联电容 / μF');ax.grid(alpha=.2);ax.legend();ax.spines[['top','right']].set_visible(False)
fig.savefig(ROOT/'assets/power_curves.png',dpi=210)
fig.savefig(ROOT/'assets/power_curves.pdf')
print(json.dumps(summary,ensure_ascii=False,indent=2))
