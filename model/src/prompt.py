"""Monta o prefixo de condicionamento do BLIP a partir dos campos que o
formulário de cadastro já coleta (capa, condição) — em vez do modelo ter que
adivinhar esses dois atributos pela foto (e às vezes errar, ex.: sempre dizer
"brochura" mesmo em livro de capa dura), ele já começa a legenda sabendo
disso e só preenche o resto (arranhões, anotações, páginas etc.). BLIP
suporta "conditional captioning" nativamente: passar `text=prefixo` faz o
decoder continuar a partir dali em vez de gerar do zero.

Uso: import build_prefix — chamado por infer.py e serve.py.
"""

CAPA_TEXTO = {
    "mole": "Brochura",
    "dura": "Capa dura",
}

CONDICAO_TEXTO = {
    "novo": "praticamente novo",
    "seminovo": "muito bem conservado",
    "usado": "com sinais de uso",
    "antigo": "antigo, mas conservado",
}


def build_prefix(capa: str | None, condicao: str | None) -> str | None:
    partes = [parte for parte in (CAPA_TEXTO.get(capa), CONDICAO_TEXTO.get(condicao)) if parte]
    if not partes:
        return None
    return ", ".join(partes) + ","
