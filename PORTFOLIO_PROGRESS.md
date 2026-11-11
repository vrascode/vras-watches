# VRAS Watches — progresso / progress

## 08/11/2026 — Refatoração MTV / MTV refactor

Implementado no checkout `C:\Projetos\vras-watches`, originalmente limpo em
`main` / `c7b2ff6`. Catálogo, preços, publicação, carrinho, mídia, vitrine e portal
foram separados por domínio dentro do app `loja`. Templates compartilhados e
testes foram reorganizados. Banco, dados, preços e fotografias foram preservados.

Delivered: domain packages, shared publication service, organized templates,
regression coverage and updated operating documentation. The Django app label,
public URLs and session contract are unchanged.

Validação / validation:

- `python manage.py check`: OK.
- Antes / before: `python manage.py test`: 135 tests, OK, skipped=2;
  both optional browser tests also passed when explicitly enabled.
- Depois / after: `python manage.py test`: 137 tests, OK, skipped=2;
  both optional browser tests also passed when explicitly enabled.
- Final combined run with `VRAS_BROWSER_QA=1`: all 137 tests passed, no skips, 35.641s.
- `python manage.py audit_storefront`: 12 products / 12 drafts; same baseline.
- `node scripts/browser_qa.mjs`: passed before and after; no browser/network errors.
- Four `node --check` calls passed for storefront/manager and QA scripts.
- Production manifest `collectstatic`: passed in a separate artifact directory.
- `makemigrations loja --check --dry-run`: no changes detected.
- 619 protected files unchanged; 35 routes unchanged; 35 identical screenshots.
- `git diff --check`: passed.

Pendência / remaining: Git metadata is read-only. `git add` failed with permission
denied on `.git/index.lock`; no commits, push or deploy were performed. Remote
HTTPS access was also blocked. Next action: review the working tree, create the
two coherent commits documented in `docs/REFACTOR_REPORT.md`, fetch/check the
actual remote state and push only when intended. Existing commercial draft
requirements remain pending owner confirmation.

Detalhes, comandos e mapa completo / details, commands and file map:
[docs/REFACTOR_REPORT.md](docs/REFACTOR_REPORT.md).


## 08/11/2026 — Organização do workspace / Workspace organization

A refatoração anterior está registrada nos commits locais `08efb62` e `a7aba34`;
o usuário informou sua publicação no GitHub. Esta tarefa começou com árvore
limpa em `main`, na mesma referência local de `origin/main`. Não foi possível
consultar o estado atual do servidor remoto por restrição de rede.

Entregue / delivered:

- 98 movimentos em artifacts, com 5.758 arquivos preservados por hash.
- Capturas/relatórios agrupados por suite e execução; evidências visuais,
  pesquisa, relatórios gerais, scripts históricos e runtime separados.
- Novos testes não sobrescrevem execuções anteriores; política comum em
  `scripts/qa_artifacts.mjs`.
- `.vscode/settings.json` oculta somente caches e saídas regeneráveis.
- `.gitignore` permite o guia de artifacts e settings compartilhados e
  mantém saídas de QA, dados privados, runtime e caches fora do Git.
- README, guia de artifacts e referências operacionais atualizados.
- Nenhum arquivo excluído; fonte Django, URLs e dados comerciais preservados.

Validação / validation:

- `python manage.py check`: OK antes e depois.
- `python manage.py test` antes: 137 testes, OK, skipped=2, 19.875s.
- `VRAS_BROWSER_QA=1 python manage.py test` depois: 137 testes, OK, sem skips,
  35.503s, incluindo login, upload, publicação, galeria e carrinho.
- `python manage.py audit_storefront`: mesmo resultado antes/depois,
  12 produtos / 12 rascunhos.
- `node scripts/browser_qa.mjs`: passou com 15 screenshots e sem erros inesperados.
- `node --check` nos três scripts de QA: passou.
- 5.758 hashes de arquivos movidos e 619 hashes protegidos: iguais.
- 24 caminhos concretos de artifacts e 15 links locais: válidos.
- Nenhum diff no código/dados de config, loja, templates, static ou data.
- `git diff --check`: passou.

Pendência / remaining: `git add` novamente bloqueado por `.git/index.lock`
somente para leitura. Nenhum novo commit, push ou deploy nesta execução.
Comandos para registrar e publicar os dois commits separadamente estão em
[docs/PROJECT_ORGANIZATION.md](docs/PROJECT_ORGANIZATION.md).

English: workspace artifacts were organized without deleting files or changing
commercial data. Shared editor settings hide only temporary/runtime output.
All 137 tests passed with browser QA enabled. Next action: review the changes,
create the documented commits in a normal PowerShell, check the current remote
state and publish each commit separately. Publication is not confirmed here.

