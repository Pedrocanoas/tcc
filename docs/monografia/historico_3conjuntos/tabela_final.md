# Resultados finais — divisão 80/10/10, 192 livros por conjunto

Média; desvio padrão (dp) por livro — nos atributos, que são uma medida do conjunto inteiro, o dp é o erro padrão por bootstrap; IC 95% por bootstrap (2.000 reamostragens dos livros, as mesmas para todos os modelos).


## Teste

| Modelo | Similaridade | F1 de palavras | Atributos | CIDEr-D |
|---|---|---|---|---|
| BLIP sem fine-tuning | 0,162 (dp 0,063) [0,153; 0,170] | 0,017 (dp 0,034) [0,013; 0,022] | 0,000 (dp 0,000) [0,000; 0,000] | 0,001 (dp 0,004) [0,000; 0,001] |
| BLIP 384, codificador congelado | 0,476 (dp 0,192) [0,449; 0,505] | 0,426 (dp 0,198) [0,399; 0,456] | 0,245 (dp 0,017) [0,212; 0,275] | 0,732 (dp 1,658) [0,522; 0,989] |
| BLIP 384, 2 camadas destravadas | 0,477 (dp 0,200) [0,450; 0,507] | 0,432 (dp 0,206) [0,404; 0,464] | 0,240 (dp 0,017) [0,206; 0,272] | 0,760 (dp 1,771) [0,529; 1,036] |
| BLIP 576, codificador congelado | 0,478 (dp 0,194) [0,451; 0,507] | 0,428 (dp 0,210) [0,399; 0,460] | 0,264 (dp 0,018) [0,227; 0,300] | 0,738 (dp 1,708) [0,514; 1,009] |
| BLIP 576, 2 camadas destravadas | 0,475 (dp 0,193) [0,447; 0,503] | 0,428 (dp 0,208) [0,401; 0,458] | 0,266 (dp 0,020) [0,226; 0,301] | 0,628 (dp 1,355) [0,453; 0,852] |
| BLIP-2 (OPT-2.7b) | 0,511 (dp 0,205) [0,482; 0,541] | 0,465 (dp 0,228) [0,434; 0,500] | 0,234 (dp 0,011) [0,212; 0,255] | 0,980 (dp 1,968) [0,722; 1,281] |

### Teste: diferença contra o BLIP 384 congelado (IC 95% pareado)

| Modelo | Similaridade | F1 de palavras | Atributos | CIDEr-D |
|---|---|---|---|---|
| BLIP sem fine-tuning | -0,314 [-0,344; -0,287] | -0,409 [-0,440; -0,381] | -0,245 [-0,275; -0,212] | -0,732 [-0,988; -0,520] |
| BLIP 384, 2 camadas destravadas |  0,001 [-0,011; 0,014] |  0,006 [-0,006; 0,018] | -0,005 [-0,019; 0,007] |  0,028 [-0,096; 0,171] |
| BLIP 576, codificador congelado |  0,002 [-0,015; 0,020] |  0,002 [-0,016; 0,021] |  0,019 [-0,025; 0,067] |  0,006 [-0,212; 0,226] |
| BLIP 576, 2 camadas destravadas | -0,002 [-0,021; 0,018] |  0,002 [-0,018; 0,022] |  0,021 [-0,012; 0,052] | -0,105 [-0,342; 0,124] |
| BLIP-2 (OPT-2.7b) |  0,034 [0,015; 0,056] |  0,039 [0,017; 0,062] | -0,011 [-0,043; 0,023] |  0,248 [0,024; 0,494] |

## Validação

| Modelo | Similaridade | F1 de palavras | Atributos | CIDEr-D |
|---|---|---|---|---|
| BLIP sem fine-tuning | 0,160 (dp 0,062) [0,151; 0,169] | 0,013 (dp 0,024) [0,010; 0,017] | 0,000 (dp 0,000) [0,000; 0,000] | 0,000 (dp 0,001) [0,000; 0,000] |
| BLIP 384, codificador congelado | 0,472 (dp 0,192) [0,444; 0,500] | 0,425 (dp 0,206) [0,396; 0,455] | 0,239 (dp 0,018) [0,202; 0,274] | 0,640 (dp 1,630) [0,422; 0,890] |
| BLIP 384, 2 camadas destravadas | 0,475 (dp 0,190) [0,448; 0,503] | 0,418 (dp 0,203) [0,390; 0,446] | 0,250 (dp 0,018) [0,214; 0,283] | 0,615 (dp 1,660) [0,393; 0,870] |
| BLIP 576, codificador congelado | 0,489 (dp 0,202) [0,461; 0,519] | 0,436 (dp 0,221) [0,405; 0,468] | 0,266 (dp 0,021) [0,224; 0,304] | 0,816 (dp 2,099) [0,555; 1,139] |
| BLIP 576, 2 camadas destravadas | 0,490 (dp 0,198) [0,462; 0,518] | 0,450 (dp 0,220) [0,419; 0,481] | 0,260 (dp 0,019) [0,221; 0,294] | 0,807 (dp 2,006) [0,539; 1,115] |
| BLIP-2 (OPT-2.7b) | 0,514 (dp 0,198) [0,486; 0,542] | 0,470 (dp 0,225) [0,437; 0,502] | 0,296 (dp 0,022) [0,251; 0,338] | 0,892 (dp 2,090) [0,619; 1,201] |

### Validação: diferença contra o BLIP 384 congelado (IC 95% pareado)

| Modelo | Similaridade | F1 de palavras | Atributos | CIDEr-D |
|---|---|---|---|---|
| BLIP sem fine-tuning | -0,311 [-0,338; -0,284] | -0,412 [-0,443; -0,383] | -0,239 [-0,274; -0,202] | -0,640 [-0,890; -0,422] |
| BLIP 384, 2 camadas destravadas |  0,003 [-0,010; 0,016] | -0,007 [-0,020; 0,006] |  0,011 [-0,005; 0,028] | -0,025 [-0,105; 0,070] |
| BLIP 576, codificador congelado |  0,018 [-0,001; 0,036] |  0,011 [-0,010; 0,033] |  0,026 [-0,002; 0,055] |  0,176 [-0,001; 0,390] |
| BLIP 576, 2 camadas destravadas |  0,018 [0,001; 0,035] |  0,025 [0,005; 0,044] |  0,020 [-0,004; 0,045] |  0,167 [0,012; 0,349] |
| BLIP-2 (OPT-2.7b) |  0,042 [0,023; 0,061] |  0,045 [0,021; 0,068] |  0,056 [0,021; 0,091] |  0,252 [0,085; 0,439] |

## Treino (history.json)

| Modelo | Épocas treinadas | Melhor época | Menor perda de validação | Horas de GPU (treino) |
|---|---|---|---|---|
| BLIP 384, codificador congelado | 6 | 3 | 1,282 | 0,56 |
| BLIP 384, 2 camadas destravadas | 6 | 3 | 1,280 | 0,76 |
| BLIP 576, codificador congelado | 7 | 4 | 1,322 | 1,03 |
| BLIP 576, 2 camadas destravadas | 7 | 4 | 1,273 | 1,73 |
| BLIP-2 (OPT-2.7b) | 14 | 11 | 0,911 | 1,65 |

A perda de validação do BLIP-2 não é comparável à dos BLIP: os tokenizadores são diferentes (OPT contra BERT).
