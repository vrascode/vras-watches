# Substituição do catálogo VRAS por Poedagar

**Registro da etapa anterior à aprovação comercial.** Os 12 preços foram
posteriormente autorizados, conferidos e gravados conforme
[POEDAGAR_APPLIED_PRICES.md](POEDAGAR_APPLIED_PRICES.md). Os produtos continuam
em rascunho pelos requisitos restantes de identidade, mídia e oferta.

Execução em 07/11/2026. Entrada: `main`, HEAD `91f8988`, checkout limpo.
O catálogo ativo foi substituído por 12 registros novos Poedagar. **Todos os 12
estão em rascunho, sem preço de venda; zero ofertas foram publicadas.** Faltam
referências físicas, variantes efetivamente vendidas, mídias autorizadas e
aprovação comercial. A loja apresenta a coleção em preparação, sem os relógios
antigos e sem expor preços propostos. Não houve push nem deploy.

## Modelos selecionados e verificação

Os 12 nomes desejados continuam anunciados nas páginas individuais do site 2,
com ao menos uma variante indicada como disponível por modelo na consulta.
Não foi necessário substituir algum modelo da seleção. São nomes comerciais
da fonte; referências oficiais do fabricante não foram confirmadas.

| ID interno VRAS | Modelo comercial | Variantes anunciadas | Estado |
| --- | --- | --- | --- |
| 13 | Poedagar Army | 5 | Rascunho |
| 14 | Poedagar Deluxe | 4 | Rascunho |
| 15 | Poedagar Deluxe Golden | 2 | Rascunho |
| 16 | Poedagar Golden Mars | 3 | Rascunho |
| 17 | Poedagar Golden Moon | 5 | Rascunho |
| 18 | Poedagar Golden Neptune | 6 | Rascunho |
| 19 | Poedagar Golden Star | 6 | Rascunho |
| 20 | Poedagar King Royal | 7 | Rascunho |
| 21 | Poedagar Machine | 3 | Rascunho |
| 22 | Poedagar Nautilus | 4 | Rascunho |
| 23 | Poedagar Signature | 4 | Rascunho |
| 24 | Poedagar Tempus | 8 | Rascunho |

Foram registradas 57 variantes da fonte nesses anúncios; 56 indicavam disponibilidade.
Tempus “Prata e Preta” estava `out_of_stock`. Isso não representa estoque nem cores
disponíveis na VRAS. Rótulos como “Azul” não confirmam separadamente a cor da caixa,
mostrador e pulseira. `variante` continua nula até confirmação física.

A consulta geral do site 2 abrangeu 18 anúncios, e dez páginas do site 1 foram
reconsultadas como candidatos por nome. Sete dos 12 selecionados têm candidato
registrado no site 1; cinco não têm equivalência registrada. Nenhuma equivalência
física entre as lojas foi inferida. Preços e identidade comercial vêm das páginas
individuais do site 2, com horários e hashes em `data/poedagar_sources.json`.

## O que foi retirado e como foi preservado

Saíram do catálogo ativo os IDs 1–12: Flyback, Genius, Imperium, Winner, Legacy,
Cadence, Navigator, Dominus, Monarch, Palazzo, Megir e Berny. Nenhum desses nomes,
preços, diâmetros ou arquivos de imagem foi reutilizado como dado do novo relógio.
As descrições Poedagar são novas e não afirmam material, movimento, resistência,
garantia, dimensões, vendas, avaliações ou estoque não verificados.

Backup versionado antes da substituição:
`data/backups/catalog-before-poedagar-91f8988/{products.json,media.json,backup.json}`.
Os hashes SHA-256 registram os bytes originais dos dois arquivos. `.gitattributes`
preserva os bytes dos snapshots entre checkouts, inclusive finais de linha.
O inventário e os 580 arquivos visuais legados permanecem preservados no disco.

IDs 13–24 são identificadores internos novos, não SKUs de fabricante inventados.
Não há uma correspondência entre antigo ID 1 e novo ID 13, por exemplo: trata-se
de troca da seleção inteira. IDs aposentados não podem voltar como outro produto.
`data/catalog_migration.json` documenta geração, IDs e política da migração.

## Carrinho e rotas

- A geração atual é `poedagar-v1`. Ao acessar uma sessão com carrinho de geração
  anterior, somente o carrinho é limpo e o visitante recebe um aviso. A sessão
  mantém autenticação e outros dados; não há limpeza global do banco.
- Itens de produtos retirados, em rascunho ou cuja aprovação foi retirada também
  são removidos da sessão com aviso. Subtotais usam apenas preços aprovados de
  produtos publicados, com Decimal e validação no servidor.
- Links antigos `/produto/1/` a `/produto/12/` redirecionam para `/produtos/`, com
  mensagem. Não abrem outro relógio silenciosamente. As rotas Django continuam iguais.
- Detalhes dos novos IDs retornam 404 enquanto estiverem em rascunho. Não há links
  públicos para eles, nem presença em busca, cards, relacionados ou sitemap.