## 10/11/2026 — Catálogo premium e importação Poedagar / Premium catalog

Base limpa: main em 5a047639a7d2e79781fd27683bc254df867a0734.
Alterações implementadas diretamente no projeto.

Entregue / delivered:

- Tema VRAS próprio em grafite/champanhe, apresentação responsiva, conteúdo
  original, especificações, seleção por cor, miniaturas, zoom e melhorias de
  teclado. Vídeos locais preparados para autoplay silencioso com controles.
- 13 modelos observados, 48 variantes acrescentadas, Montelux a R$ 259,00.
  Os 12 registros anteriores foram comparados com HEAD por conteúdo JSON e
  permanecem idênticos. Não foram inventadas referências industriais.
- Importação pública reutilizável, validação, simulação, IDs estáveis, prevenção
  de duplicatas, preço por variante, bloqueio concorrente e gravação atômica.
- Originais por hash e por produto/variante, WebP responsivo, suporte a MP4 H.264
  silencioso com poster real, inventário JSON/CSV e associação exata de mídia.
- Páginas de coleção disponíveis em /colecao/montelux/ e por cor, com
  disponibilidade pendente quando a oferta não está completa.
- Painel Django protegido em /admin/catalogo-referencia/ e exportação CSV.
- 44 novos testes de comportamento, incluindo fluxo isolado de publicação,
  galeria por cor, carrinho com preço calculado no servidor, retirada de oferta
  após atualização de preço e acesso administrativo.
- Plano e executor de 20 commits reais por funcionalidade, validado em simulação.
  Nenhum novo commit foi criado nesta execução.

Validação final / final validation:

- python manage.py check: sem problemas / no issues.
- python manage.py test: 242 tests, OK, skipped=2, 22.738s.
  Dois testes opcionais de navegador não executados; 240 aprovados.
- python manage.py audit_reference_catalog: 13 modelos, 48 variantes, todos os
  48 preços válidos, 12 registros anteriores, zero originais baixados.
- python manage.py audit_storefront: 60 produtos / 60 IDs únicos / 60 rascunhos.
- python manage.py audit_reference_catalog --strict-media: falha esperada,
  12 mídias pendentes; não foi representada como aprovação.
- node --check static/js/storefront.js: passou.
- node --check static/js/product-experience.js: passou.
- collectstatic com DEBUG=false e ManifestStaticFilesStorage em diretório
  separado de artifacts: passou; quatro CSS/JS principais e seus hashes
  conferidos.
- Nove rotas/arquivos via HTTP local: status 200, incluindo Montelux Prata/Azul,
  home, catálogo, busca, carrinho, login administrativo, CSS e JS novos.
  Evidência local em artifacts/reference-http-qa.json.
- git diff --check: passou.
- python scripts/commit_premium_catalog.py: 20 grupos válidos, sem arquivos
  omitidos, duplicados ou fora do plano; nenhuma gravação de índice em simulação.

Limitações observadas / observed limits:

- 12 URLs de imagens foram identificadas; a rede local negou todos os downloads
  (WinError 10013). Inventário registra erro, resolução desconhecida e ausência
  de originais. Não houve descoberta completa de vídeos ou de todo o catálogo
  de origem. ffmpeg/ffprobe não estão instalados.
- Autorização do proprietário da VRAS está registrada. A licença/titularidade
  de terceiros não foi verificada. Não houve cópia de depoimentos como avaliações
  VRAS nem reprodução do código visual exclusivo do varejista.
- Os 60 registros continuam rascunhos para compra; os novos modelos têm páginas
  de apresentação, preço autorizado e disponibilidade pendente. A publicação
  de venda mantém os critérios existentes de identificação, mídia e oferta.
- Git add falhou ao criar .git/index.lock: Permission denied. Git push origin
  main falhou ao conectar a github.com:443. Nenhum commit ou push novo confirmado.
- A revisão automática rejeitou a abertura do Chrome com depuração remota por
  política do ambiente. A alternativa headless sem depuração também falhou na
  inicialização GPU/permissões. Não foram produzidas capturas de navegador.
- Checkout/pagamento online continuam ausentes na aplicação original.

Próxima ação concreta / next concrete action:
usar o importador --refresh --discover --apply --download-media em ambiente
com rede, conferir as associações e ofertas pendentes, e executar o plano
revisado com python scripts/commit_premium_catalog.py --execute --push em um
terminal com escrita Git e acesso ao GitHub. Não é necessário recriar a
implementação nem os registros existentes.

Documentação / documentation:
[Operação / Operations](docs/PREMIUM_CATALOG.md),
[Evidências / Evidence](docs/REFERENCE_ANALYSIS.md).

