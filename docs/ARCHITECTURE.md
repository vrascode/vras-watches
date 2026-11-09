# Arquitetura MTV / MVC da VRAS Watches

## Decisão: um app Django, múltiplos domínios

`INSTALLED_APPS` continua registrando `loja`. `ROOT_URLCONF` permanece
`config.urls`; ASGI, WSGI, SQLite e middleware continuam com os mesmos contratos.
A separação é feita por pacotes internos; eles não são novos apps Django.
Não há alteração de app label, tabelas, content types, permissões ou migrações.
Não foram criados modelos artificiais para representar arquivos JSON.

No vocabulário MVC, as views Django recebem a requisição e atuam como
controllers; templates são a apresentação. Regras de negócio pertencem aos
serviços e validações dos domínios. Dados de produto continuam em JSON;
usuários, autenticação e sessões continuam nos modelos nativos do Django.

## Responsabilidades e dependências

| Módulo | Responsabilidade e dependências |
| --- | --- |
| `config/` | Configuração do projeto, conexão SQLite, templates, estáticos e entrada HTTP |
| `loja/catalog/repository.py` | Fonte única da localização do catálogo; leitura fresca com Decimal quando solicitado |
| `loja/catalog/services.py` | Produtos visíveis, busca, categorias, coleções, galerias e navegação por variantes |
| `loja/catalog/validation.py` | Identidade/referência, variante, oferta, galeria do SKU e requisitos de publicação |
| `loja/catalog/pricing.py` | Evidência e aprovação exata dos preços por variante; sem consultas de rede |
| `loja/catalog/publication.py` | Simulação e transição de rascunho apto para publicado, comparação de arquivos e gravação atômica |
| `loja/catalog/views.py` | Entrada HTTP do catálogo, detalhes, metadados e respostas |
| `loja/cart/services.py` | Validação das linhas, revisão da oferta, quantidades, subtotais e totais Decimal |
| `loja/cart/views.py` | POSTs, respostas HTML/JSON, CSRF e redirecionamento validado |
| `loja/storefront/` | Home, robots, sitemap e contexto compartilhado da interface |
| `loja/management_portal/forms.py` | Validação dos campos, confirmações e limites de upload |
| `loja/management_portal/services.py` | Recebimentos privados, comprovantes, revisões, importação e publicação pelo navegador |
| `loja/management_portal/views.py` | Autorização staff, formulários, mensagens e respostas da gestão |
| `loja/media/assets.py` | Autorização, caminhos locais, manifesto e seleção de mídias publicáveis |
| `loja/media/import_service.py` | Validação de lote e vínculo exato produto/variante; prepara os resultados em memória |
| `loja/media/processing.py` | Orientação/perfil de cor, proporções e rendições WebP; sem corte ou ampliação |
| `loja/media/staticfiles.py` | Finder restrito aos arquivos permitidos, tanto no desenvolvimento como no collectstatic |
| `loja/management/commands/` | Interface CLI e tarefas administrativas; publicação delegada ao serviço de domínio |
| `loja/utils.py` | Normalização textual e apresentação de moeda compartilhadas |

Fluxo público: URL → view do domínio → serviço → repositório/mídias → template.
Fluxo de gestão: usuário staff → form validado → recebimento privado → importação
em memória → gravação em rascunho → serviço de publicação → recibo atualizado.
O mesmo serviço publica pelo navegador e por `manage.py publish_ready_products`.
O serviço não precisa interpretar a saída textual de um comando Django.

O catálogo depende de validação, preços, repositório e mídias. O carrinho depende
do catálogo publicado. O portal coordena catálogo, importação e publicação.
Mídias não dependem de views. Evitamos classes genéricas, interfaces sem uso,
novos apps, repositórios para o ORM nativo e pastas vazias.

## Persistência e compatibilidade

`data/products.json`, `data/media.json`, evidências, aprovações, backups,
originais privados e fotografias não foram regravados durante a reorganização.
`db.sqlite3` não foi removido, recriado ou migrado. As regras existentes de
concorrência e recuperação de recebimentos foram preservadas.

O recebimento salva antes os dados em rascunho, depois o manifesto, e só então
tenta publicar. Isso evita expor uma oferta parcialmente atualizada. Não se
trata de uma transação ACID entre múltiplos arquivos. Há bloqueio exclusivo dos
recebimentos e comparações de conteúdo; coordenação entre múltiplos processos
e comandos continua tendo os limites do armazenamento em arquivos existente.
Uma evolução para banco exige projeto e migração próprios.

As chaves do carrinho permanecem `cart`, `cart_catalog_generation`,
`cart_catalog_updated` e `cart_offer_versions`. Reconciliação não limpa a sessão
inteira: preserva autenticação e referências históricas. O namespace `loja:`
e os nomes das 12 rotas da aplicação permanecem iguais; os pacotes `urls.py`
fornecem listas compostas no roteador original, sem namespaces adicionais.

## Templates e estáticos

`TEMPLATES[0][DIRS]` aponta para `BASE_DIR / "templates"`; `APP_DIRS=True`
continua encontrando `loja/templates/loja/`. A base compartilhada está em
`templates/base.html`; cabeçalho, rodapé, avisos, zoom e mídia ficam em
`templates/components/`. Templates de página e cards/galerias específicos do
catálogo ficam separados por domínio dentro do diretório do app.
O formulário e o login da gestão têm sua própria base.

Os diretórios `static/css`, `static/js`, `static/img` e `static/fonts` já tinham
responsabilidades coerentes. Mantivemos os nomes, URLs, conteúdo e arquivo
legado. O finder foi realocado, não substituído pelo finder irrestrito padrão.
Em produção, publique apenas o resultado filtrado de `collectstatic`.

## Testes e evolução

`loja/tests/{catalog,cart,media,storefront,management_portal,integration}` contém
os testes; `loja/tests/support` guarda a fixture do catálogo arquivado.
Patches de testes apontam para os novos donos das regras e caminhos, sem mocks
que liberem o catálogo real. Os dois testes de navegador usam arquivos temporários
e banco de teste; não publicam os rascunhos comerciais.

Para novas regras: adicione-as ao serviço/validação correspondente, exercite os
casos de negócio e mantenha as views pequenas. Mudanças de persistência ou
aprovação comercial não pertencem a uma refatoração estrutural.

## English architecture summary

One Django app retains its app label, permissions, SQLite database and URL
namespace. Domain packages own catalog rules, pricing, publication, cart,
storefront, owner intake and authorized media. HTTP views coordinate forms,
services and rendered templates. A small JSON repository centralizes catalog
reads; no artificial ORM models or repository classes were introduced.
Publication is shared by CLI and browser intake. Existing session keys and
commercial data are preserved. File writes retain the original locking and
content checks; multiple JSON files are not an ACID transaction.
