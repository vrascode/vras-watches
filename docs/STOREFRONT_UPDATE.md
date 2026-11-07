# Continuação VRAS Watches — 07/11/2026

**Etapa histórica antes da troca de catálogo.** A substituição posterior dos 12
produtos legados por 12 Poedagar em rascunho está em
[POEDAGAR_MIGRATION.md](POEDAGAR_MIGRATION.md).

Baseline confirmado antes das edições: `main`, HEAD `0837dfd`, checkout limpo.
Todos os commits anteriores foram preservados. O projeto continua em Django,
com as mesmas rotas, catálogo JSON e carrinho por sessão. Não houve push ou deploy.

## Melhorias implementadas no código

- Nova composição editorial do hero com “Seu tempo. Sua presença.”, tipografia
  local, CTA “Explorar coleção” e identidade em preto/grafite/off-white/dourado.
  O hero aceita foto desktop/mobile ou vídeo real autorizado com poster;
  a versão tipográfica continua quando não há mídia aprovada.
- Vitrines próprias para clássicos e esportivos, usando produtos existentes;
  destaques e lançamentos anteriores preservados. A categoria interna `Best Sellers`
  mantém filtros e dados, mas aparece como “Seleção VRAS”, sem alegar popularidade
  sem evidência de vendas. Nenhuma venda, avaliação ou estoque foi inventado.
- Seção “VRAS WATCHES — NOSSO ESTILO”, com galeria de fotos/Reels locais e links
  originais condicionados a mídias aprovadas. Sem publicações fictícias.
- Busca no cabeçalho e CTA de visualizar modelo nos cards; no toque, o CTA fica
  visível sem depender de hover. Barra de compra fixa no mobile, com preço do SKU,
  área segura de iPhone e a mesma rota de carrinho.
- Zoom ampliado com foto anterior/próxima, contador, teclado, ampliação 2x,
  rolagem de detalhes, Escape e restauração de foco. Galeria mantém swipe nativo,
  miniaturas, setas, Home/End, seleção ao redimensionar e movimento reduzido.
  Slides fora da seleção ficam `inert`, evitando foco em controles invisíveis.
- Fotografias responsivas via `srcset`/`sizes`, lazy loading, prioridade do banner
  e primeira foto, dimensões reservadas e posters de vídeo. Versão mobile do
  banner é escolhida por `<picture>`, com preload correspondente. O carregamento
  de vídeo interativo respeita economia de dados até interação do visitante.
- A home reutiliza um catálogo já carregado para destaques, lançamentos, coleções
  e vitrines por estilo, reduzindo leituras repetidas nesse fluxo.

## Importação de fotografias e vídeos

Foi implementado `loja/media_import.py` e o comando Django `import_store_media`.
Lê apenas arquivos locais descritos em `midias-instagram/manifest.json`, com ID,
origem, comprovante, texto alternativo e autorização explícita. Fotos de produto
exigem ID VRAS existente e confirmação da associação exata. Não identifica
fabricante por aparência nem muda preços, estoque ou especificações.

O lote é validado antes de escrever no catálogo de mídia. Por padrão há somente
simulação; `--apply` exporta WebP em até quatro larguras, aplica orientação EXIF,
preserva proporção/transparência e converte perfil de cor para sRGB. Não recorta,
amplia resolução, remove inscrições ou altera o original. Arquivos têm hash,
entradas são mescladas por ID e a gravação do manifesto usa substituição atômica.
Uma segunda importação do mesmo ID não duplica sua mídia.

Vídeos MP4/WebM já preparados para web são copiados com poster obrigatório e
legendas WebVTT opcionais. Não houve transcodificação: FFmpeg não está instalado.
Codec, áudio, direitos e qualidade precisam ser conferidos com os vídeos reais.
O comando não certifica uma autorização nem a autenticidade do relógio.
Comprovantes e originais ficam locais, fora do Git e do diretório público.

### Mídias efetivamente incorporadas