English: local implementation and all 240 executed tests passed. Two optional
browser tests were skipped. Actual media acquisition, browser validation,
20 new commits and remote publication remain incomplete due to the observed
execution restrictions. Source products retain the Poedagar brand and original
records are unchanged.

## 10/11/2026 — Continuação de download e publicação / Download and publication continuation

Preservado o trabalho anterior em main / 5a047639a7d2e79781fd27683bc254df867a0734.
Inventário inicial de 57 arquivos modificados/novos salvo em artifacts.
Os 12 produtos anteriores, os 60 preços/aprovações e o SHA256 do banco foram
conferidos e permaneceram iguais.

Entregue nesta continuação / delivered in this continuation:

- Diagnóstico estruturado que separa WinError 10013 local de respostas HTTP
  401/403/404/429 e de falhas de processamento.
- Comando retry_reference_media, apenas para mídia: não reimporta catálogo,
  não renova aprovação de preço e não grava SQLite.
- Associação à galeria exige processamento completo e arquivo local válido.
  Corrigida a preservação dos metadados do inventário ao reimportar mídias.
- Sete novos testes de diagnóstico/repetição/preservação, além da verificação
  de que mídia incompleta ou ausente não entra na galeria.
- Plano de 20 commits atualizado, ainda sem commits vazios ou criados.

Resultados reais / actual results:

- Retry de 12 imagens: 12 environment_network_denied; zero imagens ou vídeos
  importados, zero mídias integradas e zero ofertas publicadas.
- DNS funcionou; TCP 443 foi negado para origem, CDN e GitHub com WinError 10013.
  Nenhuma resposta HTTP do site foi recebida pelo downloader.
- Uma imagem por cor (Prata/Preto/Azul) tem URL associada na fonte; nove imagens
  continuam sem variante confirmada. Conferência visual dos arquivos pendente.
- python manage.py check: OK.
- python manage.py test: 249 encontrados, 247 aprovados, dois opcionais ignorados,
  22.702s.
- python manage.py test loja.tests.reference: 50 aprovados.
- git status --short e git diff --check executados; sem erros de whitespace.
- Git add negado em .git/index.lock; git ls-remote sem conexão pelo terminal.
- A integração GitHub permitiu leitura e confirmou main idêntica à base local.
  create_tree foi recusado: “MCP tool call requires approval, but approval policy
  is never”. Nenhum commit ou update de branch foi realizado.
- Commits novos criados: 0. Commits enviados: 0. Nenhum hash novo para informar.

Banco preservado:
0f0395694d479fe41b86d0915d02b11575df2e785feecc920b9df2a7c13eb37b.

Próxima ação: executar retry_reference_media em ambiente com conexão pública
permitida, conferir mídias e ofertas reais e executar o plano Git em ambiente
com escrita/publicação permitida. Não remover as confirmações existentes nem
usar o estado de estoque do varejista como confirmação de disponibilidade VRAS.

Relatório bilíngue: [docs/CATALOG_PUBLICATION_STATUS.md](docs/CATALOG_PUBLICATION_STATUS.md).
English: zero real media imported, zero new offers published and zero commits
sent. All products, prices and database bytes were preserved. The 247 executed
tests passed. Remaining work requires an external change to the observed
network/Git/approval restrictions and verified product/media availability.

## 10/11/2026 — Catálogos com fotos / Photo catalogs

Trabalho anterior preservado. 45 novas imagens identificadas por seletor de cor,
totalizando 48 cores dos 13 modelos existentes e 57 imagens no inventário.
Fotos externas nas prévias por modelo/cor; nenhum requisito de venda alterado.

Entregue / delivered:
- Catálogo imprimível em /catalogos/poedagar/, filtro por modelo e links na loja.
- export_poedagar_catalog gera um HTML completo e 13 por modelo com CSS/JS
  incorporados; incorpora fotos locais quando disponíveis.
- Arquivos em artifacts/catalogos/poedagar/. Guia: docs/POEDAGAR_CATALOGS.md.
- Oito novos testes de associação por cor, precedência local, origens permitidas,
  impressão, exportação/preservação, incorporação e metadados de compartilhamento.

Validação real / actual validation:
- python manage.py check: passou.
- python manage.py test loja.tests.reference --noinput: 58 passaram.
- python manage.py test --noinput: 257 encontrados, 255 passaram, dois opcionais
  ignorados; 23.014s.
- node --check static/js/poedagar-catalog.js: passou.
- python manage.py export_poedagar_catalog: 14 arquivos, 13 modelos, 48 cores;
  48 imagens externas.
- git diff --check: passou.

Limite observado / observed limit:
- python manage.py retry_reference_media --apply --report artifacts/catalogos/poedagar/download-report.json:
  57 environment_network_denied (WinError 10013), zero downloads, zero mídias
  anexadas e zero ofertas publicadas. As fotos exigem internet no navegador.
  Nenhum PDF foi renderizado ou inspecionado visualmente.
