# Entrega da atualização Poedagar — 07/11/2026

Este documento registra a etapa anterior, até `93e8963`. A continuação a partir
de `0837dfd`, com importador de mídia, novas vitrines e galeria ampliada, está em
[STOREFRONT_UPDATE.md](STOREFRONT_UPDATE.md).

Foram concluídas a pesquisa pública, a revisão do catálogo, as melhorias possíveis
na vitrine Django e as verificações locais. A inclusão dos produtos Poedagar reais
continua dependente da identificação dos SKUs da VRAS e de fotografias autorizadas.
Não foram publicados preços externos, imagens de concorrentes ou especificações
novas sem confirmação. Não houve push ou deploy.

## 1. Modelos identificados nas fontes

18 anúncios/modelos comerciais masculinos no site 2, com 82 variantes cadastradas.
Dez páginas do site 1 foram consultadas como candidatos por nome. Esses nomes não
comprovam 18 referências distintas do fabricante nem equivalência entre as lojas.
O snapshot em `data/poedagar_sources.json` registra URLs, data/hora individual,
hashes SHA-256 do HTML e URLs de imagens apenas para consulta.

## 2. Produtos já existentes

12 registros VRAS inspecionados. Zero correspondências Poedagar confirmadas entre
eles. Todos foram preservados, com IDs, nomes, preços, descrições, categorias,
destaques e referências legadas de imagem iguais aos da entrada desta tarefa.
Foram adicionados apenas campos internos de revisão e identificação pendente.
Isso não afirma que a loja não venda Poedagar: faltam dados que permitam associar
essa oferta aos cadastros atuais. Veja a [tabela de correspondência](POEDAGAR_CATALOG.md).

## 3. Imagens autorizadas incorporadas

Zero. O manifesto não continha fotos aprovadas e não foram recebidos originais ou
licenças. Os 580 arquivos visuais legados continuam preservados. As 12 capas foram
vistas individualmente/por folha de contato, além de uma triagem visual de 71
grupos de nomes raster. Existem outras marcas visíveis e arquivos nomeados
`Gemini_Generated_Image_*`; não foram reapresentados como fotografias Poedagar reais.

`static/img/products/poedagar/` foi preparado com instruções de organização, formatos
e procedência. O diretório contém somente README; nenhuma imagem artificial ou
fotografia de terceiro foi incluída. As imagens temporárias dos testes são blocos
de cor, não relógios; foram removidas e nunca fizeram parte do manifesto publicado.

## 4. Modelos que precisam de fotografias

Todos os modelos pesquisados: Army, Deluxe, Deluxe Golden, Deluxe Ice, Deluxe Old,
Golden Mars, Golden Moon, Golden Neptune, Golden Star, King Royal, Lattitude,
Legítimu's, Machine, Nautilus, Signature, Signature Vibe, Tempus e Universy.
Também permanecem pendentes fotos autorizadas dos 12 cadastros VRAS preservados.

A [lista de arquivos pendentes](POEDAGAR_MEDIA_PENDING.csv) tem 82 linhas, por
variante da fonte, com URLs para revisão e destinos sugeridos de frente, lateral
e verso. Não presume que esses ângulos existam nem que a VRAS venda todas as
variantes. Receber referência de fabricante, confirmação de cor/pulseira e
autorização comercial antes de cadastrar ou transformar arquivos em WebP/AVIF.

## 5. Tabela de preços e comparação

Veja a [tabela dos 18 anúncios e comparação com os 12 preços VRAS](POEDAGAR_PRICES.md)
e o [CSV das 82 variantes](POEDAGAR_PRICES.csv). Fonte principal:
https://lojaspoedagar.com.br/masculinos?sort_by=best_sellers, com consulta individual
em 07/11/2026. Os preços são os valores de venda cadastrados no HTML público por
variante; valores condicionados de Pix estão separados no CSV e não foram adotados.
Nenhum preço principal veio do site 1.

Tempus “Prata e Preta” consta como `out_of_stock` na fonte. Seu preço cadastrado é
registrado apenas como evidência; não é uma proposta aplicável à VRAS. Nenhum
estado de estoque da fonte foi transferido para a loja.

## 6. Aprovação pendente

Os 18 preços de referência aguardam correspondência exata e aprovação do
proprietário. Não há uma substituição apta a ser aprovada por ID local ainda.
Depois de receber a associação real, apresentar preço atual, preço proposto,
diferença, modelo, variante, URL e data por SKU antes de modificar `preco`.
Todos os preços publicados atuais foram mantidos.

