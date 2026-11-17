"""Figura 3.2: perdas por época na rodada com três conjuntos, com parada antecipada.
Rode a partir da raiz do repositório: python docs/monografia/figura-perdas-3conjuntos.py"""
import json, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'Liberation Serif'
U = 'docs/monografia/historico_3conjuntos/'
runs = [('blip_384_congelado.json', 'BLIP 384 congelado'),
        ('blip_384_2camadas.json', 'BLIP 384 + 2 camadas'),
        ('blip_576_congelado.json', 'BLIP 576 congelado'),
        ('blip_576_2camadas.json', 'BLIP 576 + 2 camadas'),
        ('blip2_opt27b.json', 'BLIP-2')]
runs = [r for r in runs if os.path.exists(U + r[0])]
TR, VA = '#2a78d6', '#eb6834'; INK = '#333333'; GRID = '#e6e6e6'
n = len(runs); cols = 3 if n > 4 else (2 if n == 4 else n); rows = (n + cols - 1) // cols
fig, axs = plt.subplots(rows, cols, figsize=(6.3, 2.35 * rows + 0.35), sharex=True, sharey=True, squeeze=False)
for ax, (f, title) in zip(axs.flat, runs):
    ep = json.load(open(U + f))['epochs']
    x = [e['epoch'] for e in ep]; tr = [e['train_loss'] for e in ep]; va = [e['val_loss'] for e in ep]
    ax.plot(x, tr, color=TR, lw=1.6, ls='--', label='treino')
    ax.plot(x, va, color=VA, lw=1.8, label='validação')
    b = min(range(len(va)), key=va.__getitem__)
    ax.plot(x[b], va[b], 'o', ms=6, color=VA, mec='white', mew=1.2, zorder=5)
    ax.annotate(f'menor: época {x[b]}\n{va[b]:.3f}'.replace('.', ','), (x[b], va[b]), xytext=(4, 14),
                textcoords='offset points', ha='left', fontsize=8.5, color=INK)
    ax.axvline(x[-1], color='#999999', lw=0.8, ls=':')
    ax.annotate(f'parada: época {x[-1]}', (x[-1], 0.08), xytext=(3, 0), textcoords='offset points',
                ha='left', fontsize=8, color='#666666')
    ax.set_title(title, fontsize=10, color=INK, pad=4)
    ax.set_xlim(0.5, 20.5); ax.set_ylim(0, 2.15); ax.set_xticks([1, 4, 8, 12, 16, 20])
    ax.grid(axis='y', color=GRID, lw=0.7); ax.set_axisbelow(True)
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'): ax.spines[s].set_color('#999999')
    ax.tick_params(colors=INK, labelsize=9, length=3, labelbottom=True)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f'{v:.1f}'.replace('.', ',')))
    ax.set_xlabel('Época', fontsize=9.5, color=INK)
for ax in axs[:, 0]: ax.set_ylabel('Perda', fontsize=9.5, color=INK)
for ax in list(axs.flat)[n:]: ax.axis('off')
h, l = axs[0, 0].get_legend_handles_labels()
fig.legend(h, l, loc='lower center', ncol=2, frameon=False, fontsize=9.5, bbox_to_anchor=(0.5, 0.0))
fig.tight_layout(rect=(0, 0.07, 1, 1), h_pad=1.2, w_pad=1.2)
fig.savefig('docs/monografia/figura-perdas-3conjuntos.png', dpi=300)
