# VRAS Watches

Loja Django com templates renderizados no servidor, catálogo JSON e carrinho
persistido em sessões Django. A arquitetura MTV mantém um único app `loja`,
organizado internamente por domínio, sem alterar o banco, permissões ou URLs.

Os **12 modelos Poedagar têm preços aprovados e continuam em rascunho** no catálogo
entregue. A venda depende de identidade, variante, fotos autorizadas e disponibilidade
confirmadas. Nenhum estado comercial foi alterado pela refatoração.

## Arquitetura

```text
config/                         settings, URLs principais, ASGI e WSGI
loja/
  catalog/                      catálogo e detalhes públicos
    repository.py               leitura de data/products.json
    services.py                 consultas, filtros, galerias e variantes
    pricing.py                  aprovação e correspondência de preços
    validation.py               identidade e requisitos de publicação
    publication.py              simulação e publicação segura
    views.py, urls.py            requisições HTTP e rotas do catálogo
  cart/                         serviços de sessão, views e URLs do carrinho
  storefront/                   home, robots, sitemap e context processor
  management_portal/            forms, recebimento de fotos, views e URLs da gestão
  media/                        autorização, importação, WebP e finder de estáticos
  management/commands/          adaptadores administrativos para manage.py
  templates/loja/               catalog/, cart/, storefront/, management_portal/, legacy/
  tests/                        testes por domínio, integração e fixtures de suporte
  templatetags/                 apresentação segura de JSON-LD
  models.py                     contrato de persistência; sem modelos ORM de produtos
  urls.py                       composição das rotas no namespace existente loja:
  utils.py                      normalização textual e formatação BRL
templates/                     base.html, componentes compartilhados e páginas de erro
static/                         css/, js/, img/ e fonts/ preservados
data/                          catálogo, manifesto, aprovações e backups preservados
midias-instagram/               originais e comprovantes privados; ignorados pelo Git
scripts/                        pesquisa, relatórios e QA de navegador
docs/                          arquitetura, operação e relatórios de validação
manage.py
requirements.txt
.env.example
```

As views recebem requisições e coordenam respostas; serviços concentram as regras;
forms validam os envios do proprietário; templates apresentam os resultados.
O repositório existe porque o catálogo é um arquivo JSON. Não há repositórios
artificiais para sessões ou autenticação, nem migração de produtos para o ORM.
SQLite continua responsável por usuários, permissões e sessões.

Leia [as decisões arquiteturais](docs/ARCHITECTURE.md) e o
[relatório da refatoração](docs/REFACTOR_REPORT.md), incluindo o mapa de arquivos.

## Instalação e execução

Na pasta que contém `manage.py`, com Python 3.12+:

```powershell
cd C:\Projetos\vras-watches
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8001
```

Dependências fixadas: Django 6.0.6 e Pillow 13.0.0. Node 22+ e Chrome/Chromium são
usados apenas nos testes de navegador; a loja não precisa de npm ou bundler.
Em uma instalação nova, execute `python manage.py migrate` para criar as tabelas
Django. No banco existente, esse comando aplica apenas migrações pendentes.
A refatoração não exige novas migrações nem recriação de `db.sqlite3`.

`.env.example` documenta as variáveis; Django não carrega `.env` automaticamente.
Configure o ambiente do processo. Em produção, defina `DJANGO_DEBUG=false`,
`DJANGO_SECRET_KEY` persistente e `DJANGO_ALLOWED_HOSTS`. Uma chave persistente
preserva a autenticação entre reinicializações; a chave de desenvolvimento gerada
quando a variável está ausente é efêmera, como antes da refatoração.
`SITE_URL` recebe uma origem HTTP(S) sem caminho; sem ela, não são inventados
canonical ou URLs absolutas de sitemap. Consulte também `HTTPS_ENABLED` e
`DJANGO_CSRF_TRUSTED_ORIGINS` em `.env.example`.

## Rotas preservadas

| Rota | Comportamento |
| --- | --- |
| `/` | Home, editorial, coleções e mídias aprovadas |
| `/produtos/` | Busca, categoria e ordenação de ofertas publicadas |
| `/produto/<id>/` | Detalhes, galeria, zoom e variantes confirmadas |
| `/carrinho/` | Quantidades, subtotais e total calculados com Decimal |
| `/carrinho/adicionar/<id>/` | POST: adiciona uma unidade |
| `/carrinho/remover/<id>/` | POST: diminui uma unidade |
| `/carrinho/atualizar/<id>/` | POST: quantidade de 0 a 99; zero remove |
| `/gestao/entrar/` | Login administrativo |
| `/gestao/catalogo/` | Painel do proprietário |
| `/gestao/catalogo/<id>/` | Confirmações e upload pelo navegador |
| `/admin/` | Administração Django |
| `/robots.txt`, `/sitemap.xml` | Metadados de indexação |

Todos os nomes `loja:...` foram mantidos. Filtros usam `categoria`, `q` e `ordem`;
a busca ignora caixa e acentos. Rascunhos não aparecem na busca, detalhes públicos
ou sitemap. IDs aposentados 1–12 redirecionam ao catálogo; os Poedagar mantêm
os IDs 13–24. O carrinho preserva suas chaves de sessão e remove ofertas que
ficaram indisponíveis ou mudaram de referência/variante, sem apagar o login.

