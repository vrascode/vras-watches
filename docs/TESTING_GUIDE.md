# Guia de testes / Testing guide

## Verificação padrão

```powershell
python manage.py check
python manage.py test
python manage.py audit_storefront
node --check static/js/storefront.js
node --check static/js/catalog-manager.js
```

O runner descobre `loja/tests/`. Há testes para catálogo, filtros, identidade,
variantes, preços aprovados, mídia, publicação, carrinho, permissões, formulários,
recebimentos e configuração. Os testes de integração verificam URLs públicas e
preservação da autenticação ao reconciliar um carrinho antigo.

Para executar por domínio:

```powershell
python manage.py test loja.tests.catalog
python manage.py test loja.tests.cart
python manage.py test loja.tests.media
python manage.py test loja.tests.storefront
python manage.py test loja.tests.management_portal
python manage.py test loja.tests.integration
```

Os testes usam banco separado e arquivos temporários. Não é necessário modificar
`data/products.json`, `data/media.json`, preços ou estados de publicação reais.
Fixtures de ofertas fictícias não representam disponibilidade comercial.

## Navegador

Os scripts usam Node 22+ e Chrome/Chromium via CDP, sem dependências npm.
Inicie um navegador de QA com perfil próprio, em outro terminal:

```powershell
& 'C:\Program Files\Google\Chrome\Application\chrome.exe' --headless=new --disable-gpu --remote-debugging-address=127.0.0.1 --remote-debugging-port=9333 --user-data-dir="$PWD/artifacts/runtime/chrome/qa" --no-first-run --no-default-browser-check about:blank
```

Use somente o perfil isolado, nunca o perfil pessoal. Neste ambiente restrito,
o Chrome só permaneceu ativo com `--no-sandbox`; esse argumento foi usado
apenas na execução de QA isolada, não é necessário ao código da aplicação.

Execute os dois fluxos completos com o navegador ativo:

```powershell
$env:VRAS_BROWSER_QA='1'
python manage.py test loja.tests.catalog.test_variants.GalleryBrowserTests loja.tests.management_portal.test_browser.CatalogReceiptBrowserTests
Remove-Item Env:VRAS_BROWSER_QA
```

O Django inicia servidores próprios e um banco de teste. O fluxo da gestão cria
um usuário fictício, entra pelo login, envia fotos temporárias, verifica WebP,
publicação, detalhes, galeria, variantes e carrinho. Não exige criar conta de QA
ou publicar produtos no banco/catálogo existentes. A variável `QA_DEBUG_URL`
altera a porta CDP. Sem a variável de habilitação, esses dois testes são pulados.

Para a vitrine real, inicie `python manage.py runserver 127.0.0.1:8001` e rode:

```powershell
$env:QA_BASE_URL='http://127.0.0.1:8001'
node scripts/browser_qa.mjs
```

A versão atual do catálogo usa o modo de rascunhos do script, que verifica
home, catálogo, carrinho, redirecionamentos aposentados e bloqueio de detalhes
não publicados. Os fluxos com ofertas e galerias publicadas são cobertos pelas
fixtures isoladas. A responsividade cobre 360, 390, 768, 1024 e 1440 pixels;
o fluxo de galeria inclui teclado, zoom e movimento reduzido.
Relatórios JSON e screenshots ficam em
`artifacts/browser/<suite>/runs/<execução>/{reports,screenshots}/`, ignorados
pelo Git. O terminal mostra o diretório da execução. `pre-organization` contém
as evidências anteriores; execuções novas usam data/hora UTC e sufixo único.
Não é necessário configurar manualmente o diretório de saída. Veja
[o guia dos artefatos](../artifacts/README.md).

## Limites

QA de navegador e comparação de screenshots não substituem teste de produção,
validação humana de identidade comercial ou teste com fotografias reais.
Nenhum checkout ou pagamento foi implementado. Consulte os resultados efetivos
da execução em [REFACTOR_REPORT.md](REFACTOR_REPORT.md).

## English

Run the standard commands above or select a domain with
`python manage.py test loja.tests.<domain>`. Browser tests require an isolated
Chrome CDP session and `VRAS_BROWSER_QA=1`; their temporary users, data and images
do not modify the live catalog. `scripts/browser_qa.mjs` checks the current
storefront at `QA_BASE_URL`. Reports and screenshots are local, uniquely named runs under
`artifacts/browser/<suite>/runs/`; previous evidence is preserved.
