# Correspondência e inspeção do catálogo VRAS

**Registro histórico anterior à substituição.** Os 12 produtos descritos abaixo
foram retirados do catálogo ativo e arquivados em
`data/backups/catalog-before-poedagar-91f8988/`. A migração para os IDs 13–24 está
documentada em [POEDAGAR_MIGRATION.md](POEDAGAR_MIGRATION.md).

Inspeção em 07/11/2026, branch `main`. Foram lidos os 12 registros de
`data/products.json`, o manifesto de mídia e o inventário de 580 arquivos locais.
Foram vistas as 12 capas e uma folha de contato de 71 grupos de nomes de arquivos
raster (agrupando sufixos de resolução). Essa triagem não certifica originalidade
nem identidade de todas as imagens do arquivo. Folhas de contato locais em
`artifacts/visual/contact-sheets/catalog-contact-sheet.jpg` e `artifacts/visual/contact-sheets/archive-contact-sheet.jpg`,
ignoradas pelo Git e não publicadas pela loja.

## Tabela de correspondência

As observações abaixo descrevem o que se vê nos arquivos de referência legados;
não são especificações do produto VRAS nem comprovação da sua autenticidade.
As capas continuam preservadas no disco e no campo `imagem`, sem concessão de licença.

| ID / produto | Observação da capa local | Modelo Poedagar / variante | Origem da imagem | Preço VRAS | Referência site 2 |
| --- | --- | --- | --- | --- | --- |
| 1 — Vras Flyback 42mm | Mostrador VOXO, pulseira cinza | Não correspondidos | `41_1200x.webp`, arquivo legado; autorização pendente | R$ 359,00 | Não confirmado |
| 2 — Vras Genius 42mm | Inscrição Genius, caixa rosada e pulseira cinza; a descrição local menciona verde | Não correspondidos | `0be87f4f-f1d0-4858-b062-1c7c756e4075_1200x.png`, legado; autorização pendente | R$ 389,00 | Não confirmado |
| 3 — Vras Imperium 41mm | Inscrição LONG... no mostrador, visual claro, pulseira marrom | Não correspondidos | `Imperium_1200x.jpg`, legado; autorização pendente | R$ 589,00 | Não confirmado |
| 4 — Vras Winner 40mm | Inscrição Winner, mostrador preto, pulseira preta | Não correspondidos | `FotosPNGTOP_bd9537fc-04bb-4d0c-ab13-ca227d7b784e_1200x.png`, legado; autorização pendente | R$ 529,00 | Não confirmado |
| 5 — Vras Legacy 42mm | Mostrador claro com submostradores e pulseira marrom | Não correspondidos | `1_9eff571c-24cd-4281-b16d-c43038dea5ac_1200x.png`, legado; autorização pendente | R$ 389,00 | Não confirmado |
| 6 — Vras Cadence 39mm | Mostrador claro, inscrição alada, pulseira marrom | Não correspondidos | `43_cd351668-10cd-411d-b375-ac05281c4c42_1200x.jpg`, legado; autorização pendente | R$ 369,00 | Não confirmado |
| 7 — Vras Navigator 42mm | Relógio azul no pulso, pulseira azul | Não correspondidos | `Navigator_768x.png`, legado; autorização pendente | R$ 449,00 | Não confirmado |
| 8 — Vras Dominus 40mm | Inscrição CURREN, mostrador preto, caixa dourada, pulseira preta | Não correspondidos; nome Dominus não comprova ser Poedagar | `Dominus_1200x.jpg`, legado; autorização pendente | R$ 429,00 | Não confirmado |
| 9 — Vras Monarch 40mm | Mostrador azul, caixa quadrangular, pulseira preta | Não correspondidos | `88_fbbced28-dfa4-4ef6-ba7d-961bc3338663_1200x.jpg`, legado; autorização pendente | R$ 479,00 | Não confirmado |
| 10 — Vras Palazzo 40mm | Arquivo nomeado Gemini_Generated_Image, relógio no pulso | Não correspondidos; não usar como foto real | `Gemini_Generated_Image_kqspgxkqspgxkqsp_1200x.png`, legado; origem sintética indicada pelo nome, não certificada | R$ 459,00 | Não confirmado |
| 11 — Vras Megir 42mm | Inscrição MEGIR, mostrador e pulseira azuis | Não correspondidos | `128_667d1500-87fc-497a-bad6-93746f7d9e7c_1200x.jpg`, legado; autorização pendente | R$ 399,00 | Não confirmado |
| 12 — Vras Berny 38mm | Inscrição BERNY, mostrador claro e pulseira preta | Não correspondidos | `50_4c9ee022-801b-49a0-ac53-aec57125b2c9_1200x.jpg`, legado; autorização pendente | R$ 329,00 | Não confirmado |

