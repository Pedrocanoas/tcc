import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
from PIL import Image
import numpy as np
plt.rcParams['font.family']='Liberation Serif'
plt.rcParams['mathtext.fontset']='custom'; plt.rcParams['mathtext.it']='Liberation Serif:italic'; plt.rcParams['mathtext.rm']='Liberation Serif'
W,H=6.3,5.6
fig=plt.figure(figsize=(W,H)); ax=fig.add_axes([0,0,1,1]); ax.set_xlim(0,W); ax.set_ylim(0,H); ax.axis('off')
EDGE='#333333'; FROZ='#dcdcdc'; TR='#cfe8cf'; MUT='#666666'; ERR='#c0392b'
def box(x,y,w,h,txt='',fc='white',fs=9.5,ls='-',lw=1,bold=False,color='black'):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0,rounding_size=0.05',fc=fc,ec=EDGE,lw=lw,ls=ls))
    if txt: ax.text(x+w/2,y+h/2,txt,ha='center',va='center',fontsize=fs,linespacing=1.25,fontweight='bold' if bold else 'normal',color=color)
def arr(p1,p2,ls='-',color=EDGE):
    ax.annotate('',xy=p2,xytext=p1,arrowprops=dict(arrowstyle='-|>',lw=1,color=color,mutation_scale=10,linestyle=ls,shrinkA=0,shrinkB=0))
def title(y,t): ax.text(0.05,y,t,fontsize=10.5,fontweight='bold',va='top')
# ---- 1
title(5.55,'1. O codificador lê a fotografia')
img=Image.open('docs/monografia/figura-fotos-anuncio.jpg').crop((30,20,640,880))
y1=4.35; hh=0.95
ax.imshow(np.asarray(img),extent=(0.15,0.15+hh*610/860,y1-0.05,y1-0.05+hh),zorder=2)
x=0.15+hh*610/860+0.18
arr((x-0.13,y1+0.42),(x,y1+0.42))
box(x,y1,1.75,0.85,'Codificador de imagens\ncongelado: não muda\nno treinamento',fc=FROZ)
x2=x+1.75+0.2; arr((x2-0.2,y1+0.42),(x2,y1+0.42))
# vector of numbers
vals=[0.12,-0.80,0.45,0.91,-0.33,0.07]
for i,v in enumerate(vals):
    ax.add_patch(Rectangle((x2+i*0.36,y1+0.32),0.34,0.22,fc='white',ec=EDGE,lw=0.8))
    ax.text(x2+i*0.36+0.17,y1+0.43,f'{v:.2f}'.replace('.',','),ha='center',va='center',fontsize=7.5)
ax.text(x2+6*0.36+0.03,y1+0.43,'…',va='center',fontsize=10)
ax.text(x2+1.1,y1+0.24,'resumo da foto em números',ha='center',va='top',fontsize=9,color=MUT)
# ---- 2
title(4.05,'2. O decodificador escreve uma palavra por vez')
ax.plot([4.1,4.1],[4.38,3.75],color=EDGE,lw=1,ls='--'); arr((4.1,3.75),(4.1,3.31),ls='--')
ax.text(4.17,3.85,'resumo da foto, usado em todos os passos',fontsize=8.5,color=MUT,va='center')
rows=[('início','Brochura,'),('Brochura,','em'),('Brochura, em','bom'),('Brochura, em bom','estado,'),('…, dedicatória na folha de rosto.','fim')]
ytop=3.35; rh=0.33
ax.text(1.2,ytop+0.05,'texto já escrito',ha='center',fontsize=9,color=MUT)
ax.text(5.45,ytop+0.05,'próxima palavra',ha='center',fontsize=9,color=MUT)
dec_y0=ytop-len(rows)*rh-0.02
box(2.75,dec_y0,1.7,len(rows)*rh-0.04,'Decodificador\nde texto\n\najustado no\ntreinamento',fc=TR)
for i,(a,b) in enumerate(rows):
    y=ytop-(i+1)*rh
    box(0.15,y,2.3,rh-0.07,a,fs=9,color=MUT if a in ('início',) else 'black')
    arr((2.45,y+(rh-0.07)/2),(2.75,y+(rh-0.07)/2))
    arr((4.45,y+(rh-0.07)/2),(4.9,y+(rh-0.07)/2))
    box(4.9,y,1.1,rh-0.07,b,fs=9,bold=b!='fim',color=MUT if b=='fim' else 'black')
# ---- 3
title(1.2,'3. No treinamento, o erro corrige só o decodificador')
yb=0.35; bh=0.62
box(0.15,yb,1.75,bh,'Palavra do modelo:\n“regular”',fs=9)
box(2.1,yb,1.75,bh,'Palavra do vendedor:\n“bom”',fs=9)
box(4.05,yb,2.1,bh,'Diferença entre as duas\najusta os pesos do\ndecodificador',fs=9,fc=TR)
ax.text(1.995,yb+bh/2,'≠',ha='center',va='center',fontsize=13)
arr((3.85,yb+bh/2),(4.05,yb+bh/2))
ax.text(0.15,dec_y0-0.12,'A palavra escolhida entra no texto já escrito do passo seguinte, até o modelo escolher o fim.',fontsize=9,color=MUT,va='top')
fig.savefig('docs/monografia/figura-blip-passo-a-passo.png',dpi=300,bbox_inches='tight',pad_inches=0.04)
