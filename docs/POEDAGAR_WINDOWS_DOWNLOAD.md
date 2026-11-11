# Download Poedagar pelo Windows / Windows media download

O downloader é scripts/download_poedagar_media.ps1. Execute no PowerShell normal
do Windows, fora do Codex. O script usa Invoke-WebRequest; o auxiliar Python
somente lê o inventário e valida arquivos locais. Não usa a rede do Python.

Na pasta do projeto:

    Set-Location 'C:\Projetos\vras-watches'
    & .\scripts\download_poedagar_media.ps1

Depois dos downloads:

    python manage.py import_poedagar_media --apply
    python manage.py export_poedagar_catalog

O primeiro comando Django trabalha somente com originais locais, cria WebP e
miniaturas de 160/480/800/1200/1920 px (limitadas à resolução do original) e
atualiza data/media.json com associação exata de modelo/cor. O segundo exporta
novamente os catálogos HTML com as fotos locais incorporadas.

Sem --apply, import_poedagar_media apenas verifica os arquivos e grava o
relatório. Para verificar depois da importação:

    python manage.py import_poedagar_media
    python manage.py check
    python manage.py test

## Requisitos e política de execução

O script requer PowerShell 5.1 ou superior e o Python do projeto com Django e
Pillow instalados. Seleciona .venv\Scripts\python.exe quando disponível;
caso contrário, usa python encontrado no PATH. Para indicar outro interpretador:

    & .\scripts\download_poedagar_media.ps1 -Python 'C:\caminho\python.exe'

Planejamento sem acessar a rede (Python auxiliar):

    python scripts/poedagar_media.py --root 'C:\Projetos\vras-watches' plan

O processo do Codex rejeitou a execução de .ps1 com PSSecurityException,
mesmo usando -PlanOnly. Nenhuma política foi alterada. A sintaxe foi validada
pelo analisador do PowerShell; o downloader completo com Invoke-WebRequest
não pôde ser executado aqui.

Se o PowerShell normal também disser que a execução de scripts está desabilitada,
interrompa e confira Get-ExecutionPolicy -List. O script precisa de um ambiente
que já permita sua execução, ou de assinatura/aprovação pela administração do
computador. Não use Bypass, não desative validação TLS e não altere as proteções
para executar esta entrega. O arquivo não foi assinado nesta execução.

## Autorizações e escopo

São 57 URLs únicas de imagens no inventário. Todas têm registro de autorização
do proprietário da VRAS, com status owner_authorized_unverified_rightsholder.
Isso é diferente de uma licença/titularidade de terceiros verificada, cujo
contador continua zero. Os dados de autorização não foram modificados.

O filtro exige imagem e registro de autorização não vazio, com o status existente
de autorização do proprietário ou confirmed: true. Rejeita confirmação falsa,
revogação e status denied/rejected/revoked. Não permite escolher arbitrariamente
URLs novas por parâmetro.

48 imagens têm modelo e cor associados. Nove imagens Montelux não têm cor
confirmada: são baixadas e processadas, mas não entram em galerias por suposição.
Mesmo com todos os downloads, essas nove continuam pendentes de associação.

## Arquivos, validação e repetição

- HTTPS restrito a poedagareco.com e cdn.shopify.com, incluindo redirecionamentos;
  no máximo cinco redirecionamentos e timeout configurável, padrão 45 segundos.
- Usa -UseBasicParsing, -OutFile e nunca -PassThru. A documentação da
  [Microsoft](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/invoke-webrequest?view=powershell-5.1)
  registra um problema em que a combinação OutFile/PassThru deixa arquivos vazios.
- Valida conteúdo real com Pillow: JPEG, PNG, WebP ou AVIF; máximo de 20 MiB e
  40 megapixels; rejeita HTML, animação, corrupção e pixels truncados.
- O limite de bytes é conferido no arquivo após a transferência pelo
  Invoke-WebRequest. O timeout limita a duração de cada requisição.
- Preserva nome, bytes e SHA256 do original em
  media-originals/<modelo>/<cor-ou-sem-variante-confirmada>/<id>/<nome-original>.
- Downloads ficam temporariamente em media-originals/.incoming/. Somente arquivos
  validados são promovidos, sem sobrescrever originais, por criação atômica de
  hard link no mesmo volume. Exige suporte a hard links, como em NTFS.
- Cada mídia tem comprovante em media-originals/.receipts/<id>.json, com origem,
  formato, dimensões, SHA256 e erro individual, se houver.
- Repetir o script verifica o original e o SHA256 e pula a transferência quando
  ele já é válido. Originais ausentes são tentados; originais corrompidos ou com
  hash divergente são reportados e preservados para investigação.
- Não há tentativas automáticas repetidas da mesma URL. Se houver erro local de
  socket 10013, o script interrompe o lote.
- Um lock impede dois downloaders simultâneos. Os comprovantes e arquivos já
  concluídos permitem retomar após interrupção. Duplicatas idênticas do
  inventário são processadas uma vez; IDs conflitantes são recusados.

## Relatórios e contadores

Os relatórios JSON ficam em artifacts/catalogos/poedagar/:

- powershell-download-report.json: validação dos arquivos presentes;
- powershell-download-run.json: acrescenta downloads/reutilizações/falhas desta execução;
- local-import-report.json: validação, processamento e associação no Django.

Contadores: urls_identified, images_authorized, downloads_completed,
valid_images, products_with_gallery e media_pending.
download_pending separa originais ausentes/inválidos de pendências de galeria.
media_pending inclui imagens ainda sem processamento ou sem associação exata.

A verificação usa o arquivo real, não apenas o estado do inventário. Um
arquivo ausente ou com hash divergente nunca conta como validado/concluído.

Estado observado antes da execução externa: 57 URLs, 57 imagens com autorização
do proprietário registrada, zero downloads comprovados, zero imagens válidas,
zero produtos com galeria local e 57 mídias pendentes. O trabalho de aquisição
permanece aberto até os arquivos reais serem recebidos e validados.

Preços, produtos, disponibilidade e SQLite são preservados. Não há parâmetro
para publicar ofertas neste importador. Uma foto local não confirma estoque.

## English

Run scripts/download_poedagar_media.ps1 from ordinary Windows PowerShell,
then python manage.py import_poedagar_media --apply. The PowerShell process
uses Invoke-WebRequest; Python only validates local files, creates receipts
and imports them offline. The importer refuses all network fetches and never
publishes products or writes prices, products or SQLite.

The script validates actual image bytes and pixels, checks SHA256 on resumed
runs, refuses overwriting originals and records individual failures. It only
selects images with recorded owner authorization; unverified third-party
ownership remains explicit. Nine images have no confirmed color and will
remain unassociated. Re-export catalogs after local import for offline images.

The sandbox also disallowed .ps1 execution. We did not change execution policy
or use a bypass. PowerShell syntax and the offline Python behavior were tested;
actual HTTP downloads and execution of the complete PowerShell script remain
unverified here. Run it in a Windows session already authorized for scripts,
or obtain approved script signing if required by your system.
