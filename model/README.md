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
> não está diferenciando as fotos o suficiente.
>
> **`--no-freeze-vision` tentado e descartado (2026-09-26):** destravar o
> encoder com os hiperparâmetros atuais (lr=5e-5 uniforme, 20 epochs,
> ~2.653 exemplos) piora a situação em vez de ajudar — colapso de modo
> ("mode collapse"): numa amostra de 8 livros do split de validação, a
> similaridade média caiu de 0.44 (encoder congelado) pra 0.22, com 6 de 8
> livros gerando a **legenda idêntica, palavra por palavra**, ignorando a
> foto por completo. Dataset pequeno demais pra destravar o encoder inteiro
> com essa configuração — o modelo encontra um mínimo mais "barato"
> (repetir a legenda mais comum do treino) do que aprender a diferenciar as
> imagens. Checkpoint desse experimento não foi promovido a produção. Se
> for tentar de novo: learning rate bem menor especificamente pro encoder
> (LR diferencial, não a mesma taxa do decoder), menos epochs, e/ou
> destravar só as últimas 1-2 camadas do encoder em vez dele inteiro.
>
> **Vazamento de código do vendedor (corrigido em 2026-09-24, retreinado e
> promovido em 2026-09-26):** ~24% dos livros tinham o código interno do
> vendedor (ex.: `"Local: Direito DR460/01/2005/235AP - Brochura, ..."`)
> sobrando no início da legenda de treino — `strip_leading_seller_code` só
> cobria o formato mais simples (`"<código> - texto"`, prefixo ≤25
> caracteres) e não os formatos com `"Local: <categoria>"` ou `"SKU:
> <número>."`. O modelo aprendeu a reproduzir esse padrão, gerando
> prefixos de código inventados mesmo em fotos sem relação nenhuma com o
> código real. `strip_leading_seller_code` foi reescrita pra cobrir os três
> formatos (heurística: só corta um prefixo se ele tiver dígito e nenhuma
> palavra comum do português); vazamento caiu pra ~0,3% dos livros.
> Retreinado com encoder congelado (isolando essa variável do experimento
> `--no-freeze-vision` acima) e comparado com `src/evaluate.py` no split de
> validação **completo** (192 livros): similaridade média subiu de 0.29
> (checkpoint anterior, dados com vazamento) pra **0.32** (checkpoint
> novo). Melhora modesta mas real — promovido a `model/checkpoints/best/`.
>
> **Vazamento de ID no final da legenda (corrigido em 2026-10-13):**
> investigando outliers de comprimento no dataset, achado um segundo
> vazamento — **10,3% dos livros (197 de 1.918)** tinham um ID interno de
> listagem (sempre 8-9 dígitos) sobrando no **final** da legenda, ex.:
> `"...sem grifos, rabiscos ou anotações. - 201641077."`. Diferente do
> vazamento de 2026-09-24 (que era no início do texto), esse só aparecia
> depois de remover a tag de foto (`_PI1234567_`) do final, expondo o ID
> que estava antes dela. `TRAILING_ID_RE` adicionado em `prepare_dataset.py`
> corta esse padrão (exige "-" explícito antes do número ≥7 dígitos, pra
> não arriscar cortar um ano de 4 dígitos); vazamento caiu de 10,3% pra 0%
> sem encurtar nenhuma legenda indevidamente. Retreinado e promovido a
> `model/checkpoints/best/` em 2026-10-18 — sob o mesmo decoding (beam
> search) do checkpoint anterior, a similaridade média no split de
> validação completo (192 livros) ficou em **0.34** nos dois, ou seja, essa
> troca não mudou a métrica (era um empate, não uma melhora) — a correção
> valeu pela qualidade do dado de treino, não por ganho de similaridade.
>
> **Outros outliers encontrados (não corrigidos ainda):** ~3,8% dos livros
> (73 de 1.918) têm legenda bem mais longa que a média (>408 caracteres,
> acima do limite IQR); dentro desses, uma fração pequena mas real mistura
> **sinopse/resenha de marketing** (`"Resenha: ..."`, 0,3% / 6 livros) ou
> **dimensões físicas** (`"Dimensões: 21 x 13.6 x 1.6 cm"`, 0,4% / 7
> livros) dentro do campo de condição — conteúdo que não é "condição física
> do livro" e ensina o modelo a às vezes gerar texto fora do escopo. Baixo
> volume (<1% cada), não corrigido por ora — risco de um filtro automático
> cortar conteúdo de condição real misturado no mesmo parágrafo.
>
> **Livros que são coleções/multi-volume:** ~5,8% dos livros (111 de
> 1.918) são coleções ou kits de vários volumes (ex.: *"São 26 volumes;
> coleção incompleta; As matérias completas são Matemática, Física..."*,
> livro107) — a legenda muda de estrutura nesses casos (fala de vários
> volumes/estados ao mesmo tempo, às vezes com `"coleção incompleta"`,
> contagens, etc.), diferente do padrão de 1 livro = 1 estado. **Testado em
> 2026-10-28** (`--exclude-colecoes`, já com o fix do split — ver nota
> abaixo): checkpoint treinado sem as coleções e checkpoint de produção
> avaliados no mesmo split de validação sem coleções (180 livros) deram a
> **mesma** similaridade média, **0.34**. Livro a livro o resultado muda
> bastante pra ambos os lados (ex.: livro1299 vai de 0.06 pra 0.58, livro657
> cai de 0.96 pra 0.50), mas se cancela na média — não há sinal de que
> excluir coleções do treino ajude (ou prejudique) a qualidade nos livros
> normais, pela métrica de similaridade usada. Mantido misturado no treino
> (mais dado, nenhuma perda medida).
>
> **Bug no split treino/validação do experimento `--exclude-colecoes`
> (corrigido em 2026-10-28):** a primeira versão de `--exclude-colecoes`
> removia os livros-coleção **antes** de sortear treino/validação
> (`collect_examples` já devolvia a lista filtrada pra `split_by_book`).
> Isso muda a lista de `book_ids` embaralhada e quebra o sorteio inteiro —
> o val set gerado com a flag não tem nenhuma relação com o val set gerado
> sem ela, e pior, livros que o checkpoint de produção viu no treino podiam
> cair nessa nova validação. Qualquer comparação entre os dois seria
> inválida. Corrigido: `collect_examples` agora sempre coleta todos os
> livros e marca cada exemplo com `"colecao": true/false`; o split
> (`split_by_book`) roda sempre sobre a população inteira, e só depois do
> split a flag `--exclude-colecoes` remove as coleções **do treino**
> (nunca da validação, que fica idêntica com ou sem a flag). Pra avaliar
> excluindo coleções, `src/evaluate.py` ganhou a mesma flag, que filtra
> pelo campo `"colecao"` do manifesto na hora de pontuar, sem afetar o
> split.

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