- POST direto não permite adicionar nem definir quantidade de produto aposentado
  ou rascunho. Preço enviado pelo navegador não altera o total.
- Não foram alterados pedidos históricos, registros de clientes ou autenticação.
  O projeto não possui modelo de pedido nem checkout/gateway implementado.

## Bloqueio de publicação e aprovação de preço

O servidor exige todos os requisitos abaixo, mesmo que alguém marque
`status: publicado` manualmente. A auditoria sinaliza publicação incompleta e a
vitrine oculta essa oferta enquanto houver pendências.

1. `marca`, `modelo` e `referencia` coerentes com `identificacao`, confirmados com
   fonte confiável. Não preencher referência usando o SKU interno repetido da loja fonte.
2. `variante` confirmada, com cor, pulseira, fonte e `source_variant_id` presente
   em `variantes_fonte`. Esse ID identifica a variante anunciada na loja fonte,
   não certifica a referência física do fabricante.
3. `oferta_confirmada: true` após confirmar que a VRAS realmente oferece esse SKU.
   Não se infere uma contagem de estoque ou disponibilidade VRAS da concorrência.
4. `preco` com valor aprovado; `aprovacao_preco` precisa de `aprovado: true`, `valor`
   exato, `data` ISO, `registro` da aprovação do proprietário e `source_variant_id`
   correspondente. Uma aprovação antiga não autoriza outro preço ou variante.
5. Capa, fotografias, vídeos e posters aprovados, locais e associados ao mesmo
   produto, modelo, geração e variante. Uma capa correta não permite fotos de
   outra variante no restante da galeria.

Valores propostos por modelo e variante, com URL/data e comparação com a pesquisa
anterior, estão em [POEDAGAR_NEW_PRICES.md](POEDAGAR_NEW_PRICES.md) e
[POEDAGAR_NEW_PRICE_VARIANTS.csv](POEDAGAR_NEW_PRICE_VARIANTS.csv). Os preços atuais
da consulta coincidem com os valores do briefing; a diferença é R$ 0,00 em todos
os 12 anúncios. Isso não é comparação entre os antigos VRAS e os novos Poedagar.
Nenhum `preco` novo foi publicado: todos continuam nulos.

## Fotografias, vídeos e arquivos necessários

**Zero fotografias e zero vídeos incorporados.** A pasta `midias-instagram` não
continha arquivos de mídia nem comprovações. Nenhuma imagem de concorrente foi
baixada, copiada, rebatizada ou usada como hotlink. Nenhuma imagem artificial foi criada.

Foram preparados os diretórios por modelo em `static/img/products/poedagar/`, com
README em cada um. As galerias estão preparadas para arquivos reais, não preenchidas.
O arquivo [POEDAGAR_NEW_MEDIA_PENDING.csv](POEDAGAR_NEW_MEDIA_PENDING.csv) contém
57 linhas por variante da fonte: ID/modelo VRAS, variante anunciada, ID da fonte,
página de consulta, nome sugerido para foto frontal, lateral/verso opcionais e
destino. Os nomes/ângulos são solicitações, não arquivos ou fotos existentes.

Solicitar para cada variante que a VRAS realmente vender:

- Foto frontal original nítida, sem distorção, com o relógio/variante corretos.
  Fotos laterais e do verso são opcionais, quando existirem; o verso e a ficha
  do fornecedor ajudam a conferir a referência física.
- Marca/modelo, referência de fabricante, SKU real do fornecedor quando houver,
  cor de caixa/mostrador/pulseira e tipo de pulseira. Se desconhecido, registrar
  como pendente, sem deduzir por aparência ou nome comercial.
- Autoria e permissão para uso comercial na VRAS, com comprovante/referência
  documental. Direitos do site de referência não foram presumidos.
- Vídeo real opcional, já otimizado para web, poster autorizado da mesma variante
  e legendas WebVTT quando houver fala. Não houve transcodificação nesta execução.
- Para o hero/editorial: foto/vídeo real autorizado do modelo ou marca, com
  enquadramento desktop/mobile. Para Instagram: original e permalink verdadeiro.

O `manifest.json` local contém 12 entradas pendentes, com `autorizado: false`,
`produto_confirmado: false` e `variante_fonte_id: null`; não foi versionado por conter
o fluxo local de recebimento. O exemplo versionado foi atualizado para o novo ID 13.
`import_store_media --apply` ignorou as 12 entradas não autorizadas e criou zero
arquivos. `data/media.json` ficou inalterado.

O importador agora exige `variante_fonte_id` válido no catálogo Poedagar e grava
os vínculos no arquivo de mídia e no poster de vídeo. Continua gerando WebP
responsivo sem alterar originais e sem remover marcas d'água. Importar fotos não
aprova preços, referências ou disponibilidade de oferta automaticamente.

## Interface e identidade

A marca permanece VRAS Watches. Hero tipográfico, paleta e navegação premium foram
mantidos. A home e a listagem indicam a coleção Poedagar em preparação, sem anúncios
compráveis ou preços fictícios. Não há classificações não comprovadas de material,
clássico/esportivo ou lançamento nos novos registros; a categoria inicial é Poedagar.
A seção “VRAS WATCHES — NOSSO ESTILO” continua presente, sem publicações inventadas.
Cards, detalhes, zoom, variantes, galeria por toque e carrinho permanecem preparados
para ofertas que passem nas regras de publicação.

