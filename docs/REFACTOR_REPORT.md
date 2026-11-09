# Relatório de refatoração MVC / MTV — VRAS Watches

Data local da execução: 08/11/2026. Checkout: `C:\Projetos\vras-watches`.
A execução ocorreu no workspace disponibilizado, não no caminho antigo de Downloads.

## Estado inicial

- `git status --short --branch`: árvore limpa; branch `main`.
- HEAD e referência local `origin/main`: `c7b2ff6`; divergência local `0 / 0`.
- `git fetch origin main` falhou: escrita de `.git/FETCH_HEAD` negada pelo ambiente.
- `git ls-remote origin refs/heads/main` falhou: conexão HTTPS com GitHub bloqueada.
  Portanto, a coincidência com o estado atual do servidor remoto não foi confirmada.
- Nenhum arquivo modificado ou não versionado de outra tarefa precisava ser isolado.
- Mapeamento anterior aos movimentos: 35 rotas, incluindo admin Django; 40 módulos
  Python em `config/`, `loja/` e `scripts/`; templates, estáticos e dependências.
- Baseline de preservação: 619 arquivos de `data/`, `static/`, `midias-instagram/`
  e `db.sqlite3`. Inclui registros privados, originais, histórico e backups existentes.
- Evidências locais em `artifacts/reports/refactor/`: `baseline.txt`, `inventory-before.json`
  e `preservation-before.json`. Esses arquivos são ignorados pelo Git.

## Estrutura final

```text
config/                              configuração Django preservada
loja/
  catalog/
    repository.py                    leitura do JSON e localização do catálogo
    services.py                      consultas, galerias, filtros e variantes
    pricing.py                       preços aprovados e vínculo com a variante
    validation.py                    identidade e requisitos comerciais
    publication.py                   simulação e publicação segura
    views.py, urls.py                listagem e detalhes HTTP
  cart/
    services.py                      sessões, quantidades e totais
    views.py, urls.py                endpoints do carrinho
  storefront/
    views.py, urls.py                home, robots e sitemap
    context_processors.py           contador, políticas e metadados compartilhados
  management_portal/
    forms.py                         validações e upload
    services.py                      recebimentos, auditoria e coordenação
    views.py, urls.py                autenticação staff e painel
  media/
    assets.py                        manifesto e autorização local
    import_service.py                vínculo e importação de mídias
    processing.py                    geração de WebP responsivo
    staticfiles.py                   finder com restrições preservadas
  management/commands/              quatro comandos existentes preservados
  templates/loja/
    catalog/                         listagem, detalhes, cards e galeria
    cart/                            página do carrinho
    storefront/                      home e sitemap
    management_portal/               base, login, painel e formulário
    legacy/                          modal antigo arquivado
  tests/
    catalog/                         produtos, preços, variantes e publicação
    cart/                            operações e validações do carrinho
    media/                           autorização e importação
    storefront/                      páginas e apresentação
    management_portal/               recebimentos e fluxo de navegador
    integration/                     deploy, URLs e sessão autenticada
    support/                         fixtures isoladas do catálogo arquivado
  templatetags/                      JSON-LD seguro
  models.py                          contrato de persistência, sem novas tabelas
  urls.py                            namespace loja: preservado
  utils.py                           normalização e moeda
templates/
  base.html                          base pública compartilhada
  components/                        header, footer, avisos, zoom e mídia
  404.html, 500.html                  erros globais
static/                              CSS, JS, imagens e fontes com caminhos originais
data/                               produtos, manifesto, aprovações e backups
midias-instagram/                     arquivos privados preservados
scripts/                             pesquisa, relatórios e QA existentes
docs/                               documentação e decisões
```

`config/` já tinha responsabilidade adequada; somente os caminhos do context
processor, finder e diretório compartilhado de templates precisaram mudar.
Mantivemos `INSTALLED_APPS`, `ROOT_URLCONF`, ASGI, WSGI e SQLite. Os pacotes internos
não são novos apps, por isso não alteram labels, content types ou permissões.
As responsabilidades e dependências estão detalhadas em [ARCHITECTURE.md](ARCHITECTURE.md).

## Arquivos movidos e separados