# 3b. inferência condicionada à capa/condição já preenchidas no formulário
#     (evita o modelo ter que adivinhar esses dois atributos pela foto)
.venv/Scripts/python.exe -m src.infer --capa dura --condicao seminovo foto1.jpg

# 4. avaliação: compara gerado vs. legenda original do vendedor
#    (--split val usa livros que o modelo nunca viu no treino)
.venv/Scripts/python.exe -m src.evaluate --split val --limit 10
```

`train.py --limit-train N --epochs 1` é útil para testar rapidamente se o
pipeline roda antes de disparar um treino completo (que em CPU deve demorar
— vale rodar em background).

### Condicionar a legenda à capa/condição já conhecidas

O formulário de cadastro já coleta **Capa** (mole/dura) e **Condição**
(novo/seminovo/usado/antigo) diretamente do usuário — não faz sentido o
modelo ter que adivinhar esses dois atributos pela foto (e às vezes errar,
ex.: dizer "brochura" num livro de capa dura, porque a maioria do dataset é
brochura). `src/prompt.py` monta um prefixo (ex.: `"Capa dura, muito bem
conservado,"`) a partir desses dois campos; passado como `text=` pro BLIP
(`conditional captioning`, suportado nativamente pelo modelo), o decoder
continua a legenda a partir dali em vez de gerar do zero — só precisa
preencher o resto (arranhões, anotações, páginas etc.).

`infer.py --capa/--condicao`, `serve.py` (aceita `capa`/`condicao` no JSON
de entrada) e o formulário (`backend/`/`frontend/`) já usam isso — a
descrição é regenerada automaticamente se você trocar Capa ou Condição
depois de já ter enviado as fotos.

### Outros scripts em `src/`

- **`serve.py`** — processo persistente de inferência (carrega o modelo
  uma vez, atende pedidos via stdin/stdout). É o que o `backend/` usa por
  trás do endpoint `/api/livros/gerar-descricao`, em vez de rodar
  `infer.py` do zero a cada request (~15-20s de carga de modelo evitados).
  Não roda direto por conta própria, é chamado pelo backend.
- **`detect_barcode.py`** — lê um código de barras EAN-13/ISBN numa foto
  (`pyzbar`), sem depender de nenhum checkpoint treinado. Usado pelo
  autofill de título/autor/editora do formulário (`backend/`).
  `.venv/Scripts/python.exe -m src.detect_barcode foto.jpg`. Tenta a foto
  original, depois com realce de contraste, rotações (90/180/270 +
  inclinação leve) e upscale se a imagem for pequena.

  > **Taxa de acerto baixa por natureza:** medido contra `dataset/raw/`
  > (fotos do sebo usadas no treino), a detecção acha 0% dos códigos — não
  > é bug: a maioria dos livros tem só 1 foto (65%, sem contracapa
  > nenhuma), e mesmo os que têm 3 fotos raramente mostram a contracapa de
  > frente (costuma ser lombada, página interna, ou contracapa em ângulo
  > forte, ilegível pro zbar mesmo com as melhorias acima). Pra funcionar
  > na prática, precisa de uma foto relativamente reta e bem iluminada
  > mirando o código de barras — vale considerar um texto de dica perto do
  > upload de fotos no formulário.

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

- Avaliar se vale tentar remover a sinopse/dimensões misturadas nos
  outliers mais longos (~1% do dataset) — baixo volume, pode não compensar
  o risco de cortar conteúdo de condição real no meio do parágrafo.
- Se quiser tentar `--no-freeze-vision` de novo no futuro, meça com
  hiperparâmetros diferentes (ver nota acima) — não repita a configuração
  que já colapsou (lr uniforme 5e-5, 20 epochs, encoder inteiro
  destravado).
- A melhora do fix de vazamento de código foi modesta (0.29 → 0.32) — o
  problema de legendas genéricas/pouco diferenciadas por foto (ver
  "Limitação conhecida" acima) continua em aberto; a causa raiz mais
  provável ainda é o encoder congelado, mas destravá-lo precisa de uma
  configuração mais cuidadosa do que a tentada até agora.
