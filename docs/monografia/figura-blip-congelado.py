import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
plt.rcParams['font.family']='Liberation Serif'
W,H=6.3,2.6
fig=plt.figure(figsize=(W,H)); ax=fig.add_axes([0,0,1,1]); ax.set_xlim(0,W); ax.set_ylim(0,H); ax.axis('off')
FROZ='#dcdcdc'; TR='#cfe8cf'; EDGE='#333333'
def box(x,y,w,h,txt,fc='white',ls='-',fs=9.5):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0,rounding_size=0.06',fc=fc,ec=EDGE,lw=1,ls=ls))
    ax.text(x+w/2,y+h/2,txt,ha='center',va='center',fontsize=fs,linespacing=1.3)
def arr(xy1,xy2,ls='-'):
    ax.annotate('',xy=xy2,xytext=xy1,arrowprops=dict(arrowstyle='-|>',lw=1,color=EDGE,mutation_scale=10,linestyle=ls,shrinkA=0,shrinkB=0))
yc=1.95; h=0.9; y0=yc-h/2
box(0.05,y0,0.9,h,'Fotografia\ndo livro,\n384 × 384\npixels')
box(1.12,y0,1.38,h,'Codificador\nde imagens ViT,\ncerca de 86 milhões\nde parâmetros',fc=FROZ)
ax.text(1.81,y0-0.07,'pesos congelados',ha='center',va='top',fontsize=9)
box(2.67,y0,0.95,h,'Um vetor\npara cada\nbloco da\nimagem')
box(3.79,y0,1.33,h,'Decodificador\nde texto, com\natenção cruzada\nsobre a imagem',fc=TR)
ax.text(4.25,y0-0.07,'pesos ajustados',ha='center',va='top',fontsize=9)
box(5.29,y0+0.15,0.96,h-0.3,'Próxima\npalavra')
for a,b in ((0.95,1.12),(2.5,2.67),(3.62,3.79),(5.12,5.29)): arr((a,yc),(b,yc))
# loop
ax.plot([5.77,5.77,4.95],[y0+0.15,1.05,1.05],color=EDGE,lw=1,ls='--')
arr((4.95,1.05),(4.95,y0),ls='--')
ax.text(5.29,1.0,'volta ao decodificador até\no fim da descrição',ha='center',va='top',fontsize=8.5)
# exemplo
box(0.05,0.1,6.2,0.5,'Exemplo ilustrativo de saída: “Brochura, em bom estado, páginas levemente amareladas, sem anotações.”',fs=9)
fig.savefig('figura-blip-congelado.png',dpi=300)
