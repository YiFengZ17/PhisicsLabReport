"""Markdown 为唯一正文来源：将 密立根油滴实验报告.md 转换为 latex-report/sections/*.tex。"""
from pathlib import Path
import re, hashlib
R = Path(__file__).resolve().parents[1]
source = R / '密立根油滴实验报告.md'
before = source.read_bytes()
md = before.decode('utf-8')
parts = re.split(r'(?m)(?=^# [一二三四]、)', md)
sections = [p for p in parts if re.match(r'^# [一二三四]、', p)]
assert len(sections) == 4, '应包含四个报告正文部分'
WIDTH = {'software-params': '5.6cm', 'raw-data': '16cm', 'software-summary': '11cm'}
SUP = str.maketrans('⁻⁰¹²³⁴⁵⁶⁷⁸⁹', '-0123456789')

def inline(s):
    s = re.sub(r'(?<!\\)%', r'\\%', s)
    s = re.sub(r'([⁻⁰¹²³⁴⁵⁶⁷⁸⁹]+)', lambda m: '$^{' + m[1].translate(SUP) + '}$', s)
    s = s.replace('·', r'$\cdot$').replace('μm', r'$\mu$m')
    return re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', s)

def fig(cap, path, width):
    return r'\includegraphics[width=' + width + ']{../' + path + r'}\caption{' + inline(cap) + '}'

def render(md):
    lines = md.splitlines(); out = []; i = 0; listing = False; math = False
    while i < len(lines):
        l = lines[i]
        if l.startswith('|'):
            block = []
            while i < len(lines) and lines[i].startswith('|'):
                cells = [x.strip() for x in lines[i].strip('|').split('|')]
                if not all(re.fullmatch(r'[-: ]+', c) for c in cells):
                    block.append(cells)
                i += 1
            n = len(block[0])
            out += [r'\begin{center}\small\setlength{\tabcolsep}{4pt}', r'\begin{tabular}{' + 'c' * n + '}', r'\toprule']
            for k, row in enumerate(block):
                out.append(' & '.join(inline(c) for c in row) + r' \\')
                if k == 0:
                    out.append(r'\midrule')
            out += [r'\bottomrule\end{tabular}\end{center}']
            continue
        item = re.match(r'^\d+\. (.*)', l)
        if listing and l.strip() and not item:
            out.append(r'\end{enumerate}'); listing = False
        imgs = re.findall(r'!\[(.*?)\]\((.*?)\)', l)
        if math and l != '$$':
            out.append(l)
        elif item:
            if not listing:
                out.append(r'\begin{enumerate}'); listing = True
            out.append(r'\item ' + inline(item[1]))
        elif l.startswith('# '):
            out.append(r'\section*{' + l[2:] + '}')
        elif l.startswith('## '):
            out.append(r'\subsection*{' + l[3:] + '}')
        elif l.startswith('### '):
            out.append(r'\subsubsection*{' + inline(l[4:]) + '}')
        elif l == '$$':
            out.append(r'\]' if math else r'\['); math = not math
        elif len(imgs) >= 2:
            w = '0.31'
            out.append(r'\begin{figure}[H]\centering')
            cells = [r'\begin{minipage}[b]{' + w + r'\linewidth}\centering' + fig(c, pth, r'\linewidth') + r'\end{minipage}' for c, pth in imgs]
            out.append((r'\hfill' if len(imgs) == 3 else r'\hspace{2em}').join(cells))
            out.append(r'\end{figure}')
        elif len(imgs) == 1:
            cap, path = imgs[0]
            width = next((w for k, w in WIDTH.items() if k in path), r'\linewidth')
            out.append(r'\begin{figure}[H]\centering' + fig(cap, path, width) + r'\end{figure}')
        elif l == '<!-- pagebreak -->':
            out.append(r'\clearpage')
        else:
            out.append(inline(l))
        i += 1
    if listing:
        out.append(r'\end{enumerate}')
    return '\n'.join(out) + '\n'

for name, sec in zip(['01-principle', '02-data', '03-results', '04-discussion'], sections):
    (R / f'latex-report/sections/{name}.tex').write_text(('\\clearpage\n' if name != '01-principle' else '') + render(sec), encoding='utf-8')
assert source.read_bytes() == before, '不得改写 Markdown'
print('Markdown SHA256:', hashlib.sha256(before).hexdigest())