**Zero fotografias e zero vídeos reais.** `midias-instagram` estava vazia e o
manifesto não continha mídias aprovadas. Agora a pasta contém instruções e um
exemplo não autorizado, sem registros de publicações inventados. A consulta pública
ao Instagram retornou `Online fetch throttled`; não houve contorno de acesso.
Os 580 ativos legados foram preservados e mantêm seu estado anterior de aprovação.

O arquivo `data/media.json` não foi modificado. Nenhuma foto de concorrente foi
baixada/republicada. Imagens de teste são blocos de cor temporários e não representam
produtos. As fixtures e suas associações existem somente no servidor isolado do
teste e são removidas ao terminar. Não viraram arquivos publicados da loja.

## Modelos, identificação e preços

Nova consulta individual ao site de preços concluída em **2026-11-07T23:09:14 UTC**.
Foram encontrados 18 anúncios masculinos, 82 variantes e dez candidatos por nome
no site 1. Os preços continuam iguais à consulta anterior. Isso não comprova 18
referências distintas de fabricante ou equivalência entre as lojas.

| Modelo comercial no site 2 | Preço cadastrado por variante |
| --- | --- |
| Army | R$ 196,92 |
| Deluxe | R$ 199,90 |
| Deluxe Golden | R$ 194,90 |
| Deluxe Ice | R$ 187,90 |
| Deluxe Old | R$ 169,90 |
| Golden Mars | R$ 197,90 |
| Golden Moon | R$ 197,20 |
| Golden Neptune | R$ 197,40 |
| Golden Star | R$ 179,90 |
| King Royal | R$ 219,90 |
| Lattitude | R$ 194,90 |
| Legítimu's | R$ 173,90 |
| Machine | R$ 194,90 |
| Nautilus | R$ 189,90 |
| Signature | R$ 177,90 |
| Signature Vibe | R$ 299,90 |
| Tempus | R$ 187,90 |
| Universy | R$ 199,90 |

As URLs individuais e variantes estão em [POEDAGAR_PRICES.md](POEDAGAR_PRICES.md)
e [POEDAGAR_PRICES.csv](POEDAGAR_PRICES.csv). Valores Pix são condicionados e ficam
separados; não foram adotados como preço VRAS. Tempus “Prata e Preta” está
`out_of_stock` na fonte. Esse estado não foi copiado para a VRAS.

Nenhuma correspondência Poedagar foi confirmada entre os **12 cadastros VRAS**.
Todos continuam pendentes de identificação por referência e variante. O arquivo
completo `data/products.json` é igual ao do commit `0837dfd`, inclusive os preços.

O [CSV de comparação](POEDAGAR_COMPARISON.csv) e a tabela em
[POEDAGAR_PRICES.md](POEDAGAR_PRICES.md) contêm produto VRAS, modelo correspondente,
preço atual, preço de referência, diferença, URL e data. Os campos sem associação
segura ficam vazios/não confirmados; diferença não calculável não foi tratada como
zero. Todos os 18 preços de referência dependem de identificação e aprovação antes
de qualquer substituição de preço publicado.

O [inventário por variante](POEDAGAR_VARIANT_IDENTITY.csv) acrescenta marca
anunciada, modelo comercial, SKU/ID interno, referência do fabricante, rótulo de
cor, cor da caixa, cor/tipo de pulseira, quantidade de fotos e disponibilidade.
As referências do fabricante e atributos não comprovados ficam não confirmados;
“Azul” não foi reinterpretado como cor da caixa/pulseira. Fotografias necessárias
continuam listadas em [POEDAGAR_MEDIA_PENDING.csv](POEDAGAR_MEDIA_PENDING.csv).

## Arquivos desta continuação

