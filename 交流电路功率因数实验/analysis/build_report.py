from pathlib import Path
import re, hashlib
R=Path(__file__).resolve().parents[1]
source=R/'交流电路功率因数实验报告.md'
before=source.read_bytes()
md=before.decode('utf-8')
# Markdown是唯一正文来源；本脚本只更新LaTeX，不回写文稿。
parts=re.split(r'(?m)(?=^# [一二三四]、)',md)
sections=[part for part in parts if re.match(r'^# [一二三四]、',part)]
assert len(sections)==4, '应包含四个报告正文部分'
def inline(s):
 s=s.replace('%',r'\%')
 return re.sub(r'\*\*(.*?)\*\*',r'\\textbf{\1}',s)
def render(md):
 lines=md.splitlines(); out=[]; i=0; listing=False; math=False
 while i<len(lines):
  l=lines[i]
  if l.startswith('|'):
   block=[]
   while i<len(lines) and lines[i].startswith('|'):
    cells=[x.strip() for x in lines[i].strip('|').split('|')]
    if not all(re.fullmatch(r'[-: ]+',c) for c in cells):block.append(cells)
    i+=1
   n=len(block[0]);out += [r'\begin{center}\small',r'\begin{tabular}{'+'c'*n+'}',r'\toprule']
   for k,row in enumerate(block):
    out.append(' & '.join(inline(c) for c in row)+r' \\')
    if k==0:out.append(r'\midrule')
   out += [r'\bottomrule\end{tabular}\end{center}'];continue
  item=re.match(r'^\d+\. (.*)',l)
  if listing and l.strip() and not item:out.append(r'\end{enumerate}');listing=False
  if item:
   if not listing:out.append(r'\begin{enumerate}');listing=True
   out.append(r'\item '+inline(item[1]))
  elif l.startswith('# '):out.append(r'\section*{'+l[2:]+'}')
  elif l.startswith('## '):out.append(r'\subsection*{'+l[3:]+'}')
  elif l.startswith('### '):out.append(r'\subsubsection*{'+l[4:]+'}')
  elif l=='$$':out.append(r'\]' if math else r'\[');math=not math
  elif l.startswith('!['):
   m=re.match(r'!\[(.*?)\]\((.*?)\)',l);cap,path=m.groups();width='7cm' if 'power-circuit' in path else r'\linewidth'
   if 'raw-data' in path:width='16cm'
   out.append(r'\begin{figure}[H]\centering\includegraphics[width='+width+']{../'+path+r'}\caption{'+cap+r'}\end{figure}')
  elif l=='<!-- pagebreak -->':out.append(r'\clearpage')
  else:out.append(inline(l))
  i+=1
 if listing:out.append(r'\end{enumerate}')
 return '\n'.join(out)+'\n'
for name,sec in zip(['01-principle','02-data','03-results','04-discussion'],sections):
 (R/f'latex-report/sections/{name}.tex').write_text(('\\clearpage\n' if name!='01-principle' else '')+render(sec))

assert source.read_bytes()==before, '不得改写用户Markdown'
print('Markdown SHA256:',hashlib.sha256(before).hexdigest())