| Origem | Destino / separação |
| --- | --- |
| `loja/services.py` | `loja/catalog/{repository,services,pricing,validation}.py`, `loja/cart/services.py`, `loja/utils.py` |
| `loja/pricing.py` | `loja/catalog/pricing.py` |
| `loja/views.py` | `loja/{catalog,cart,storefront}/views.py` |
| `loja/catalog_views.py` | `loja/management_portal/views.py`; preparação do catálogo do proprietário em `services.py` |
| `loja/catalog_forms.py` | `loja/management_portal/forms.py` |
| `loja/catalog_receipts.py` | `loja/management_portal/services.py`; confirmações e armazenamento de originais extraídos em funções menores |
| `loja/context_processors.py` | `loja/storefront/context_processors.py` |
| `loja/media.py` | `loja/media/assets.py` |
| `loja/media_import.py` | `loja/media/import_service.py` e `loja/media/processing.py` |
| `loja/staticfiles.py` | `loja/media/staticfiles.py` |
| Lógica de `publish_ready_products` | `loja/catalog/publication.py`; comando mantido como adaptador CLI |
| `loja/urls.py` | composição de quatro módulos de rotas, mantendo todos os nomes anteriores |
| `loja/templates/loja/base.html` | `templates/base.html` e `templates/components/{header,footer,notifications,zoom}.html` |
| `loja/templates/loja/{_responsive_image,_video}.html` | `templates/components/{responsive_image,video}.html` |
| `loja/templates/loja/{products,product_detail,_product_card,_product_gallery}.html` | `loja/templates/loja/catalog/` |
| `loja/templates/loja/{home.html,sitemap.xml}` | `loja/templates/loja/storefront/` |
| `loja/templates/loja/cart.html` | `loja/templates/loja/cart/cart.html` |
| `loja/templates/loja/manager/*` | `loja/templates/loja/management_portal/` |
| `loja/templates/{404,500}.html` | `templates/{404,500}.html` |
| `loja/templates/loja/_welcome_modal.html` | `loja/templates/loja/legacy/_welcome_modal.html` |
| `loja/tests.py` | classes separadas em `tests/{catalog,cart,media,storefront,integration}/test_*.py` |
| `loja/test_poedagar.py` | `loja/tests/catalog/test_variants.py` |
| `loja/test_approved_prices.py` | `loja/tests/catalog/test_pricing.py` |
| `loja/test_catalog_migration.py` | `loja/tests/catalog/test_migration.py` |
| `loja/test_publication.py` | `loja/tests/catalog/test_publication.py` |
| `loja/test_media_import.py` | `loja/tests/media/test_import.py` |
| `loja/test_catalog_receipts.py` | `loja/tests/management_portal/test_receipts.py` |
| `loja/test_catalog_owner_browser.py` | `loja/tests/management_portal/test_browser.py` |
| `loja/test_storefront_update.py` | `loja/tests/storefront/test_editorial.py` |
| `loja/testing_catalog.py` | `loja/tests/support/catalog.py` |

Foram atualizados imports, alvos dos patches, caminhos de templates, configuração
e comandos. Os scripts auxiliares não dependiam dos imports antigos e mantêm sua
interface. Os documentos de entrega datados de mudanças anteriores são registros
históricos; seus caminhos antigos podem ser localizados pela tabela acima.

## Funcionalidades preservadas

- Home e estado de coleção em preparação; busca, filtros e ordenações.
- Detalhes públicos apenas de ofertas aptas, variantes, galerias e zoom.
- Adição, remoção, quantidades, subtotais Decimal e respostas HTML/JSON do carrinho.
- Mesmas chaves de sessão; reconciliação preserva login e dados históricos.
- Login administrativo, autorização staff e painel `/gestao/catalogo/`.
- Cadastro de fotos pelo navegador; validação de formato/tamanho, autorização,
  correspondência com SKU, WebP, originais privados e comprovantes.
- Confirmação de identidade, variante e disponibilidade, publicação automática,
  revisão da oferta, recibos com autor/horário e proteção contra envios concorrentes.
- Todos os comandos `manage.py`, admin Django, estáticos filtrados e URLs `loja:`.
- Identidade visual: 35 screenshots de antes/depois idênticos pixel a pixel.

## Dados preservados

Os 619 hashes conferidos continuam iguais. Nenhum arquivo protegido sumiu.
Isso inclui o SQLite existente, todas as contas nele armazenadas, os dois JSONs,
preços aprovados, IDs 13–24, variantes, referências, autorizações, fotos e backups.
Não foi executado `migrate`, nem criado um arquivo de migração durante o trabalho.
`makemigrations loja --check --dry-run` informou ausência de mudanças.
Os 12 produtos reais permaneceram em rascunho; o catálogo real não foi publicado
para satisfazer testes.

SHA-256 antes e depois:

- `data/products.json`: `09f76249261def7cfb04672ac89055e4d93b125afbfb9d2454b3e2f40483e8ad`
- `data/media.json`: `7237fc6eb595847951a056282bde1d1548088ef44052747bd96baf8d7fa1941b`

