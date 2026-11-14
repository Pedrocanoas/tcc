import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
plt.rcParams.update({'font.family':'Liberation Serif','font.size':10})
cfg=['BLIP 576 px,\ncodificador congelado','BLIP 384 px,\nduas camadas destravadas','BLIP 576 px,\nduas camadas destravadas','BLIP-2, Q-Former\ne LoRA','Produção anterior,\nlimpeza intermediária']
data={'Similaridade':[(-0.027,-0.050,-0.004),(-0.003,-0.020,0.015),(-0.026,-0.045,-0.008),(0.020,0.002,0.037),(-0.007,-0.028,0.013)],
'F1 de palavras':[(-0.049,-0.075,-0.022),(-0.015,-0.032,0.004),(-0.018,-0.037,0.000),(0.010,-0.009,0.030),(-0.018,-0.041,0.003)],
'Atributos':[(-0.010,-0.063,0.048),(-0.031,-0.073,0.019),(-0.029,-0.082,0.031),(-0.030,-0.083,0.026),(-0.061,-0.105,-0.009)]}
C={'pior':'#d03b3b','melhor':'#0ca30c','empate':'#8a8984'}
ink='#0b0b0b';ink2='#52514e'
fig,axes=plt.subplots(1,3,figsize=(6.3,2.9),sharey=True,dpi=300)
ys=list(range(len(cfg)))[::-1]
for ax,(name,rows) in zip(axes,data.items()):
    ax.axvline(0,color=ink,lw=0.9,zorder=1)
    for y,(m,lo,hi) in zip(ys,rows):
        v='melhor' if lo>0 else 'pior' if hi<0 else 'empate'
        ax.plot([lo,hi],[y,y],color=C[v],lw=2,solid_capstyle='round',zorder=2)
        ax.plot([m],[y],marker='o',ms=6,mfc=C[v] if v!='empate' else 'white',mec=C[v],mew=1.6,zorder=3)
    ax.set_title(name,fontsize=10.5,color=ink,pad=6)
    ax.set_xlim(-0.115,0.065)
    ax.set_xticks([-0.10,-0.05,0,0.05])
    ax.set_xticklabels(['−0,10','−0,05','0','+0,05'],fontsize=8,color=ink2)
    ax.grid(axis='x',color='#e4e3df',lw=0.6,zorder=0)
    for s in ('top','right','left'): ax.spines[s].set_visible(False)
    ax.spines['bottom'].set_color('#b5b4ae')
    ax.tick_params(axis='y',length=0); ax.tick_params(axis='x',length=0)
    ax.set_ylim(-0.6,len(cfg)-0.4)
axes[0].set_yticks(ys); axes[0].set_yticklabels(cfg,fontsize=8.5,color=ink)
h=[Line2D([0],[0],color=C['pior'],lw=2,marker='o',ms=6,mfc=C['pior'],mec=C['pior'],label='Pior: intervalo todo abaixo de zero'),
   Line2D([0],[0],color=C['empate'],lw=2,marker='o',ms=6,mfc='white',mec=C['empate'],mew=1.6,label='Empate: intervalo inclui o zero'),
   Line2D([0],[0],color=C['melhor'],lw=2,marker='o',ms=6,mfc=C['melhor'],mec=C['melhor'],label='Melhor: intervalo todo acima de zero')]
fig.legend(handles=h,loc='lower center',ncol=3,frameon=False,fontsize=7.8,bbox_to_anchor=(0.5,0.0),handlelength=1.8,columnspacing=1.2)
fig.tight_layout(rect=(0,0.09,1,1),w_pad=1.6)
fig.savefig('figura-intervalos.png',facecolor='white')
