"""Figura 4.1: diferença pareada contra o BLIP 384 congelado, na validação e no teste.
Lê as tabelas de diferenças de historico_3conjuntos/tabela_final.md.
Rode a partir da raiz do repositório."""
import re
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
plt.rcParams.update({'font.family': 'Liberation Serif', 'font.size': 10})
md = open('docs/monografia/historico_3conjuntos/tabela_final.md', encoding='utf-8').read()
def diffs(sec):
    blk = md.split(sec)[1].split('\n## ')[0].split('\n### ')[0]
    out = {}
    for line in blk.splitlines():
        if not line.startswith('| BLIP') or 'sem fine' in line: continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        vals = []
        for c in cells[1:]:
            m, lo, hi = [float(x.replace(',', '.').replace('−', '-')) for x in re.findall(r'-?\d+,\d+', c)]
            vals.append((m, lo, hi))
        out[cells[0]] = vals
    return out
te = diffs('### Teste: diferença'); va = diffs('### Validação: diferença')
names = {'BLIP 384, 2 camadas destravadas': 'BLIP 384,\n2 camadas destravadas',
         'BLIP 576, codificador congelado': 'BLIP 576,\ncodificador congelado',
         'BLIP 576, 2 camadas destravadas': 'BLIP 576,\n2 camadas destravadas',
         'BLIP-2 (OPT-2.7b)': 'BLIP-2'}
cfg = list(names)
metr = ['Similaridade', 'F1 de palavras', 'Atributos', 'CIDEr-D']
lims = [(-0.06, 0.07), (-0.06, 0.07), (-0.06, 0.10), (-0.40, 0.55)]
ticks = [[-0.05, 0, 0.05], [-0.05, 0, 0.05], [-0.05, 0, 0.05, 0.10], [-0.25, 0, 0.25, 0.5]]
C = {'pior': '#d03b3b', 'melhor': '#0ca30c', 'empate': '#8a8984'}
ink = '#0b0b0b'; ink2 = '#52514e'
fig, axes = plt.subplots(2, 2, figsize=(6.3, 4.9), sharey=True, dpi=300)
ys = list(range(len(cfg)))[::-1]
def fmt(v):
    return f'{v:+.2f}'.replace('.', ',').replace('-', '−') if v else '0'
for k, (ax, name) in enumerate(zip(axes.flat, metr)):
    ax.axvline(0, color=ink, lw=0.9, zorder=1)
    for y, c in zip(ys, cfg):
        for off, src, mk, alpha, lw in ((0.17, va, 's', 0.55, 1.6), (-0.17, te, 'o', 1.0, 2.2)):
            m, lo, hi = src[c][k]
            v = 'melhor' if lo > 0 else 'pior' if hi < 0 else 'empate'
            ax.plot([lo, hi], [y + off] * 2, color=C[v], lw=lw, alpha=alpha, solid_capstyle='round', zorder=2)
            ax.plot([m], [y + off], marker=mk, ms=5.5, mfc=C[v] if v != 'empate' else 'white', mec=C[v],
                    mew=1.4, alpha=alpha if mk == 's' else 1, zorder=3)
    ax.set_title(name, fontsize=10.5, color=ink, pad=5)
    ax.set_xlim(*lims[k]); ax.set_xticks(ticks[k]); ax.set_xticklabels([fmt(t) for t in ticks[k]], fontsize=8, color=ink2)
    ax.grid(axis='x', color='#e4e3df', lw=0.6, zorder=0)
    for s in ('top', 'right', 'left'): ax.spines[s].set_visible(False)
    ax.spines['bottom'].set_color('#b5b4ae')
    ax.tick_params(axis='y', length=0); ax.tick_params(axis='x', length=0)
    ax.set_ylim(-0.6, len(cfg) - 0.4)
for ax in axes[:, 0]:
    ax.set_yticks(ys); ax.set_yticklabels([names[c] for c in cfg], fontsize=8.5, color=ink)
h = [Line2D([0], [0], color=C['pior'], lw=2, marker='o', ms=5.5, mfc=C['pior'], mec=C['pior'], label='Pior: intervalo todo abaixo de zero'),
     Line2D([0], [0], color=C['empate'], lw=2, marker='o', ms=5.5, mfc='white', mec=C['empate'], mew=1.4, label='Empate: intervalo inclui o zero'),
     Line2D([0], [0], color=C['melhor'], lw=2, marker='o', ms=5.5, mfc=C['melhor'], mec=C['melhor'], label='Melhor: intervalo todo acima de zero'),
     Line2D([0], [0], color=ink2, lw=2.2, marker='o', ms=5.5, mfc=ink2, mec=ink2, label='Teste'),
     Line2D([0], [0], color=ink2, lw=1.6, alpha=0.55, marker='s', ms=5.5, mfc=ink2, mec=ink2, label='Validação')]
fig.legend(handles=h[:3], loc='lower center', ncol=3, frameon=False, fontsize=7.8, bbox_to_anchor=(0.5, 0.035), handlelength=1.8, columnspacing=1.2)
fig.legend(handles=h[3:], loc='lower center', ncol=2, frameon=False, fontsize=7.8, bbox_to_anchor=(0.5, -0.005), handlelength=1.8, columnspacing=1.6)
fig.tight_layout(rect=(0, 0.09, 1, 1), w_pad=1.4, h_pad=1.4)
fig.savefig('docs/monografia/figura-intervalos-3conjuntos.png', facecolor='white')
