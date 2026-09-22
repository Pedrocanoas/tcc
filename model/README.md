# model

Geração automática da **descrição de condição** do livro a partir das fotos, via
fine-tuning de um modelo de image captioning pré-treinado
([BLIP](https://huggingface.co/Salesforce/blip-image-captioning-base)).

Escopo: o modelo só gera a parte de condição/estado físico do livro (o texto
livre que hoje o vendedor escreve à mão). Título, autor, ISBN etc. continuam
sendo preenchidos manualmente no formulário — não são coisas que dá pra
inferir da foto.

## Por que fine-tuning e não treinar do zero

O dataset tem ~1.918 livros / ~2.975 fotos (2.962 exemplos imagem+legenda,
2.653 treino / 309 validação) — ainda pequeno pra treinar um modelo de
captioning do zero (datasets desse tipo costumam ter 100k+ imagens). Por
padrão o encoder de visão do BLIP fica **congelado** e só o decoder de
texto é ajustado (menos parâmetros para treinar, menor risco de
overfitting). Use `--no-freeze-vision` em `train.py` para destravar o encoder.

> **Limitação conhecida:** mesmo com ~1.918 livros, a avaliação
> (`src/evaluate.py`) mostra o modelo gerando legendas bem parecidas entre
> livros com condições bem diferentes — indício de que o encoder congelado
> não está diferenciando as fotos o suficiente. Se persistir depois do
> retreino com o dataset maior, o próximo passo é tentar
> `--no-freeze-vision` (mais lento, mais parâmetros, mas usa a imagem de
> verdade em vez de aprender só o "estilo" médio do texto).

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

# 4. avaliação: compara gerado vs. legenda original do vendedor
#    (--split val usa livros que o modelo nunca viu no treino)
.venv/Scripts/python.exe -m src.evaluate --split val --limit 10
```

`train.py --limit-train N --epochs 1` é útil para testar rapidamente se o
pipeline roda antes de disparar um treino completo (que em CPU deve demorar
— vale rodar em background).

### Outros scripts em `src/`

- **`serve.py`** — processo persistente de inferência (carrega o modelo
  uma vez, atende pedidos via stdin/stdout). É o que o `backend/` usa por
  trás do endpoint `/api/livros/gerar-descricao`, em vez de rodar
  `infer.py` do zero a cada request (~15-20s de carga de modelo evitados).
  Não roda direto por conta própria, é chamado pelo backend.
- **`detect_barcode.py`** — lê um código de barras EAN-13/ISBN numa foto
  (`pyzbar`), sem depender de nenhum checkpoint treinado. Usado pelo
  autofill de título/autor/editora do formulário (`backend/`).
  `.venv/Scripts/python.exe -m src.detect_barcode foto.jpg`.

## Treinando no Kaggle

Os scripts leem os três diretórios principais (fotos, manifestos processados,
checkpoints) de variáveis de ambiente, com fallback para os caminhos locais —
isso existe justamente para rodar o treino em outro lugar sem mexer no código:

| Variável | Local (default) | No Kaggle |
|---|---|---|
| `TCC_DATASET_RAW_DIR` | `dataset/raw` | `/kaggle/input/<dataset-fotos>` |
| `TCC_DATASET_PROCESSED_DIR` | `dataset/processed` | `/kaggle/working/processed` |
| `TCC_CHECKPOINTS_DIR` | `model/checkpoints` | `/kaggle/working/checkpoints` |

`/kaggle/input` é só leitura, por isso os manifestos e checkpoints precisam
apontar para `/kaggle/working`.

### 1. Subir as fotos como Kaggle Dataset

```sh
cd dataset && zip -r raw.zip raw
```

> **Cuidado ao atualizar via `kaggle datasets version`:** se usar uma
> *junction*/symlink apontando pra `dataset/raw` numa pasta de staging (pra
> não duplicar os dados), o zip da própria CLI do Kaggle "achata" o conteúdo
> do link — os livros acabam na raiz do dataset (`livro001/...`), sem o
> prefixo `raw/`. Se isso acontecer, é só tirar o `/raw` do
> `TCC_DATASET_RAW_DIR`/`--raw-dir` (em vez de re-subir tudo de novo).

`dataset/raw` tem hoje ~310 MB — ainda cabe tranquilo num Dataset do Kaggle
(limite gratuito é bem maior). Em kaggle.com → **Create → New Dataset** →
upload do `raw.zip` (ele extrai sozinho; fica acessível em
`/kaggle/input/<nome-do-dataset>/raw/...`). Pra atualizar depois, veja o
aviso da *junction* acima.

### 2. Código

Não precisa de um segundo Dataset pro código: o notebook clona o repo
direto do GitHub (`!git clone`) na primeira célula, então sempre usa a
versão mais recente do `main` sem precisar re-subir nada manualmente.

### 3. Notebook

Criar o notebook, **Add Input** apontando o dataset das fotos, e em
**Settings** (barra lateral): Accelerator → GPU (T4 x2 ou P100), Internet →
On (necessário tanto pro `git clone` quanto pra baixar os pesos do BLIP do
Hugging Face na primeira execução).

Use o notebook pronto em [`kaggle_notebook.ipynb`](kaggle_notebook.ipynb) (**File →
Upload Notebook** no Kaggle) em vez de montar as células manualmente — já tem
os caminhos corretos e comentários explicando cada passo. Resumo do que ele faz:

```python
# célula 1 — clona o código direto do GitHub (sempre pega a versão mais recente do main)
!git clone --depth 1 https://github.com/Pedrocanoas/tcc.git /kaggle/working/repo
%cd /kaggle/working/repo/model

# célula 2 — não reinstale o torch: o Kaggle já vem com build CUDA pronta
!pip install -q -r requirements-kaggle.txt

# célula 3
import os
os.environ["TCC_DATASET_RAW_DIR"] = "/kaggle/input/datasets/<usuário>/<dataset-fotos>"
os.environ["TCC_DATASET_PROCESSED_DIR"] = "/kaggle/working/processed"
os.environ["TCC_CHECKPOINTS_DIR"] = "/kaggle/working/checkpoints"

# célula 4 — gera os manifestos e inicia o fine-tuning
!python kaggle_train.py \
  --raw-dir /kaggle/input/datasets/<usuário>/<dataset-fotos> \
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

Com ~2.975 imagens numa T4, isso deve rodar em minutos, bem dentro da cota
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

1. Em [kaggle.com/settings/api](https://www.kaggle.com/settings/api) →
   **Generate New Token** → copia o token (string única, mostrada uma vez só).
2. No GitHub: **Settings → Secrets and variables → Actions → New repository
   secret** → `KAGGLE_API_TOKEN` = o token copiado.

(A CLI `kaggle` 2.x não aceita mais usuário+chave via env var — só esse
token único, ou o arquivo `~/.kaggle/access_token`.)

Depois disso, todo `git push` que altere `model/` dispara um novo treino
sozinho (consome cota de GPU do Kaggle a cada vez — evite commits triviais
nessa pasta). Acompanhe o progresso em kaggle.com → **Your Work → Notebooks**;
o download do checkpoint continua manual (passo 4 acima).

## Próximos passos

- Avaliar o checkpoint treinado com o dataset expandido (~1.918 livros) e
  ver se o `--max-length 128` resolveu o corte de legenda e se o volume
  maior de dados reduziu a repetição de legendas genéricas entre livros
  diferentes (`src/evaluate.py`).
- Se a repetição persistir, tentar `--no-freeze-vision` (ver nota acima).
