# Catálogos Poedagar / Poedagar catalogs

Foram gerados 14 arquivos HTML: um catálogo completo e um para cada um dos
13 modelos existentes, com 48 cores. Abra artifacts/catalogos/poedagar/index.html
no navegador. O botão **Imprimir / Salvar PDF** aguarda as imagens e abre a
impressão do navegador. Escolha **Salvar como PDF** para exportar.
Não foi produzido um PDF nesta execução.

A loja também oferece /catalogos/poedagar/ e o filtro por modelo, por exemplo
/catalogos/poedagar/?modelo=Signature. O catálogo normal e as páginas de
coleção possuem links para impressão. As páginas de coleção e seus cartões
agora apresentam a fotografia da cor exata observada na fonte.

    python manage.py runserver 127.0.0.1:8001
    python manage.py export_poedagar_catalog
    python manage.py test loja.tests.reference

A exportação inclui CSS e JavaScript no próprio HTML. Fotos locais aprovadas
são incorporadas em base64 quando disponíveis. Fotos externas permanecem
como URLs e precisam de internet no navegador.

## Fotos e limitações verificadas em 10/11/2026

- 45 links foram acrescentados aos três links Montelux já associados por cor.
- A associação de modelo/cor vem dos seletores identificados nas páginas públicas,
  inclusive os cartões de recomendação. Não foi inferida pela aparência ou pelo
  nome do arquivo. O escopo cobre somente as 48 cores já cadastradas.
- O inventário contém 57 imagens: 48 associadas a cores e nove Montelux sem cor
  confirmada. As nove sem cor não entram nas prévias.
- Fontes observadas: [Signature](https://poedagareco.com/products/relogio-poedagar-signature),
  [Army e cartões relacionados](https://poedagareco.com/products/relogio-poedagar-army)
  e [Montelux](https://poedagareco.com/products/relogio-poedagar-montelux%C2%AE).
  Evidências em data/poedagar_photo_sources.json e data/reference_media_inventory.json.
- A tentativa real de baixar as 57 imagens falhou com
  environment_network_denied / WinError 10013. Nenhum arquivo de imagem
  foi baixado. Relatório: artifacts/catalogos/poedagar/download-report.json.
- As ferramentas de consulta identificaram as URLs, mas não forneceram
  os bytes das fotografias ao workspace. Algumas URLs também não tinham cópia
  no cache da consulta. A renderização das 48 fotografias no navegador e a
  paginação visual do PDF não foram verificadas neste ambiente.
- O catálogo trata erros de imagem e mantém a identificação e o preço visíveis.
  Fotos de referência exibidas por URL não contam como mídia local aprovada para
  publicar uma oferta de venda.

Quando o terminal tiver acesso à internet, use o fluxo de mídia existente:

    python manage.py retry_reference_media --apply --report artifacts/catalogos/poedagar/download-report.json
    python manage.py export_poedagar_catalog

Os originais serão preservados em media-originals/, as versões WebP em
static/img/products/poedagar/, e a exportação seguinte incorporará as fotos
locais no HTML. Os preços, aprovações, ofertas e SQLite não são modificados
por esses comandos de mídia/exportação. A disponibilidade deve ser confirmada
na VRAS pelo fluxo existente.

## English

The full catalog and thirteen model catalogs are available as portable HTML
files under artifacts/catalogos/poedagar/, and through the Django route
/catalogos/poedagar/. They cover 48 existing colors, retain VRAS prices and
include a browser print/save-as-PDF action. No PDF was rendered in this run.

All 57 actual download attempts were denied by the execution environment.
The catalogs therefore currently reference external image URLs and require
browser internet access. The existing retry command preserves originals,
creates responsive WebP files and binds exact model/color images once network
access is available. Re-exporting embeds those local photos for offline use.

Remote previews do not satisfy sale publication checks. Catalog data, approved
prices, the commercial media manifest and SQLite were preserved byte for byte.
Validation: 257 tests found, 255 passed, two optional browser tests skipped;
58 reference tests passed; Django checks, JavaScript syntax and whitespace
checks passed. Visual browser/PDF verification remains unavailable.

## Download pelo PowerShell normal / Native Windows downloader

O novo fluxo recomendado usa scripts/download_poedagar_media.ps1 no PowerShell
normal e python manage.py import_poedagar_media --apply para importar somente
arquivos locais. Consulte [o guia Windows](POEDAGAR_WINDOWS_DOWNLOAD.md) para
comandos, autorização, retomada, relatórios e política de execução.

English: use the Windows downloader and offline Django importer; see the guide
for verified limits and real-file validation. Acquisition is still pending.