## Validação antes e depois

| Verificação | Antes | Depois |
| --- | --- | --- |
| `python manage.py check` | sem problemas | sem problemas |
| `python manage.py test` (execução padrão) | 135 testes, OK, 2 de navegador pulados | 137 testes, OK, 2 de navegador pulados |
| Dois testes de navegador habilitados | 2 passaram | 2 passaram |
| Su?te final com `VRAS_BROWSER_QA=1` | opcional executado separadamente | **137 testes passaram, sem skips, em 35,641 s** |
| `python manage.py audit_storefront` | 12 produtos, 12 IDs únicos, 580 mídias locais, 0 aprovadas, 0 posts, 12 rascunhos | resultado igual |
| `node scripts/browser_qa.mjs` | 15 screenshots, 12 redirecionamentos, 12 rascunhos protegidos, sem erros | resultado igual |
| Rotas com nomes, incluindo admin | 35 mapeadas | 35 preservadas |
| Templates | mapeados | 21 compilados |
| Módulos Python de config/app/scripts | 40 mapeados | 70 compilados |
| Arquivos protegidos | 619 hashes registrados | 619 iguais |
| Comparação visual | baseline capturado | 35/35 screenshots idênticos |
| `collectstatic` com ManifestStaticFilesStorage | não refeito antes | passou em `artifacts/runtime/static-build/refactor`, 292 entradas de saída |
| `makemigrations loja --check --dry-run` | nenhuma mudança estrutural anterior | nenhuma mudança detectada |
| Sintaxe JS: scripts e interface | scripts existentes executados | quatro arquivos passaram no `node --check` |
| `git diff --check` | árvore limpa | sem erros |

A suíte recebeu dois novos testes: contrato das 12 URLs da aplicação e preservação
de uma sessão autenticada ao reconciliar o carrinho legado. Os 135 anteriores
foram mantidos, com organização e imports atualizados. Os fluxos de navegador
usam banco e ofertas fictícios isolados, incluindo upload, publicação e compra
pelo carrinho; nenhum estado comercial foi inventado nos dados reais.

No primeiro lançamento, o Chrome falhou antes da refatoração por restrição do
ambiente. A execução isolada com `--no-sandbox` permitiu rodar os testes de antes
e depois. Essa opção não foi adicionada à aplicação ou aos scripts existentes.
Os relatórios locais estão em `artifacts/` e os inventários/hashes/comparação
estão em `artifacts/reports/refactor/` e `artifacts/visual/refactor/`; eles não fazem parte do versionamento.

## Commits e pendências

**Nenhum commit foi criado.** A tentativa real de `git add -- loja config`
falhou ao criar `.git/index.lock` por acesso negado. O ambiente permite editar
o código, mas expõe `.git` somente para leitura e não permite elevação.
As alterações permanecem no diretório de trabalho para revisão e commit em um
terminal normal. Não houve reset, recriação do repositório, push ou deploy.

As etapas foram verificadas progressivamente: extração de catálogo/carrinho/mídia;
publicação compartilhada; separação de views/rotas; testes por domínio; templates;
regressões e documentação. Para registrar a entrega em commits coesos, execute
fora deste ambiente restrito:

```powershell
git add -- config loja templates
git commit -m "refactor: modularize VRAS Watches MTV domains and preserve contracts"
git add -- README.md docs/ARCHITECTURE.md docs/POEDAGAR_CATALOG.md docs/TESTING_GUIDE.md docs/REFACTOR_REPORT.md PORTFOLIO_PROGRESS.md
git commit -m "docs: document MTV architecture and refactor validation"
git fetch origin
git status --short --branch
```

Confira a sincronização real e trate eventual atualização remota antes de publicar.
O comando de envio, não executado aqui, é:

```powershell
git push origin main
```

Pendências comerciais pré-existentes: confirmar produtos/variantes reais,
fornecer fotografias autorizadas, confirmar disponibilidade e demais dados de
lançamento. A refatoração não substitui essas confirmações. Não há falhas de
regressão conhecidas ao concluir os testes descritos.

## English delivery notes

The refactor was applied directly in the available checkout. The Django app
identity, URLs, session keys, SQLite bytes and all commercial/media records were
preserved. Domain packages replace the catalog/cart/view monoliths; publication
is shared between CLI and authenticated browser intake. Existing tests were
moved by domain and two compatibility tests were added. Browser workflows and
35 pixel-identical screenshots confirm the preserved behavior and appearance.
Local commits and live remote synchronization remain blocked by read-only Git
metadata and restricted outbound networking; no push or deployment occurred.
