"""以用户当前 Markdown 为唯一正文来源，仅更新 LaTeX，绝不写回 Markdown。"""
from pathlib import Path
import re,hashlib,csv
B=Path(__file__).resolve().parent
L=B/'latex-report'
def inline(s):
 parts=re.split(r'(\$[^$]+\$)',s)
 for i in range(0,len(parts),2):
  q=parts[i].replace('%',r'\%').replace('&',r'\&').replace('_',r'\_').replace('#',r'\#')
  q=q.replace('²',r'\textsuperscript{2}')
  q=re.sub(r'\*\*(.+?)\*\*',lambda m:r'\textbf{'+m[1]+'}',q)
  parts[i]=q
 return ''.join(parts)

def convert(s):
 blocks=re.split(r'\n\s*\n',s.strip());out=[]
 for block in blocks:
  block=block.strip()
  if block.startswith('$$'):
   out.append('\\begin{equation}\n'+block.strip('$').strip()+'\n\\end{equation}')
  elif block.startswith('!['):
   ma=re.fullmatch(r'!\[(.*?)\]\((.*?)\)',block);assert ma,block
   cap,path=ma.groups()
   path=path.replace('prelab-latex/assets/','../prelab-latex/assets/')
   if not path.startswith('../'):path='../'+path
   if 'raw-data.png' in path:
    opts='height=14.5cm,keepaspectratio'
   else:opts='width=\\linewidth,height=.47\\textheight,keepaspectratio'
   out.append('\\begin{figure}[H]\n\\centering\n\\includegraphics['+opts+']{'+path+'}\n\\caption{'+inline(cap)+'}\n\\end{figure}')
   if 'raw-data.png' in path:out.append('\\clearpage')
  elif block.startswith('|'):
   lines=block.splitlines();head=[q.strip() for q in lines[0].strip('|').split('|')]
   data=[[q.strip() for q in ln.strip('|').split('|')] for ln in lines[2:]]
   nc=len(head);size='\\small' if nc<=5 else '\\footnotesize'
   short=len(data)<=10
   if nc>=8:out.append('\\begingroup\n\\setstretch{1.1}')
   if short:out.append('\\begin{center}\n\\begin{minipage}{\\linewidth}\n\\centering')
   env='tabular' if short else 'longtable'
   out.append('{'+size+'\n\\setlength{\\tabcolsep}{'+('5' if nc>=8 else '6')+'pt}\n\\renewcommand{\\arraystretch}{1.15}\n\\begin{'+env+'}{'+'c'*nc+'}\n\\toprule')
   h=' & '.join(map(inline,head))+r' \\'
   out.extend([h,'\\midrule'])
   if not short:out.extend(['\\endfirsthead','\\toprule',h,'\\midrule','\\endhead','\\bottomrule','\\endfoot'])
   for row in data:
    assert len(row)==nc,(head,row)
    out.append(' & '.join(map(inline,row))+r' \\')
   if short:out.append('\\bottomrule')
   out.append('\\end{'+env+'}\n}')
   if short:out.append('\\end{minipage}\n\\end{center}')
   if nc>=8:out.append('\\endgroup')
  elif block.startswith('#'):
   level,title=block.split(' ',1)
   command={1:'section',2:'subsection',3:'subsubsection'}[len(level)]
   if len(level)==1 and not title.startswith('四、'):out.append('\\clearpage')
   out.append('\\'+command+'*{'+inline(title)+'}')
  elif re.match(r'^\d+\. ',block):
   items=re.split(r'(?m)^\d+\. ',block)[1:]
   out.append('\\begin{enumerate}\n'+'\n'.join('\\item '+inline(item.strip()) for item in items)+'\n\\end{enumerate}')
  else:out.append(inline(block))
 return '\n\n'.join(out)+'\n'

def split_blocks(source):
 """识别相邻公式/表格/列表，不要求用户在每个块之前加空行。"""
 lines=source.splitlines();blocks=[];i=0
 def special(line):
  return line.startswith(('#','![','$$','|')) or bool(re.match(r'^\d+\. ',line))
 while i<len(lines):
  line=lines[i].strip()
  if not line:i+=1;continue
  if line=='$$':
   j=i+1
   while j<len(lines) and lines[j].strip()!='$$':j+=1
   assert j<len(lines),'未闭合的公式'
   blocks.append('\n'.join(lines[i:j+1]));i=j+1
  elif line.startswith(('#','![')):
   blocks.append(line);i+=1
  elif line.startswith('|'):
   j=i+1
   while j<len(lines) and lines[j].lstrip().startswith('|'):j+=1
   blocks.append('\n'.join(lines[i:j]));i=j
  elif re.match(r'^\d+\. ',line):
   j=i+1
   while j<len(lines) and (re.match(r'^\d+\. ',lines[j].strip()) or (lines[j].startswith('  ') and lines[j].strip())):j+=1
   blocks.append('\n'.join(lines[i:j]));i=j
  else:
   j=i+1
   while j<len(lines) and lines[j].strip() and not special(lines[j].strip()):j+=1
   blocks.append('\n'.join(lines[i:j]));i=j
 return blocks

def main():
 md=B/'弗兰克-赫兹实验报告.md'
 content=md.read_text();digest=hashlib.sha256(md.read_bytes()).hexdigest()
 body=content[content.index('# 一、预习报告'):]
 chapters=re.split(r'(?m)(?=^# [一二三四]、)',body)
 chapters=[c for c in chapters if c.strip()]
 assert len(chapters)==4
 names=['01-preparation','02-operation-data','03-results','04-discussion']
 for index,(name,chapter) in enumerate(zip(names,chapters)):
  if index==0:
   original=(B/'弗兰克-赫兹实验预习报告.md').read_text().split('# 一、预习报告',1)[1].strip()
   if chapter.split('# 一、预习报告',1)[1].strip()==original:
    tex=(B/'prelab-latex/preparation.tex').read_text().replace('{assets/franck-principle.png}','{../prelab-latex/assets/franck-principle.png}')
   else:
    blocks=split_blocks(chapter)
    blocks=[blk for blk in blocks if not re.match(r'^图\s*1[：:]',blk)]
    tex=convert('\n\n'.join(blocks)).replace('这三组配对峰','\\newpage\n这三组配对峰')
  else:tex=convert('\n\n'.join(split_blocks(chapter)))
  (L/'sections'/f'{name}.tex').write_text(tex)
 assert hashlib.sha256(md.read_bytes()).hexdigest()==digest,'Markdown 被意外修改'
 print('已按当前 Markdown 更新全部正文，Markdown 字节未变。')

if __name__=='__main__':main()