- Não foram criados commits; .git é somente leitura e a política é never.

Preservação byte a byte / preserved SHA256:
- data/products.json: 867253998156235ac0017e34ec3da40669fdb2a4244e44e2774327fe40152ebb
- data/media.json: 7237fc6eb595847951a056282bde1d1548088ef44052747bd96baf8d7fa1941b
- db.sqlite3: 0f0395694d479fe41b86d0915d02b11575df2e785feecc920b9df2a7c13eb37b

Próxima ação: retry_reference_media em terminal com rede permitida; exportar
novamente para incorporar fotos locais e conferir impressão em navegador.
English: HTML catalogs delivered; actual downloads remain environment-blocked.
No price, stock or sale status was changed.

## 10/11/2026 — Downloader Windows e importador offline / Windows downloader

Solicitação atual: separar o download no PowerShell normal da rede restrita do
Codex, validar arquivos reais, importar localmente e preservar produtos/preços.

Implementado:
- scripts/download_poedagar_media.ps1: Invoke-WebRequest HTTPS, seleção por
  autorização registrada, timeout, redirecionamentos restritos, falhas individuais,
  parada no primeiro socket 10013, comprovantes e retomada com SHA256.
- scripts/poedagar_media.py e loja/media/local_reference.py: auxiliares offline
  de plano, validação real de formato/pixels/tamanho, hash, comprovantes e relatório.
- Originais preservados sem sobrescrita, em media-originals/, com staging,
  promoção atômica por hard link no mesmo volume e comprovantes por mídia.
- import_poedagar_media: sem transporte de rede, importação parcial com relatório,
  associações exatas por modelo/cor, WebP e miniaturas de 160 px, sem publicar.
- Exportador existente reutiliza as galerias locais após a importação.
- Guia bilíngue: docs/POEDAGAR_WINDOWS_DOWNLOAD.md.
- 14 testes novos: arquivos válidos/corrompidos, limites, autorização/revogação,
  hashes, duplicatas, retomada, caminhos, importação parcial, cor, preservação,
  operação offline e análise de sintaxe PowerShell.

Validação executada:
- python manage.py check: passou.
- python manage.py test loja.tests.reference.test_local_import --noinput:
  14 passaram, 1.693s.
- python manage.py test: 271 encontrados, 269 passaram, dois opcionais ignorados,
  25.027s.
- Analisador AST PowerShell 5.1: sem erros.
- python scripts/poedagar_media.py --root C:/Projetos/vras-watches plan:
  57 URLs, 57 imagens com autorização registrada do proprietário, 57 a baixar.
- python scripts/poedagar_media.py --root C:/Projetos/vras-watches report:
  0 downloads comprovados, 0 imagens válidas, 0 produtos com galeria local,
  57 mídias pendentes; rightsholder_verified = 0; 9 imagens sem cor associada.
- git diff --check: passou.

Limites e estado aberto:
- Nenhuma tentativa de rede foi repetida no sandbox nesta continuação.
- A invocação do .ps1 somente com -PlanOnly foi recusada com PSSecurityException:
  execução de scripts desabilitada neste processo. Não foram usadas mudanças de
  política, Bypass, proxies, assinatura fictícia ou desativação de TLS.
- O downloader PowerShell completo não foi executado; a análise AST não substitui
  um teste real de Invoke-WebRequest. Não há novos arquivos de fotos comerciais.
- A execução externa foi solicitada ao usuário com o comando exato. A aquisição
  NÃO está concluída até os originais reais serem recebidos e validados.
- Após download/importação bem-sucedidos de todas as URLs, nove imagens sem cor
  continuam sem associação e não serão atribuídas por suposição.
- Nenhum commit criado: .git é somente leitura neste ambiente.

Hashes preservados:
data/products.json = 867253998156235ac0017e34ec3da40669fdb2a4244e44e2774327fe40152ebb
data/media.json = 7237fc6eb595847951a056282bde1d1548088ef44052747bd96baf8d7fa1941b
db.sqlite3 = 0f0395694d479fe41b86d0915d02b11575df2e785feecc920b9df2a7c13eb37b

Próxima ação:
no PowerShell normal: & .\scripts\download_poedagar_media.ps1
depois: python manage.py import_poedagar_media --apply
então: python manage.py export_poedagar_catalog
Se a política normal também bloquear scripts, obter a saída de
Get-ExecutionPolicy -List e usar o fluxo de assinatura/aprovação permitido
pelo administrador. Nenhuma redução de proteção foi implementada ou recomendada.

English: implementation and offline tests are ready; actual photo acquisition
is explicitly still open. Product data, prices, offers and SQLite are unchanged.