Os 12 produtos foram preservados: IDs, nomes, preços, descrições, categorias,
destaques e nomes dos arquivos de imagem. Não foram criados produtos, variantes,
estoques ou dimensões. Foi adicionada uma revisão interna com identificação
pendente; isso não aparece como informação técnica na vitrine. Eventuais dados
legados, inclusive os diâmetros nos nomes, não foram verificados nesta pesquisa.

## Fontes externas

Os [preços e candidatos entre sites](POEDAGAR_PRICES.md) ficam em relatório separado.
A consulta identificou 18 anúncios masculinos do site 2 e 82 variantes da fonte.
Dez páginas do site 1 foram analisadas como candidatas por nome. Nenhuma das dez
recebeu confirmação de equivalência por referência de fabricante; não é seguro
transpor automaticamente cores, pulseiras, materiais ou preços entre os sites.
Os outros oito anúncios não receberam candidato do site 1 nesta triagem.

Zero Poedagar confirmados entre os produtos VRAS; zero fotografias autorizadas
recebidas/incorporadas. A informação que falta é a relação real dos produtos
vendidos pela VRAS com referências de fabricante, fotos da caixa/mostrador/verso,
variantes e originais autorizados do fornecedor. Todos os 18 anúncios da pesquisa
e os 12 produtos legados continuam com pendência de fotos para uso nessa atualização.

## Cadastro de identidade, variantes e especificações

O contrato em `loja/catalog/validation.py` exige identificação com `confirmada: true`,
`marca`, `modelo`, `referencia` e `fonte` HTTPS. Esse sinalizador registra uma
conferência humana; uma URL isoladamente não comprova um produto.

Cada combinação vendida de cor e pulseira tem seu próprio ID de produto, preço e
mídias. Para habilitar escolhas, cada registro precisa também de `variante` com
`confirmada: true`, `cor`, `pulseira` e `fonte` HTTPS. Só registros com a mesma marca,
modelo e referência confirmados se agrupam. Os links de opção abrem o detalhe do
SKU escolhido e funcionam sem JavaScript. O carrinho continua usando IDs e rotas
existentes; duas cores entram em linhas separadas. Não há seletor artificial nos
12 produtos sem confirmação. Não há campos de estoque inferidos das fontes.

`especificacoes` aceita um objeto por rótulo, com `valor` textual, `fonte` HTTPS e
`confirmada: true`. Por exemplo, um dado precisa ser conferido no manual/ficha
correspondente ao SKU real antes de ser marcado confirmado. Entradas sem evidência
permanecem no arquivo, mas não aparecem como especificação verificada. Não adicionar
resistência à água, material, mecanismo ou garantia apenas para preencher o detalhe.

## Aprovações restantes

1. Informar quais modelos/SKUs Poedagar a VRAS vende e a associação com IDs locais,
   ou autorizar o cadastro de novos SKUs com sua oferta real e variantes.
2. Fornecer originais e autorização comercial; lista em [POEDAGAR_MEDIA_PENDING.csv](POEDAGAR_MEDIA_PENDING.csv).
3. Confirmar especificações com manual ou ficha confiável por referência.
4. Aprovar uma comparação de preços por SKU após a associação exata. Os preços
   externos pesquisados não alteram o catálogo nem o carrinho.

O perfil [@usevras](https://www.instagram.com/usevras/) continua como destino oficial
indicado pelo proprietário. Não foram copiados posts ou importada uma identidade
visual concorrente. A vitrine mantém preto, grafite, branco e o detalhe dourado existente.