## Testes e validação

- `python manage.py check`: sem problemas.
- Suite completa com Chrome isolado e `VRAS_BROWSER_QA=1`: **100 testes passaram**.
  Inclui regressões anteriores com fixture do catálogo arquivado, sem ativá-lo
  na produção, e testes novos sem mock dos bloqueios de publicação.
- Verificados 12 IDs/nomes/slugs únicos, backup e hashes, ausência de imagens
  legadas e preço de venda, proteção de rascunhos e sitemap, redirecionamentos,
  reconciliação de sessão com aviso e preservação de dados alheios ao carrinho.
- Testes com oferta completa fictícia, apenas em arquivos temporários: preço
  aprovado e total corretos, retirada de aprovação, referência divergente,
  variante errada, foto errada, foto secundária incompatível e ID aposentado.
- Importador: exige a variante anunciada e mantém a vinculação ao modelo correto.
- `audit_storefront`: 12 produtos, 12 IDs únicos, 12 rascunhos, 580 mídias locais,
  zero arquivos aprovados e zero posts. Nenhuma foto de teste permaneceu publicada.
- QA real do servidor 8001: home/listagem/carrinho em cinco larguras de 360 a
  1440 px, 15 screenshots. Pesquisa/filtro/ordenação, menu mobile e foco passaram;
  12 URLs aposentadas redirecionaram e os 12 rascunhos ficaram protegidos.
  As 404 dos rascunhos são intencionais, sem outros erros de rede ou JavaScript.
- Galerias, variantes, zoom e compra foram verificados no navegador com fixtures
  isoladas; isso não significa que as fotos reais já foram recebidas.
- `node --check` para scripts e `git diff --check`: válidos. Atributos dos backups
  mantêm CRLF original sem tratá-lo como espaço incorreto.

Não foram testados dispositivos físicos ou outros motores de navegador. Fotos e
vídeos reais não podem ser validados sem os originais aprovados. Evidências locais:
`artifacts/browser/migration/runs/pre-organization/reports/migration-browser-report.json`, `artifacts/browser/gallery/runs/pre-organization/reports/gallery-browser-report.json`
e screenshots da migração, ignorados pelo Git.

## Arquivos e commits

| Grupo | Arquivos |
| --- | --- |
| Backup | `.gitattributes`, `data/backups/catalog-before-poedagar-91f8988/products.json`, `media.json`, `backup.json` |
| Catálogo | `data/products.json`, `data/catalog_migration.json`, `data/poedagar_sources.json` |
| Django | `loja/services.py`, `loja/views.py`, `loja/context_processors.py`, `loja/media_import.py`, `loja/management/commands/audit_storefront.py` |
| Interface | `loja/templates/loja/base.html`, `_product_card.html`, `home.html`, `product_detail.html`, `products.html`, `static/css/premium.css` |
| Testes | `loja/testing_catalog.py`, `loja/test_catalog_migration.py`, `loja/tests.py`, `loja/test_poedagar.py`, `loja/test_storefront_update.py`, `loja/test_media_import.py`, `scripts/browser_qa.mjs` |
| Pesquisa/relatórios | `scripts/review_poedagar.py`, `scripts/report_poedagar_migration.py`, `docs/POEDAGAR_PRICES.md`, `POEDAGAR_PRICES.csv`, `POEDAGAR_COMPARISON.csv`, `POEDAGAR_VARIANT_IDENTITY.csv`, `POEDAGAR_NEW_PRICES.md`, `POEDAGAR_NEW_PRICE_VARIANTS.csv`, `POEDAGAR_NEW_MEDIA_PENDING.csv` |
| Instruções | `README.md`, `docs/POEDAGAR_CATALOG.md`, `docs/STOREFRONT_UPDATE.md`, este relatório, `midias-instagram/README.md`, `midias-instagram/manifest.example.json`, 12 READMEs nos diretórios dos modelos |

Commits locais:

- `9482b80` — `chore: backup previous VRAS watch catalog`
- `be68490` — `feat: migrate Poedagar drafts and reconcile legacy carts`
- `cf344c0` — `feat: present pending Poedagar collection and validate public routes`
- Documentação/propostas — `docs: document Poedagar migration prices and release requirements`

Nenhum histórico foi apagado e nenhum commit vazio ou push foi criado.

## Próximas decisões do proprietário

Confirmar referências e variantes que a VRAS realmente oferece, fornecer mídias
autorizadas e aprovar o valor exato por SKU. Somente depois preencher os registros
de confirmação/aprovação, importar a galeria correspondente, publicar e auditar.
Push/publicação remota continuam dependendo de autorização explícita.

```powershell
python -m pip install -r requirements.txt
python manage.py check
python manage.py runserver 127.0.0.1:8001
```

O servidor local existente foi preservado e já apresenta o catálogo em preparação.
