import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
plt.rcParams['font.family']='Liberation Serif'
plt.rcParams['mathtext.fontset']='custom'
plt.rcParams['mathtext.it']='Liberation Serif:italic'
plt.rcParams['mathtext.rm']='Liberation Serif'
W,H=6.3,2.95
fig=plt.figure(figsize=(W,H)); ax=fig.add_axes([0,0,1,1]); ax.set_xlim(0,W); ax.set_ylim(0,H); ax.axis('off')
EDGE='#333333'; C={'treino':'#e3e3e3','validação':'#cfe8cf','teste':'#f6d7a7'}
def rbox(x,y,w,h,fc='white'):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0,rounding_size=0.06',fc=fc,ec=EDGE,lw=1))
def chip(x,y,w,name,label=None):
    ax.add_patch(FancyBboxPatch((x,y),w,0.2,boxstyle='round,pad=0,rounding_size=0.04',fc=C[name],ec=EDGE,lw=0.7))
    ax.text(x+w/2,y+0.1,label or name,ha='center',va='center',fontsize=8.5)
def arr(p1,p2):
    ax.annotate('',xy=p2,xytext=p1,arrowprops=dict(arrowstyle='-|>',lw=1,color=EDGE,mutation_scale=10,shrinkA=0,shrinkB=0))
fs=9.5
# linha 1
y1,h1=1.95,0.9
rbox(0.05,y1,1.55,h1); ax.text(0.825,y1+h1/2,'1. Coleta das\nfotografias e das\ndescrições do catálogo',ha='center',va='center',fontsize=fs,linespacing=1.25)
rbox(1.8,y1,1.55,h1); ax.text(2.575,y1+h1/2,'2. Limpeza das\ndescrições: códigos\ninternos e coleções',ha='center',va='center',fontsize=fs,linespacing=1.25)
rbox(3.55,y1,2.7,h1); ax.text(4.9,y1+h1-0.2,'3. Divisão por livro em três conjuntos',ha='center',va='center',fontsize=fs)
for i,(n,l) in enumerate((('treino','treino, 80%'),('validação','validação, 10%'),('teste','teste, 10%'))):
    chip(3.65+i*0.86,y1+0.18,0.8,n,l)
arr((1.6,y1+h1/2),(1.8,y1+h1/2)); arr((3.35,y1+h1/2),(3.55,y1+h1/2))
# linha 2
y2,h2=0.1,1.15; bw=1.4; xs=[0.05,1.65,3.25,4.85]
txt=['4. $\\mathit{Fine}$-$\\mathit{tuning}$ de cada\nconfiguração, com\nparada antecipada','5. Escolha da\nconfiguração\nfinal','6. Avaliação final,\nfeita uma única vez','7. Integração do\nmodelo escolhido\nà interface web']
uses=[[('treino',None),('validação',None)],[('validação',None)],[('teste',None)],[]]
for x,t,u in zip(xs,txt,uses):
    rbox(x,y2,bw,h2)
    ax.text(x+bw/2,y2+h2-0.4 if u else y2+h2/2,t,ha='center',va='center',fontsize=fs,linespacing=1.25)
    if len(u)==2:
        chip(x+0.08,y2+0.08,0.6,u[0][0],u[0][1]); chip(x+0.72,y2+0.08,0.6,u[1][0],u[1][1])
    elif u:
        chip(x+0.3,y2+0.08,0.8,u[0][0],u[0][1])
for i in range(3): arr((xs[i]+bw,y2+h2/2),(xs[i+1],y2+h2/2))
# 3 -> 4
ax.plot([4.9,4.9,xs[0]+bw/2],[y1,1.6,1.6],color=EDGE,lw=1)
arr((xs[0]+bw/2,1.6),(xs[0]+bw/2,y2+h2))
fig.savefig('figura-etapas-metodo.png',dpi=300)