## 7. Arquivos alterados ou adicionados

| Grupo | Arquivos |
| --- | --- |
| Catálogo e pesquisa | `data/products.json`, `data/poedagar_sources.json`, `scripts/review_poedagar.py` |
| Serviços e views | `loja/services.py`, `loja/views.py` |
| Templates | `loja/templates/loja/_product_card.html`, `_product_gallery.html`, `cart.html`, `home.html`, `product_detail.html` |
| Vitrine | `static/css/premium.css`, `static/js/storefront.js` |
| Auditoria e testes | `loja/management/commands/audit_storefront.py`, `loja/test_poedagar.py`, `scripts/browser_qa.mjs` |
| Documentação | `README.md`, `docs/POEDAGAR_CATALOG.md`, `docs/POEDAGAR_PRICES.md`, `docs/POEDAGAR_PRICES.csv`, `docs/POEDAGAR_MEDIA_PENDING.csv`, `docs/POEDAGAR_DELIVERY.md`, `static/img/products/poedagar/README.md` |

O script não rastreado `scripts/collect_poedagar_sources.py` já existia na entrada
da tarefa. Foi preservado sem alterações e não incluído nos commits. O novo
`scripts/review_poedagar.py` é independente dele e reproduz a captura e os relatórios.

Cards em destaque maiores, tipografia ajustada e uma seção própria para os dois
produtos já classificados como lançamentos. Galeria com miniaturas, setas,
contador, Home/End, zoom e alinhamento ao redimensionar. Escolhas de cor/pulseira
apenas para identidades confirmadas, com preço e carrinho próprios por ID.
Especificações novas exigem confirmação e fonte; busca considera somente marca,
modelo, referência e variante confirmados. Todas as rotas existentes permanecem.

## 8. Verificações realizadas

- `python manage.py check`: sem problemas.
- `python manage.py audit_storefront`: 12 produtos, 12 IDs únicos, 580 mídias
  locais, zero arquivos aprovados, zero posts. Arquivos temporários de QA removidos.
- `python manage.py test --verbosity 1`, com `VRAS_BROWSER_QA=1` e Chrome isolado:
  **64 testes passaram**, incluindo 53 anteriores, dez novos testes de comportamento
  e um teste de navegador com servidor Django isolado e fixtures temporárias.
- `node --check static/js/storefront.js` e `node --check scripts/browser_qa.mjs`: válidos.
- QA da loja atual no Chrome: home, listagem, detalhe e carrinho em 360, 390, 768,
  1024 e 1440 px, com 20 screenshots. Também foram visitados todos os 12 detalhes.
  Pesquisa/ordenação, lançamentos, menu mobile, foco, Escape, adição AJAX,
  incremento/decremento/remoção no carrinho e movimento reduzido passaram.
  Nenhum erro de rede, JavaScript ou overflow foi identificado nessas verificações.
- QA de galeria com fixtures: imagens carregadas, setas, miniaturas, Home/End,
  zoom, Escape, restauração de foco e seleção mantida após redimensionamento.
  Seleção de variante navegou para o produto correto, mostrou seu preço e
  adicionou a variante correta ao carrinho. Larguras 360, 390 e 1440 px.
- Geração offline dos relatórios e coleta pública: 18 páginas de produto do site 2,
  dez candidatos do site 1, sem falhas de consulta. Zero fotografias baixadas.
- Comparação dos campos legados de `products.json` com o HEAD inicial: todos iguais.
- `git diff --check`: sem problemas de whitespace.

Evidências locais, ignoradas pelo Git: `artifacts/browser/storefront/runs/pre-organization/reports/browser-report.json`,
`artifacts/browser/gallery/runs/pre-organization/reports/gallery-browser-report.json`, screenshots e folhas de contato.
A qualidade de fotografias Poedagar reais ainda não pode ser validada, pois nenhuma
foi recebida/aprovada. Os testes de mídia comprovam o comportamento com fixtures,
sem certificar uma galeria real de produto. Não houve validação em dispositivos
físicos ou outros motores de navegador.

## 9. Commits locais

- `1c7509b` — `feat: map Poedagar product catalog and price references`
- `3c84af2` — `feat: improve watch galleries and confirmed variant selection`
- `edec58e` — `test: verify approved galleries variants and mobile storefront`
- Commit desta documentação — `docs: document Poedagar media price sources and delivery`

Os hashes completos constam em `git log`; o hash final da documentação é informado
na resposta de entrega. Nenhum commit vazio, push, merge remoto ou deploy foi executado.