Não existe checkout, gateway de pagamento ou criação de pedidos pelo contato.

## Painel, fotografias e publicação

Acesse http://127.0.0.1:8001/gestao/catalogo/ usando uma conta administrativa
ativa existente. Se ainda não houver conta, crie uma com
`python manage.py createsuperuser`. Não há credenciais padrão.

1. Selecione o modelo e confira no produto real a referência e a documentação.
2. Selecione a variante correspondente e confirme as cores e a pulseira.
3. Envie até oito fotos por envio, em JPG, PNG, WebP ou AVIF, com até 20 MB e
   40 megapixels por arquivo. Registre autor/fornecedor e autorização comercial.
4. Confirme a disponibilidade real e registre como ela foi verificada.
5. Salve. O painel preserva os originais, gera WebP responsivo e publica
   automaticamente somente se todos os requisitos forem satisfeitos.

Dados parciais continuam em rascunho. Preços aprovados não são editáveis nesse
formulário. Ao trocar de variante, substitua a galeria para evitar fotos de outro
SKU. Uma troca de referência ou variante revisa a oferta e invalida suas linhas
antigas no carrinho. Cada recebimento mantém autor, horário, comprovantes,
originais, cópias anteriores e resultado em `midias-instagram/recebidos/`, fora
de `static/` e do Git. O serviço mantém o bloqueio de recebimentos simultâneos
e verifica alterações concorrentes antes de gravar os arquivos.

A importação em lote continua disponível:

```powershell
python manage.py import_store_media
python manage.py import_store_media --apply
python manage.py publish_ready_products
python manage.py publish_ready_products --apply
```

Sem `--apply`, os comandos simulam. O importador lê
`midias-instagram/manifest.json`; use o exemplo existente nessa pasta e informe
produto e variante correspondentes. O publicador preserva preços e aprovações.
Consulte [importação](docs/MEDIA_IMPORT.md), [mídias](docs/MEDIA_GUIDELINES.md) e
[publicação](docs/POEDAGAR_PUBLICATION.md). O comando `apply_reference_prices`
continua exigindo evidência recente e autorização expressa; não é necessário
reaplicar preços para cadastrar fotos ou publicar uma oferta já aprovada.

## Testes

```powershell
python manage.py check
python manage.py test
python manage.py audit_storefront
node --check static/js/storefront.js
node --check static/js/catalog-manager.js
```

Os testes de domínio ficam em `loja/tests/`. Os dois testes de navegador são
habilitados com `VRAS_BROWSER_QA=1` e usam arquivos e usuários fictícios isolados:

```powershell
$env:VRAS_BROWSER_QA='1'
python manage.py test loja.tests.catalog.test_variants.GalleryBrowserTests loja.tests.management_portal.test_browser.CatalogReceiptBrowserTests
Remove-Item Env:VRAS_BROWSER_QA
```

Eles exigem um Chrome de QA com perfil isolado e CDP local na porta 9333.
O QA da vitrine existente usa `node scripts/browser_qa.mjs` com Django ativo;
`QA_BASE_URL` e `QA_DEBUG_URL` configuram os endereços. Veja os comandos completos,
os testes por domínio e limites no [guia de testes](docs/TESTING_GUIDE.md).
Os relatórios e screenshots ficam em `artifacts/`, ignorado pelo Git.

## Estáticos e publicação

CSS ativo: `premium.css` e `catalog-manager.css`. JavaScript ativo:
`storefront.js` e `catalog-manager.js`. Fontes locais, fotos, nomes e caminhos
existentes foram preservados. Arquivos legados permanecem arquivados, sem serem
incluídos automaticamente na interface ou na coleta de estáticos.

O finder `loja.media.staticfiles.ApprovedMediaFinder` continua bloqueando imagens
e vídeos sem autorização. Em produção, execute
`python manage.py collectstatic --noinput` e sirva somente `STATIC_ROOT`
(`staticfiles/`), nunca toda a pasta de arquivo `static/`. Use um servidor
WSGI/ASGI apropriado com `config.wsgi:application` ou `config.asgi:application`.
Banco, comprovantes, originais e segredos ficam fora da área pública.
Confira [o checklist](docs/RELEASE_CHECKLIST.md) antes de disponibilizar ofertas.

## English

This Django MTV storefront keeps the `loja` app identity and existing public
URLs. Internal packages separate catalog queries, price approval, publication,
session cart, owner intake and authorized media processing. JSON remains the
catalog storage; SQLite retains accounts and sessions. All twelve Poedagar
models retain their approved prices and current draft state.

Install with `python -m pip install -r requirements.txt`, run
`python manage.py runserver 127.0.0.1:8001`, and validate with
`python manage.py check`, `python manage.py test` and
`python manage.py audit_storefront`. Owners use `/gestao/catalogo/` to confirm
real variants, upload authorized photos and publish complete offers. See the
[architecture](docs/ARCHITECTURE.md), [test guide](docs/TESTING_GUIDE.md) and
[refactor report](docs/REFACTOR_REPORT.md) for boundaries, validation and limitations.
