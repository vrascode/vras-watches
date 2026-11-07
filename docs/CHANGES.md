# Arquivos e entregas

## Configuracao

- `.env.example`: referencia de variaveis, sem credenciais.
- `.gitignore`: segredos, saida estatica e artefatos locais.
- `config/settings.py`: ambiente, HTTPS, cookies, SEO e coleta de midias aprovadas.
- `requirements.txt`: versao Django instalada e testada.
- `db.sqlite3`: removido somente do rastreamento Git; arquivo local preservado.

## Backend

- `loja/services.py`: Decimal, ordenacao, busca normalizada, midias opcionais e quantidades.
- `loja/views.py`: rotas, carrinho, respostas JSON, redirecionamento validado, SEO e cache.
- `loja/urls.py`: preservacao das rotas anteriores e novas rotas de quantidade/SEO.
- `loja/context_processors.py`: contador, identidade, canonical e links configuraveis.
- `loja/media.py`: autorizacao, caminho local, poster, legendas e procedencia.
- `loja/staticfiles.py`: arquivo legado nao e publicado automaticamente.
- `loja/management/__init__.py` e `loja/management/commands/__init__.py`: pacotes de comandos.
- `loja/management/commands/audit_storefront.py`: auditoria de catalogo/midias e inventario.
- `loja/templatetags/__init__.py` e `loja/templatetags/store_tags.py`: JSON-LD com escape seguro.
- `data/media.json`: manifesto inicialmente vazio, sem autorizacoes presumidas.

## Interface

- `loja/templates/loja/base.html`: navegacao, menu mobile, metatags, rodape e modal de zoom.
- `loja/templates/loja/home.html`: hero, destaques, editorial, colecoes e social condicionais.
- `loja/templates/loja/products.html`: busca, categorias, ordenacao e estado vazio.
- `loja/templates/loja/product_detail.html`: galeria, zoom, videos opcionais, descricao e relacionados.
- `loja/templates/loja/cart.html`: quantidades, remocao integral e total do servidor.
- `loja/templates/loja/_product_card.html`: componente compartilhado do catalogo.
- `loja/templates/loja/_video.html`: video local, poster, controles e fallback.
- `loja/templates/loja/sitemap.xml`: sitemap somente com origem oficial configurada.
- `loja/templates/404.html` e `loja/templates/500.html`: erros de producao.
- `static/css/premium.css`: identidade proposta, layouts responsivos e movimento reduzido.
- `static/js/storefront.js`: menu, teclado, carrinho incremental, galeria, compartilhamento e videos.

## Testes e Documentacao

- `loja/tests.py`: 53 testes automatizados.
- `scripts/browser_qa.mjs`: QA com Chrome real e relatorio/screenshots locais.
- `README.md`: execucao, cadastro, midias, ambiente, testes e deploy.
- `docs/ANALYSIS.md`: analise inicial, restricoes e decisoes.
- `docs/INSTAGRAM_MEDIA.md`: fontes, autorizacao, pendencias e fluxo de atualizacao.
- `docs/MEDIA_INVENTORY.csv`: 580 registros individuais do arquivo visual.
- `docs/VALIDATION.md`: resultados, avisos e limites do QA.
- `docs/CHANGES.md`: este registro.

## Preservacao

O diff contra o baseline `72264fa` confirmou que `data/products.json`, `static/img/` e `static/fonts/` nao mudaram. Nenhum dos 12 produtos ou 580 arquivos visuais foi removido. Codigo antigo de estilo/popup permaneceu no disco, sem ser carregado pelo novo storefront. Os contatos existentes foram mantidos e a confirmacao externa foi registrada como pendencia.

## Commits

- `2034236` - `fix(security): configure environment and publish only approved media`
- `ae45693` - `feat(store): enhance catalog cart and configurable SEO`
- `85ab4dd` - `feat(ui): redesign responsive storefront and video experiences`
- `b886b98` - `test(store): cover catalog cart media and browser workflows`
- O commit de documentacao que inclui este arquivo: `docs: record redesign media provenance and deployment workflow`.

Todos sao locais na branch main. Nenhum push ou deploy publico foi executado. O resultado visual permanece pendente de fotos, videos e identidade oficial fornecidos ou autorizados pelo proprietario; nao se declara uma home cinematografica preenchida com conteudo real.
