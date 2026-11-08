# Preços Poedagar — referência, aprovação e aplicação

Os 12 modelos comerciais desejados foram encontrados nas páginas individuais do site 2 nesta consulta.
Cada modelo possui ao menos uma variante anunciada disponível. A seleção original foi mantida; nenhuma substituição adicional foi necessária.
São anúncios comerciais da fonte, não confirmação de referências físicas de fabricante ou estoque VRAS.

**12 preços aprovados e gravados no catálogo; 0 produtos com status publicado.**
Veja [POEDAGAR_APPLIED_PRICES.md](POEDAGAR_APPLIED_PRICES.md) para o registro da autorização, condições e testes.
O preço unitário anunciado foi aplicado sem adotar Pix, cupom ou quantidade mínima. A promoção da fonte não vira promoção da VRAS.
A diferença compara apenas a pesquisa Poedagar anterior fornecida no briefing com a consulta atual do mesmo anúncio.
Não é uma diferença entre os antigos relógios VRAS e os novos Poedagar: são produtos distintos.

| ID VRAS novo | Modelo | Referência anterior | Preço atual verificado | Diferença da pesquisa anterior | Fonte | Consulta UTC | Estado |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 13 | Poedagar Army | R$ 196,92 | R$ 196,92 | R$ 0,00 | [Página individual](https://lojaspoedagar.com.br/army/p) | 2026-11-08T00:02:44 | Preço aplicado; rascunho |
| 14 | Poedagar Deluxe | R$ 199,90 | R$ 199,90 | R$ 0,00 | [Página individual](https://lojaspoedagar.com.br/deluxe/p) | 2026-11-08T00:02:44 | Preço aplicado; rascunho |
| 15 | Poedagar Deluxe Golden | R$ 194,90 | R$ 194,90 | R$ 0,00 | [Página individual](https://lojaspoedagar.com.br/deluxe-golden/p) | 2026-11-08T00:02:44 | Preço aplicado; rascunho |
| 16 | Poedagar Golden Mars | R$ 197,90 | R$ 197,90 | R$ 0,00 | [Página individual](https://lojaspoedagar.com.br/golden-mars/p) | 2026-11-08T00:02:44 | Preço aplicado; rascunho |
| 17 | Poedagar Golden Moon | R$ 197,20 | R$ 197,20 | R$ 0,00 | [Página individual](https://lojaspoedagar.com.br/golden-moon/p) | 2026-11-08T00:02:44 | Preço aplicado; rascunho |
| 18 | Poedagar Golden Neptune | R$ 197,40 | R$ 197,40 | R$ 0,00 | [Página individual](https://lojaspoedagar.com.br/neptune/p) | 2026-11-08T00:02:44 | Preço aplicado; rascunho |
| 19 | Poedagar Golden Star | R$ 179,90 | R$ 179,90 | R$ 0,00 | [Página individual](https://lojaspoedagar.com.br/golden-star/p) | 2026-11-08T00:02:44 | Preço aplicado; rascunho |
| 20 | Poedagar King Royal | R$ 219,90 | R$ 219,90 | R$ 0,00 | [Página individual](https://lojaspoedagar.com.br/king-royal/p) | 2026-11-08T00:02:44 | Preço aplicado; rascunho |
| 21 | Poedagar Machine | R$ 194,90 | R$ 194,90 | R$ 0,00 | [Página individual](https://lojaspoedagar.com.br/machine/p) | 2026-11-08T00:02:45 | Preço aplicado; rascunho |
| 22 | Poedagar Nautilus | R$ 189,90 | R$ 189,90 | R$ 0,00 | [Página individual](https://lojaspoedagar.com.br/relogio-poedagar-nautilus-azul/p) | 2026-11-08T00:02:45 | Preço aplicado; rascunho |
| 23 | Poedagar Signature | R$ 177,90 | R$ 177,90 | R$ 0,00 | [Página individual](https://lojaspoedagar.com.br/signature/p) | 2026-11-08T00:02:45 | Preço aplicado; rascunho |
| 24 | Poedagar Tempus | R$ 187,90 | R$ 187,90 | R$ 0,00 | [Página individual](https://lojaspoedagar.com.br/tempus/p) | 2026-11-08T00:02:45 | Preço aplicado; rascunho |

## Variantes, disponibilidade e aprovação

Foram consultadas 57 variantes dos modelos selecionados. O arquivo
[POEDAGAR_NEW_PRICE_VARIANTS.csv](POEDAGAR_NEW_PRICE_VARIANTS.csv) registra cada cor anunciada,
ID interno da fonte, SKU da fonte, preço proposto, disponibilidade, URL e horário.
O SKU repetido da fonte não foi tratado como referência do fabricante nem como SKU da VRAS.
Cor anunciada não confirma cor da caixa, mostrador ou pulseira separadamente.

Variantes indisponíveis na fonte: Relógio Poedagar Tempus Prata e Preta — out_of_stock.
O preço dessa variante foi consultado separadamente; a disponibilidade de venda precisa
ser confirmada pela própria VRAS. Nenhum estado de estoque externo foi copiado para a loja.

Antes da publicação: confirmar referência física do fabricante e a variante efetivamente vendida,
receber fotografias autorizadas correspondentes e confirmar a oferta VRAS. A aprovação dos valores
atuais já foi registrada por ID de variante; não constitui confirmação de estoque ou identidade física.
O servidor exige que o valor da aprovação corresponda ao preço de venda, além dos demais requisitos.
Marcar apenas `status: publicado` não torna um produto comprável.

## Fotografias e origem

Zero fotos e vídeos foram incorporados. Veja [POEDAGAR_NEW_MEDIA_PENDING.csv](POEDAGAR_NEW_MEDIA_PENDING.csv)
para os arquivos a solicitar por variante e os destinos `static/img/products/poedagar/<modelo>/`.
Os nomes de arquivos e ângulos são solicitações, não fotografias existentes.
Nenhuma imagem antiga dos IDs 1–12 foi associada aos novos IDs 13–24.
As páginas do site 1 registradas como candidatas continuam sem equivalência física confirmada;
não se transferem fotos, variantes ou especificações de um anúncio para outro por nome semelhante.

Consulta completa: 2026-11-07T23:58:43.179133+00:00. Evidência: `data/poedagar_sources.json`.
Regerar este relatório: `python scripts/report_poedagar_migration.py`, após atualizar a pesquisa
com `python scripts/review_poedagar.py --refresh`. Nenhum dos comandos aprova preços.