| Grupo | Arquivos |
| --- | --- |
| Importação | `.gitignore`, `requirements.txt`, `loja/media.py`, `loja/media_import.py`, `loja/management/commands/import_store_media.py` |
| Serviços | `loja/services.py`, `loja/views.py` |
| Templates | `loja/templates/loja/_responsive_image.html`, `_product_card.html`, `_product_gallery.html`, `_video.html`, `base.html`, `home.html`, `product_detail.html`, `products.html` |
| Interface | `static/css/premium.css`, `static/js/storefront.js` |
| Pesquisa | `scripts/review_poedagar.py`, `data/poedagar_sources.json`, `docs/POEDAGAR_PRICES.md`, `docs/POEDAGAR_PRICES.csv`, `docs/POEDAGAR_COMPARISON.csv`, `docs/POEDAGAR_VARIANT_IDENTITY.csv` |
| Testes | `loja/test_media_import.py`, `loja/test_storefront_update.py`, `loja/test_poedagar.py`, `scripts/browser_qa.mjs` |
| Instruções | `README.md`, `midias-instagram/README.md`, `midias-instagram/manifest.example.json`, `static/img/products/poedagar/README.md`, `docs/POEDAGAR_DELIVERY.md`, `docs/STOREFRONT_UPDATE.md` |

Não foram alterados `data/products.json`, `data/media.json`, as rotas, o script
de coleta legado ou os arquivos de fotografia legados.

## Testes e limites

- `python manage.py check`: sem problemas.
- `python manage.py test`: suite padrão passou; o teste de navegador é opcional.
  Execução completa com `VRAS_BROWSER_QA=1` e Chrome isolado: **80 testes passaram**.
- `python manage.py audit_storefront`: 12 IDs únicos, 580 mídias locais, zero
  fotografias aprovadas/publicadas e zero posts.
- Importador: WebP responsivo, proporções/original preservados, autorização,
  associação por SKU, bloqueio de caminhos externos, simulação, lote inválido
  sem aplicação, idempotência, poster/legendas e preço intacto verificados.
- QA em `http://127.0.0.1:8001/`: 20 screenshots, home/listagem/detalhe/carrinho
  em 360, 390, 768, 1024 e 1440 px; todos os 12 detalhes visitados. Pesquisa,
  ordenação, menu, foco, Escape, carrinho AJAX e movimento reduzido passaram.
  Sem overflow, imagens quebradas, erros de rede ou JavaScript nesse escopo.
- QA isolado com fixtures: banner desktop/mobile, campanha, galeria social com
  link, swipe por eventos de toque, zoom com troca de foto e ampliação, slides
  inativos, compra fixa mobile, variante com foto/preço/carrinho próprios.
- `node --check` nos dois scripts JavaScript e `git diff --check`: sem problemas.
- Comparação integral do catálogo com `0837dfd`: igual. Servidor 8001 já apresenta
  a nova interface; o processo existente foi preservado.

O QA usa Chrome com larguras emuladas; não certifica Safari/iOS ou aparelhos físicos.
Fotos reais, reprodução de vídeos reais e métricas Core Web Vitals não puderam ser
validadas sem os arquivos aprovados. Não se alega uma galeria real já preenchida.
Relatórios locais: `artifacts/browser-report.json`, `artifacts/gallery-browser-report.json`
e screenshots; são ignorados pelo Git.

## Commits locais

- `7f30996` — `feat: import authorized store media with responsive WebP images`
- `fe9496f` — `feat: refine premium storefront and responsive product galleries`
- `bfb5d76` — `feat: expand Poedagar identity audit and price comparison`
- Documentação: `docs: document VRAS storefront update and authorized media workflow`

## Pendências e execução local

Receber fotografias/vídeos originais com autorização comercial e confirmar a
associação dos relógios com seus IDs VRAS. Confirmar referências, cores/pulseiras
e especificações com documentação confiável. Depois disso, apresentar e aprovar
preços por SKU antes de alterá-los. Push/publicação também aguardam autorização.

```powershell
python -m pip install -r requirements.txt
python manage.py runserver 127.0.0.1:8001
```

O servidor já está ativo nessa porta. Para importar arquivos fornecidos futuramente,
seguir [midias-instagram/README.md](../midias-instagram/README.md), validar com
`python manage.py import_store_media` e aplicar com `--apply` após preencher as
autorizações e associações reais no manifesto de entrada.
