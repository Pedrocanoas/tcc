"""Métricas pra comparar a legenda gerada com a legenda de referência do vendedor.

Três medidas complementares (ver model/README.md):
- `similarity`: similaridade de sequência de caracteres (SequenceMatcher) — sensível à
  ordem das frases e ao estilo de quem escreveu.
- `word_f1`: F1 de palavras — ignora a ordem, mas não entende sinônimo.
- atributos (`extract_attributes`): fatos sobre o livro (tipo de capa, estado geral,
  anotações, amarelado, manchas...) extraídos por regra dos dois textos e comparados
  um a um — não depende de ordem nem de estilo.

Uso (recalcula tudo a partir de um log já gerado por src.evaluate, sem rodar o modelo):
    .venv/Scripts/python.exe -m src.metrics caminho/do/eval.log
"""

import argparse
import re
import unicodedata
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path


def normalize(text: str) -> str:
    # o tokenizador do BLIP (bert-base-uncased) remove acentos, então o modelo nunca
    # gera "anotações", só "anotacoes" — comparar sem acento nos dois lados
    return "".join(c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn")


def similarity(a: str, b: str) -> float:
    # autojunk=False: com o padrão (True), se `b` tiver >=200 caracteres, todo caractere
    # que aparece em >1% das posições vira "lixo" — em texto normal isso pega quase todas
    # as letras e derruba a similaridade pra perto de 0 (ver model/README.md)
    return SequenceMatcher(None, normalize(a), normalize(b), autojunk=False).ratio()


def word_f1(predicted: str, reference: str) -> float:
    pred = Counter(re.findall(r"[a-z0-9]+", normalize(predicted)))
    ref = Counter(re.findall(r"[a-z0-9]+", normalize(reference)))
    common = sum((pred & ref).values())
    if not common:
        return 0.0
    precision, recall = common / sum(pred.values()), common / sum(ref.values())
    return 2 * precision * recall / (precision + recall)


# Atributos binários: "o texto diz que o livro TEM isso?". Menção negada ("sem grifos")
# e ausência de menção contam igual (não tem) — vendedor costuma citar o defeito que existe.
PRESENCE_ATTRIBUTES = {
    "anotações/grifos": r"anotac|grif|rabisc|risco|rasura|sublinhad|marcac",
    "carimbo": r"carimb",
    "assinatura/dedicatória": r"assinatura|dedicatoria|nome d[oa] (antig[oa] )?(don[oa]|proprietari[oa])",
    "etiqueta": r"etiqueta",
    "amarelado/pigmentos": r"amarel|pigment|escurecid|oxida",
    "manchas": r"manch",
    "sujidade": r"sujidade|poeira|\bsuj[oa]s?\b",
    "desgaste/sinais de uso": r"desgast|sina(l|is) de (uso|manuseio)|marcas de (uso|manuseio)|manusead",
    "dobras/amassado": r"dobra|amassad|vinco",
    "rasgo": r"rasg",
}

NEGATION_STARTERS = {"sem", "nao", "nem", "nenhum", "nenhuma", "livre", "isento", "isenta"}
# "sem outras anotações" quer dizer que HÁ alguma — não é negação
NOT_A_NEGATION_AFTER = {"outras", "outros", "outra", "outro", "demais", "mais", "maiores", "grandes"}
VERBS = {"tem", "possui", "possuem", "apresenta", "apresentam", "ha", "contem", "se", "nota", "notam"}
NEGATION_BREAKERS = {
    "com", "mas", "porem", "apenas", "so", "somente", "exceto", "salvo", "contudo", "entretanto",
    "capa", "contracapa", "lombada", "pagina", "paginas", "miolo", "borda", "bordas", "corte",
    "folha", "folhas", "livro",
    # quantificador começa uma afirmação nova mesmo sem pontuação antes
    # ("sem riscos nem rabiscos algumas manchinhas amareladas")
    "algum", "alguma", "alguns", "algumas", "pouco", "pouca", "poucos", "poucas", "varios", "varias",
} | VERBS  # fmt: skip
# depois de uma vírgula a negação só continua se o próximo item for outro defeito da lista
# ("sem anotações, grifos ou carimbos"), não em "sem grifos, levemente amareladas"
LIST_CONTINUATION_RE = re.compile(
    r"anotac|grif|rabisc|risco|rasura|sublinhad|marcac|carimb|assinatura|dedicatoria|etiqueta|manch|dobra|"
    r"rasg|dano|defeito|avaria|sujidade"
)

COVER_RE = re.compile(r"(?P<dura>capa dura)|(?P<brochura>brochura)")
STATE_RE = re.compile(
    r"(?P<novo>\bnovo\b|lacrad|seminovo)"
    r"|(?P<otimo>otimo estado|perfeito estado|excelente estado|estado impecavel|otimamente conservad)"
    r"|(?P<muito_bom>muito bom estado|muito bem conservad)"
    r"|(?P<bom>bom estado|bem conservad|\bconservad)"
    r"|(?P<regular>estado regular|mau estado|estado ruim|mal conservad)"
)


def _negated_spans(text: str) -> list[tuple[int, int]]:
    """Trechos do texto (já normalizado) que estão dentro do alcance de uma negação."""
    spans = []
    for sentence in re.finditer(r"[^.;!?]+", text):
        tokens = [(m.group(), sentence.start() + m.start()) for m in re.finditer(r"[a-z0-9]+|,", sentence.group())]
        start = None
        for i, (token, pos) in enumerate(tokens):
            previous = tokens[i - 1][0] if i else ""
            following = tokens[i + 1][0] if i + 1 < len(tokens) else ""
            if token in NEGATION_STARTERS:
                if following in NOT_A_NEGATION_AFTER:
                    if start is not None:
                        spans.append((start, pos))
                        start = None
                elif start is None:
                    start = pos
            elif start is not None:
                negated_verb = token in VERBS and previous in {"nao", "se"}
                broken_by_word = token in NEGATION_BREAKERS and not negated_verb
                broken_by_comma = token == "," and following not in NEGATION_STARTERS and not LIST_CONTINUATION_RE.match(following)
                if broken_by_word or broken_by_comma:
                    spans.append((start, pos))
                    start = None
        if start is not None:
            spans.append((start, sentence.end()))
    return spans


def extract_attributes(text: str) -> dict:
    """Atributos do livro descritos no texto. Binários: True/False. Categóricos
    ("capa", "estado"): o valor, ou None se o texto não menciona."""
    text = normalize(text)
    negated = _negated_spans(text)

    def is_negated(pos: int) -> bool:
        return any(start <= pos < end for start, end in negated)

    attributes = {
        name: any(not is_negated(m.start()) for m in re.finditer(pattern, text))
        for name, pattern in PRESENCE_ATTRIBUTES.items()
    }
    for name, pattern in (("capa", COVER_RE), ("estado", STATE_RE)):
        match = next((m for m in pattern.finditer(text) if not is_negated(m.start())), None)
        attributes[name] = match.lastgroup if match else None
    return attributes


def attribute_report(pairs: list[tuple[str, str]]) -> tuple[str, float]:
    """`pairs` = [(gerado, referência)]. Devolve a tabela por atributo e a média
    (macro) das medidas — F1 nos binários, acerto nos categóricos."""
    extracted = [(extract_attributes(predicted), extract_attributes(reference)) for predicted, reference in pairs]
    lines, scores = [], []
    lines.append(f"{'atributo':26s} {'ref. tem':>8s} {'precisão':>9s} {'recall':>7s} {'F1':>6s}")
    for name in PRESENCE_ATTRIBUTES:
        tp = sum(p[name] and r[name] for p, r in extracted)
        fp = sum(p[name] and not r[name] for p, r in extracted)
        fn = sum(not p[name] and r[name] for p, r in extracted)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        scores.append(f1)
        lines.append(f"{name:26s} {tp + fn:8d} {precision:9.2f} {recall:7.2f} {f1:6.2f}")
    lines.append(f"{'atributo':26s} {'ref. cita':>8s} {'acerto':>9s}")
    for name in ("capa", "estado"):
        mentioned = [(p[name], r[name]) for p, r in extracted if r[name] is not None]
        accuracy = sum(p == r for p, r in mentioned) / len(mentioned) if mentioned else 0.0
        scores.append(accuracy)
        lines.append(f"{name:26s} {len(mentioned):8d} {accuracy:9.2f}")
    return "\n".join(lines), sum(scores) / len(scores)


def summary(pairs: list[tuple[str, str]], split: str = "val") -> str:
    table, attribute_mean = attribute_report(pairs)
    n = len(pairs)
    return (
        f"{table}\n"
        f"== média de acerto por atributo em {n} livros ({split}): {attribute_mean:.2f} ==\n"
        f"== média de F1 de palavras em {n} livros ({split}): {sum(word_f1(p, r) for p, r in pairs) / n:.2f} ==\n"
        f"== média de similaridade em {n} livros ({split}): {sum(similarity(p, r) for p, r in pairs) / n:.2f} =="
    )


LOG_ENTRY_RE = re.compile(r"=== (livro\d+) \(similaridade: [\d.]+\) ===\nesperado : (.*)\ngerado   : (.*)")


def read_log(path: Path) -> dict[str, tuple[str, str]]:
    """{livro_id: (gerado, referência)} de um log gerado por src.evaluate."""
    raw = Path(path).read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("cp1252")  # log redirecionado pelo console do Windows
    return {m.group(1): (m.group(3), m.group(2)) for m in LOG_ENTRY_RE.finditer(text.replace("\r\n", "\n"))}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logs", nargs="+", type=Path)
    args = parser.parse_args()
    for path in args.logs:
        print(f"\n##### {path.name}")
        print(summary(list(read_log(path).values())))


if __name__ == "__main__":
    main()
