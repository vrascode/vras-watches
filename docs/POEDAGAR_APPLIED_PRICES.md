# Preços Poedagar aprovados e aplicados

Entrada: `main`, HEAD `6a8fb02`, checkout limpo. O proprietário autorizou
expressamente aplicar os preços atuais dos 12 modelos, desde que correspondessem
ao modelo/variante e não fossem preços condicionados. Essa autorização foi
executada no catálogo; os valores abaixo não são apenas uma proposta.

## Valores gravados

Consulta específica concluída em **08/11/2026 às 00:02:46 UTC**, equivalente a
**07/11/2026 às 21:02:46 em America/Sao_Paulo**. Os horários de cada página, hashes
e campos de pagamento estão em `data/poedagar_price_verification.json`.

| ID VRAS | Modelo e página de origem | Antes em `preco` | Preço de venda aplicado |
| --- | --- | --- | --- |
| 13 | [Army](https://lojaspoedagar.com.br/army/p) | `null` | R$ 196,92 |
| 14 | [Deluxe](https://lojaspoedagar.com.br/deluxe/p) | `null` | R$ 199,90 |
| 15 | [Deluxe Golden](https://lojaspoedagar.com.br/deluxe-golden/p) | `null` | R$ 194,90 |
| 16 | [Golden Mars](https://lojaspoedagar.com.br/golden-mars/p) | `null` | R$ 197,90 |
| 17 | [Golden Moon](https://lojaspoedagar.com.br/golden-moon/p) | `null` | R$ 197,20 |
| 18 | [Golden Neptune](https://lojaspoedagar.com.br/neptune/p) | `null` | R$ 197,40 |
| 19 | [Golden Star](https://lojaspoedagar.com.br/golden-star/p) | `null` | R$ 179,90 |
| 20 | [King Royal](https://lojaspoedagar.com.br/king-royal/p) | `null` | R$ 219,90 |
| 21 | [Machine](https://lojaspoedagar.com.br/machine/p) | `null` | R$ 194,90 |
| 22 | [Nautilus](https://lojaspoedagar.com.br/relogio-poedagar-nautilus-azul/p) | `null` | R$ 189,90 |
| 23 | [Signature](https://lojaspoedagar.com.br/signature/p) | `null` | R$ 177,90 |
| 24 | [Tempus](https://lojaspoedagar.com.br/tempus/p) | `null` | R$ 187,90 |

Os valores coincidem com a pesquisa anterior, mas foram novamente confirmados
antes da aplicação. Todas as 57 variantes anunciadas desses modelos tiveram seus
IDs, títulos e preços conferidos. Cada modelo tem preço unitário uniforme entre
as variantes consultadas. Não foi escolhida uma cor arbitrariamente nem alterada
a variante física da oferta VRAS, que continua pendente de confirmação.

## Condições verificadas na fonte

- Foi usado o campo público `skus.data[].prices.data.price`, em reais, por SKU.
- O valor coincide com `price_discount`, o preço unitário anunciado atualmente,
  e com boleto sem desconto adicional. A fonte marca uma promoção própria sobre
  seu preço anterior, que não foi copiado como preço anterior da VRAS.
- Pix aparece separado com 5% de desconto nos 57 registros. Esses valores menores
  não foram adotados como preço normal da VRAS.
- Não foi inserido cupom nem selecionada quantidade mínima. Nenhuma condição de
  cupom ou quantidade foi identificada no campo de preço unitário consultado.
  Não foi calculada uma parcela mensal nem prometido parcelamento na VRAS.
- Não foram criados selos, porcentagens de desconto ou valores “de/por”.

Tempus “Prata e Preta” permanece `out_of_stock` na fonte. Seu valor cadastrado foi
identificado, mas a aprovação do preço não comprova estoque ou disponibilidade de
venda da VRAS. Nenhuma variante da fonte foi ativada automaticamente na loja.

## Aplicação e vinculação por variante

`data/products.json` recebeu os 12 preços numéricos. `aprovacao_preco` registra
autorização expressa do proprietário, data local, valor em formato de centavos,
URL e horário da consulta. O mapa `variantes` registra separadamente os 57 IDs de
variante, título, preço aprovado e URL da fonte. O SKU repetido da loja fonte não
é usado como referência física de fabricante.

O validador aceita a aprovação completa de um modelo sem escolher uma variante
somente se a cobertura dos IDs for exata e todos tiverem o mesmo valor. Depois
que a variante física é escolhida, exige a aprovação daquele ID e o mesmo preço.
Uma variante desconhecida ou um preço diferente continua bloqueado. Aprovação
sem variante selecionada e sem mapa explícito não é aceita como aprovação genérica.

A pendência de aprovação de preço foi retirada dos 12 registros, e o código
`preco_sem_aprovacao_correspondente` não aparece mais entre as pendências deles.
Todos os demais requisitos de publicação continuam ativos. Não foram modificados
nome/modelo, referência, identidade física, fotografias, descrição/especificações,
variante efetivamente vendida ou confirmação de disponibilidade da oferta.

Cards, detalhes e carrinho continuam usando a mesma fonte de preço do catálogo
com Decimal; não há cópia independente de preço em JavaScript. O carrinho ignora
preços enviados pelo cliente e calcula os subtotais no servidor.

## Publicação e fotografias

**Publicados: zero. Rascunhos: todos os IDs 13–24.** O motivo restante é ausência
de referência física/variante confirmada, foto autorizada correspondente e
confirmação da oferta VRAS. A autorização de preços foi atendida e não precisa ser
confundida com autorização ou identificação de fotografias.

Foram novamente verificadas `midias-instagram/` e
`static/img/products/poedagar/`: existem apenas instruções e manifestos pendentes,
sem fotografias ou vídeos fornecidos. A execução de `import_store_media --apply`
ignorou 12 entradas não autorizadas e importou zero arquivos. O manifesto público
`data/media.json` ficou inalterado. Nenhuma imagem antiga ou de IA foi usada.

A lista exata continua em [POEDAGAR_NEW_MEDIA_PENDING.csv](POEDAGAR_NEW_MEDIA_PENDING.csv),
com modelos, IDs de variante e destinos por diretório. Para cada variante que a
VRAS realmente vender, receber foto frontal original autorizada, identificação
de marca/modelo/referência e cores/pulseira, confirmação da oferta e comprovação
de uso comercial. Lateral/verso e vídeo são opcionais quando existirem; vídeo
exige poster autorizado e legendas quando houver fala.

O aplicador publica somente registros cujos outros requisitos já estejam todos
cumpridos. Nesta execução nenhum estava pronto; não houve relaxamento de checagens
de mídia, identidade ou disponibilidade para forçar publicação.

## Testes e evidências

- `python manage.py check`: sem problemas.
- `python manage.py test`: suite padrão passou; execução completa com
  `VRAS_BROWSER_QA=1` e Chrome isolado: **113 testes passaram**.
- Verificação independente dos 12 valores contra o snapshot e da aprovação de
  cada uma das 57 variantes; preços Pix não substituem o preço unitário.
- Oferta fictícia isolada: preços atuais nos 12 cards e detalhes, quantidades e
  subtotais do carrinho, soma total, centavos e tentativa de enviar preço falso.
  As fixtures nunca modificam produtos ou mídias de produção.
- Validados modelo/variante errados, cupom/quantidade, preço Pix, preços diferentes
  entre variantes, aprovação sem ID válido, aplicação parcial, simulação e
  rejeição de consulta com mais de 24 horas para nova aplicação.
- Aplicador com oferta fictícia pronta: publica apenas quando preço, foto,
  identidade, variante e disponibilidade já estiverem confirmados. Ofertas
  incompletas continuam em rascunho após aprovação do preço.
- Navegador no servidor 8001: 15 screenshots em cinco larguras de 360 a 1440 px;
  menu mobile, busca/filtros, redirecionamentos e proteção dos 12 rascunhos. Nenhum
  preço de rascunho vazou para a vitrine, busca ou detalhes públicos.
- Galeria, seleção de variantes, zoom e fluxo de carrinho validados com servidor
  isolado e arquivos temporários. Não houve erro inesperado de JavaScript/rede.
- `audit_storefront`: 12 produtos, 12 rascunhos, 580 mídias locais, zero arquivos
  aprovados ou posts. Sintaxe dos scripts JavaScript e whitespace verificados.

Relatórios locais em `artifacts/migration-browser-report.json` e
`artifacts/gallery-browser-report.json`, ignorados pelo Git. Não foram validados
aparelhos físicos ou reprodução de vídeos reais, pois não há mídias autorizadas.

## Arquivos e commits

| Grupo | Arquivos principais |
| --- | --- |
| Verificação | `scripts/verify_poedagar_prices.py`, `data/poedagar_price_verification.json`, `data/poedagar_sources.json` |
| Preços e regras | `data/products.json`, `loja/pricing.py`, `loja/services.py`, `loja/management/commands/apply_reference_prices.py` |
| Testes | `loja/test_approved_prices.py`, `loja/test_catalog_migration.py` |
| Relatórios | `scripts/review_poedagar.py`, `scripts/report_poedagar_migration.py`, `docs/POEDAGAR_PRICES.md`, `POEDAGAR_PRICES.csv`, `POEDAGAR_COMPARISON.csv`, `POEDAGAR_VARIANT_IDENTITY.csv`, `POEDAGAR_NEW_PRICES.md`, `POEDAGAR_NEW_PRICE_VARIANTS.csv` |
| Instruções | `README.md`, `docs/POEDAGAR_MIGRATION.md`, este relatório |

- `0e8f6fd` — `feat: verify current Poedagar unit prices and payment conditions`
- `54015ac` — `feat: apply approved Poedagar prices with exact variant bindings`
- Documentação — `docs: record applied Poedagar prices and remaining release requirements`

Nenhum push ou alteração de pedidos históricos foi executado. O servidor local
existente permanece em `http://127.0.0.1:8001/`.

## Operação do verificador

`python scripts/verify_poedagar_prices.py` consulta somente metadados públicos e
registra preços/condições, sem alterar o catálogo nem obter autorizações.
`python manage.py apply_reference_prices --approval-record "REGISTRO REAL"`
simula uma aplicação com uma autorização explicitamente informada; `--apply`
grava os preços e publica somente ofertas completas. A consulta precisa ser recente.
O comando não cria autorização por conta própria e não executa `git push`.
