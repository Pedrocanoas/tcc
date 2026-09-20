# model

Geração automática da **descrição de condição** do livro a partir das fotos, via
fine-tuning de um modelo de image captioning pré-treinado
([BLIP](https://huggingface.co/Salesforce/blip-image-captioning-base)).

Escopo: o modelo só gera a parte de condição/estado físico do livro (o texto
livre que hoje o vendedor escreve à mão). Título, autor, ISBN etc. continuam
sendo preenchidos manualmente no formulário — não são coisas que dá pra
inferir da foto.

## Por que fine-tuning e não treinar do zero

O dataset tem 401 livros / ~740 fotos — pequeno demais para treinar um
modelo de captioning do zero (datasets desse tipo costumam ter 100k+
imagens). Por padrão o encoder de visão do BLIP fica **congelado** e só o
decoder de texto é ajustado (menos parâmetros para treinar, menor risco de
overfitting). Use `--no-freeze-vision` em `train.py` para destravar o encoder.

## Setup

```sh
py -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

> **Nota sobre hardware:** a GPU disponível (MX330) tem só 2 GB de VRAM —
> insuficiente para treinar o BLIP com folga. O `requirements.txt` instala a
> build **CPU** do PyTorch por padrão, que é o que foi validado aqui. Se
> quiser tentar GPU mesmo assim, instale a build CUDA correspondente à sua
> driver antes de rodar `pip install -r requirements.txt` (veja
> https://pytorch.org/get-started/locally/) — mas espere ter que usar
> `--batch-size 1` e ainda assim correr risco de faltar memória.

## Uso

```sh
# 1. gera dataset/processed/train.jsonl e val.jsonl a partir de dataset/raw/
.venv/Scripts/python.exe -m src.data.prepare_dataset

# 2. fine-tuning (salva em checkpoints/best e checkpoints/last, ambos gitignored)
.venv/Scripts/python.exe -m src.train --epochs 5 --batch-size 4

# 3. inferência (usa checkpoints/best se existir, senão cai no modelo base)
.venv/Scripts/python.exe -m src.infer caminho/para/foto1.jpg caminho/para/foto2.jpg
```

`train.py --limit-train N --epochs 1` é útil para testar rapidamente se o
pipeline roda antes de disparar um treino completo (que em CPU deve demorar
— vale rodar em background).

## Treinando no Kaggle

Os scripts leem os três diretórios principais (fotos, manifestos processados,
checkpoints) de variáveis de ambiente, com fallback para os caminhos locais —
isso existe justamente para rodar o treino em outro lugar sem mexer no código:

| Variável | Local (default) | No Kaggle |
|---|---|---|
| `TCC_DATASET_RAW_DIR` | `dataset/raw` | `/kaggle/input/<dataset-fotos>/raw` |
| `TCC_DATASET_PROCESSED_DIR` | `dataset/processed` | `/kaggle/working/processed` |
| `TCC_CHECKPOINTS_DIR` | `model/checkpoints` | `/kaggle/working/checkpoints` |

`/kaggle/input` é só leitura, por isso os manifestos e checkpoints precisam
apontar para `/kaggle/working`.

### 1. Subir as fotos como Kaggle Dataset

```sh
cd dataset && zip -r raw.zip raw
```

`dataset/raw` tem ~32 MB — cabe tranquilo num Dataset do Kaggle. Em
kaggle.com → **Create → New Dataset** → upload do `raw.zip` (ele extrai
sozinho; vai ficar acessível em `/kaggle/input/<nome-do-dataset>/raw/...`).

### 2. Subir o código

Mais simples: zipar `model/` (só tem `src/`, `requirements.txt`, `README.md`
— `.venv` e `checkpoints` são gitignored, não faz sentido subir) e criar um
segundo Kaggle Dataset com ele. Alternativa, se o repo já estiver no GitHub:
`!git clone <url-do-repo>` direto na primeira célula do notebook.

### 3. Notebook

Criar o notebook, **Add Data** apontando os dois datasets, e em
**Settings** (barra lateral): Accelerator → GPU (T4 x2 ou P100), Internet →
On (necessário para baixar os pesos do BLIP do Hugging Face na primeira
execução).

Use o notebook pronto em [`kaggle_notebook.ipynb`](kaggle_notebook.ipynb) (**File →
Upload Notebook** no Kaggle) em vez de montar as células manualmente — já tem
os caminhos corretos e comentários explicando cada passo. Resumo do que ele faz:

```python
# célula 1 — não reinstale o torch: o Kaggle já vem com build CUDA pronta
!pip install -q -r /kaggle/input/datasets/<usuário>/<dataset-codigo>/model/requirements-kaggle.txt

# célula 2
!cp -r /kaggle/input/datasets/<usuário>/<dataset-codigo>/model /kaggle/working/model
%cd /kaggle/working/model

import os
os.environ["TCC_DATASET_RAW_DIR"] = "/kaggle/input/datasets/<usuário>/<dataset-fotos>/raw"
os.environ["TCC_DATASET_PROCESSED_DIR"] = "/kaggle/working/processed"
os.environ["TCC_CHECKPOINTS_DIR"] = "/kaggle/working/checkpoints"

# célula 3 — gera os manifestos e inicia o fine-tuning
!python kaggle_train.py \
  --raw-dir /kaggle/input/datasets/<usuário>/<dataset-fotos>/raw \
  --epochs 20 \
  --batch-size 8 \
  --max-length 128
```

> **Nota sobre o layout do Kaggle:** por padrão o Kaggle monta os datasets em
> `/kaggle/input/datasets/<usuário>/<slug>/...` (não mais direto em
> `/kaggle/input/<slug>/...`). Se os caminhos não baterem, confirme rodando
> `!find /kaggle/input -maxdepth 4` numa célula.

O script `kaggle_train.py` também aceita `--processed-dir` e
`--checkpoints-dir`; por padrão ambos ficam em `/kaggle/working`. Se a GPU
ficar sem memória, use `--batch-size 1` ou `--batch-size 2`.

**Sobre `--max-length 128`:** o default anterior (64) truncava 77% das
legendas do dataset durante o treino — o modelo nunca via o fim de boa parte
das frases e, na inferência, raramente aprendia a parar de gerar texto (as
legendas saíam cortadas no meio). 128 cobre ~91% das legendas por inteiro.

Com 743 imagens numa T4, isso deve rodar em minutos, bem dentro da cota
gratuita do Kaggle (não precisa se preocupar com o limite de sessão).

### 4. Trazer o checkpoint de volta

```python
# última célula do notebook
!zip -r /kaggle/working/checkpoint_best.zip /kaggle/working/checkpoints/best
```

Depois de **Save Version** (rodar e commitar o notebook), o zip aparece na
aba **Output** pra baixar direto pelo navegador. Ou, com a
[Kaggle API](https://www.kaggle.com/docs/api) configurada localmente:

```sh
kaggle kernels output <seu-usuario>/<slug-do-notebook> -p ./kaggle-output
```

Por fim, extraia o `checkpoint_best.zip` de forma que o resultado fique em
`model/checkpoints/best/` — é o caminho que `infer.py` usa por padrão.

### 5. Automação: disparar o treino a cada push (GitHub Actions)

`.github/workflows/kaggle-train.yml` (na raiz do repo) roda a cada push que
mexer em `model/**`: instala o `kaggle` CLI e faz `kaggle kernels push -p
model/`, que sobe `kaggle_notebook.ipynb` (usando `model/kernel-metadata.json`
pra configurar GPU/Internet/dataset) e já dispara a execução no Kaggle. Não
precisa mais criar o notebook manualmente pela UI — o primeiro push cria o
kernel `pedrocanoas/tcc-livros-blip-finetune` automaticamente.

Só falta um passo, feito uma única vez pela UI do GitHub (não dá pra
automatizar, é uma chave secreta):

1. Em [kaggle.com/settings](https://www.kaggle.com/settings) → **API** →
   **Create New Token** → baixa um `kaggle.json` com `username` e `key`.
2. No GitHub: **Settings → Secrets and variables → Actions → New repository
   secret**, cria duas:
   - `KAGGLE_USERNAME` = o `username` do `kaggle.json`
   - `KAGGLE_KEY` = o `key` do `kaggle.json`

Depois disso, todo `git push` que altere `model/` dispara um novo treino
sozinho (consome cota de GPU do Kaggle a cada vez — evite commits triviais
nessa pasta). Acompanhe o progresso em kaggle.com → **Your Work → Notebooks**;
o download do checkpoint continua manual (passo 4 acima).

## Próximos passos

- Rodar um treino completo com `--max-length 128` e avaliar se a legenda
  para de sair cortada e se a qualidade melhorou (`src/evaluate.py`).
- Considerar um processo Python persistente por trás do endpoint do
  `backend/` (hoje ele recarrega o modelo do zero a cada request, ~15-20s).
