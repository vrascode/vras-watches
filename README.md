# VRAS Watches

Loja Django com catalogo JSON, templates renderizados no servidor e carrinho persistido por sessao. Redesign editorial em preto, branco e grafite, com tipografia Crimson Text local e detalhes discretos em dourado. Sem React, bundler ou dependencias JavaScript em producao.

## Estado das midias

**A identidade visual oficial ainda precisa ser validada pelo proprietario.** O Instagram nao ficou acessivel na consulta publica. O arquivo local contem imagens de outras marcas e imagens com nomes indicando geracao por IA. Nenhuma foi reapresentada como fotografia oficial da VRAS.

- Os 12 produtos, precos, descricoes e referencias originais foram preservados integralmente em `data/products.json`.
- As fotos legadas estao bloqueadas, nao apagadas. Nao sao servidas pelo finder local nem incluidas no `collectstatic`.
- Nao ha videos, logotipo VRAS confirmado ou posts com procedencia confirmada no repositorio.
- Hero, editorial, campanha, previews e galeria social aceitam midias autorizadas. Sem elas, o hero e tipografico, o catalogo mostra um estado de fotografia indisponivel e nao ha feed ficticio.
- Os textos editoriais novos sao propostas baseadas no briefing, nao transcricoes da bio oficial.
- Leia [o registro de midias](docs/INSTAGRAM_MEDIA.md), [o inventario completo](docs/MEDIA_INVENTORY.csv) e [a analise inicial](docs/ANALYSIS.md).

## Tecnologias

- Python 3.12+; Django 6.0.6 (versao instalada e testada).
- SQLite para desenvolvimento; sessoes Django no banco.
- HTML5, CSS responsivo, JavaScript nativo, IntersectionObserver e dialog.
- Node 22+ e Chrome/Chromium apenas para QA opcional. O site nao precisa de Node.

## Executar Localmente

Abra **a pasta que contem `manage.py`** no VS Code. No seu computador:

```powershell
cd C:\Users\mathe\Downloads\saveweb2zip-com-usevoxo-com-br\vras-watches
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Se o PowerShell bloquear a ativacao, use `.\.venv\Scripts\python.exe` diretamente em lugar de `python`, sem mudar a politica de execucao do sistema.

Acesse http://127.0.0.1:8000/. Para outra porta, use `runserver 127.0.0.1:8001`. Pare com Ctrl+C no terminal do servidor. O servidor de desenvolvimento nao deve ser exposto na internet.

## Rotas e Comportamento

| Rota | Funcao |
| --- | --- |
| `/` | Destaques, editorial, colecoes e acesso ao Instagram |
| `/produtos/` | Busca, categoria e ordenacao |
| `/produto/<id>/` | Galeria, zoom, videos opcionais, compartilhamento e relacionados |
| `/carrinho/` | Quantidades, remocao de linha e total calculado com Decimal |
| `/carrinho/adicionar/<id>/` | POST: adiciona uma unidade |
| `/carrinho/remover/<id>/` | POST: diminui uma unidade (compatibilidade original) |
| `/carrinho/atualizar/<id>/` | POST: `quantity` de 0 a 99; zero remove a linha |
| `/robots.txt`, `/sitemap.xml` | SEO configuravel por SITE_URL |

Filtros: `?categoria=Maestro&q=imperium&ordem=preco_asc`. Ordenacoes: `destaques`, `preco_asc`, `preco_desc`, `nome`, `nome_desc`. Busca ignora caixa e acentos; navegacao por categoria preserva busca e ordenacao. Carrinho funciona sem JavaScript e oferece feedback incremental quando JS esta disponivel.

**Nao existe checkout ou gateway de pagamento.** O botao de contato nao cria um pedido, nao transmite automaticamente o carrinho e nao cobra o cliente. O popup antigo de cadastro, que nao persistia e-mails, foi desativado. Nao foi implementado um cadastro ficticio.

## Estrutura

```text
config/                     Configuracao Django e URLs
loja/services.py            Catalogo, filtros, Decimal e carrinho
loja/media.py               Validacao de midias locais autorizadas
loja/staticfiles.py         Publicacao restrita a midias aprovadas
loja/views.py               Paginas, POSTs, robots e sitemap
loja/management/commands/   Auditoria e inventario de midias
loja/templates/             Templates novos e arquivos legados preservados
loja/tests.py               Testes de catalogo, carrinho, midias e deploy
data/products.json          Catalogo original, 12 produtos
data/media.json             Manifesto de midias aprovadas e links institucionais
static/css/premium.css      Estilo ativo
static/js/storefront.js     Interacoes ativas
static/fonts/               Fontes locais preexistentes
static/img/products/        Arquivo original preservado, bloqueado por padrao
docs/                       Analise, procedencia e validacao
scripts/browser_qa.mjs      QA opcional com Chrome DevTools Protocol
artifacts/                  Relatorios e screenshots locais, ignorados pelo Git
staticfiles/                Saida de collectstatic, ignorada pelo Git
```

Os arquivos antigos `theme.css`, `style.css`, `swiper-reviews.min.css`, `welcome-modal.css`, `welcome-modal.js` e `_welcome_modal.html` foram preservados como arquivo, mas nao sao carregados. CSS/JS legados tambem sao excluidos da coleta de estaticos. O banco local continua no disco, mas saiu do rastreamento Git; o historico anterior nao foi reescrito.

## Adicionar Produtos

Edite o array `data/products.json`. Campos obrigatorios: `id` inteiro positivo unico, `nome`, `preco` com ate duas casas decimais, `descricao`, `imagem` (referencia legada) e `categoria`. Use `destaque: true` para a vitrine. Categorias existentes: `Classicos`, `Maestro`, `Best Sellers`, `Lancamentos`, `Esportivos`.

Campos opcionais: `descricao_detalhada`, `especificacoes` (objeto de valores reais), `capa` (objeto de midia), `galeria` (array de imagens) e `videos` (array de videos). Prefira associar midias pelo ID em `data/media.json`, sem modificar o catalogo legado. Nunca deduza especificacoes a partir de uma imagem nem publique uma imagem apenas por ela estar no repositorio.

Execute `python manage.py audit_storefront` depois da edicao.

## Cadastrar Fotos e Videos

Crie somente as pastas necessarias quando receber os arquivos originais:

```text
static/img/brand/            Logotipo raster oficial
static/img/campaigns/        Posters e fotos editoriais
static/img/products/         Fotos de produto
static/img/instagram/        Miniaturas sociais
static/videos/hero/          Videos de abertura e editoriais
static/videos/products/      Videos por modelo
static/videos/instagram/     Reels autorizados
```

Todos os caminhos sao relativos a `static/`. Cada midia requer `src`, `origem` e `autorizado: true`. Isso registra a confirmacao humana do proprietario; nao prova direitos automaticamente. Use `alt` descritivo. Imagens: JPG, PNG, WebP ou AVIF. Videos: MP4 ou WebM, obrigatoriamente com poster local autorizado.

Exemplo de estrutura, **apenas depois de receber e autorizar esses arquivos**:

```json
{
  "products": {
    "1": {
      "images": [
        {"src": "img/products/flyback-frente.webp", "alt": "Flyback visto de frente", "origem": "Arquivo original fornecido pelo proprietario; registrar comprovacao", "autorizado": true}
      ],
      "videos": [
        {
          "src": "videos/products/flyback-detalhes.mp4",
          "origem": "Video original fornecido pelo proprietario; registrar comprovacao",
          "autorizado": true,
          "poster": {"src": "img/products/flyback-frente.webp", "origem": "Original autorizado pelo proprietario", "autorizado": true}
        }
      ]
    }
  }
}
```

Mescle as entradas no manifesto existente; nao substitua outras secoes. `brand.logo` recebe um objeto de imagem. `hero`, `editorial` e `campaign` recebem `image` e/ou `video`. A primeira imagem vira capa; a segunda aparece no hover. Multiplos videos aparecem na galeria do produto. Um poster tambem pode servir como capa quando so ha video.

Videos decorativos sao silenciosos e em loop, carregados por visibilidade; previews so iniciam com mouse. Videos interativos tem controles nativos. Apenas um video reproduz por vez, ha pausa fora da tela e com aba oculta, suporte a movimento reduzido e fallback em erro. Videos com fala precisam de legendas locais `.vtt`: cadastre um objeto autorizado em `captions`. Versoes para conexao lenta, audio/legendas, codec e enquadramento devem ser validados com os arquivos reais.

Prefira exportacoes WebP/AVIF compactas e MP4 H.264 ou WebM compativel, com metadados de reproducao progressiva. Nao gere imagens falsas do produto. Nao duplique variantes so para preencher a galeria.

## Atualizar o Instagram

Adicione a `instagram` uma lista de objetos com `permalink` da publicacao oficial e `image` e/ou `video` no mesmo formato acima. So sao aceitos links HTTPS de `/p/`, `/reel/` ou `/tv/` do Instagram. O caminho nao comprova que o post pertence a @usevras: confira manualmente a conta e a autorizacao. Todas as midias ficam locais; nao ha scraping, token, feed ao vivo nem dependencia da API. Sem posts autorizados, a secao mostra apenas o convite para o perfil, nunca uma galeria inventada.

Cadastre em `policies` apenas links HTTPS aprovados pelo proprietario, por exemplo chaves `Politica de Privacidade`, `Trocas e Devolucoes`, `Termos de Uso`. Sem documentos, os links ficam ausentes. Contatos anteriores foram preservados; sua titularidade externa ainda precisa de confirmacao.

## Variaveis de Ambiente

`.env.example` e uma referencia. O Django **nao carrega `.env` automaticamente**. Configure o ambiente do processo ou do provedor. Nao versione segredos.

| Variavel | Desenvolvimento | Producao |
| --- | --- | --- |
| `DJANGO_DEBUG` | `true` por padrao | Definir `false` explicitamente |
| `DJANGO_SECRET_KEY` | Chave efemera por processo se ausente | Obrigatoria, aleatoria, persistente e secreta |
| `DJANGO_ALLOWED_HOSTS` | `127.0.0.1,localhost` | Lista dos hosts reais, obrigatoria |
| `SITE_URL` | Vazio | Origem oficial completa, sem caminho |
| `HTTPS_ENABLED` | `false` | `true` por padrao com DEBUG=false |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Vazio | Origens HTTPS confiaveis quando necessario |

No PowerShell, use `$env:DJANGO_DEBUG='true'`. Gere a chave com `python -c "import secrets; print(secrets.token_urlsafe(64))"` em um terminal privado. Nao cole credenciais em commits. A configuracao falha em producao sem chave ou hosts. Cookies seguros, redirecionamento HTTPS, HSTS de um ano, anti-clickjacking e CSRF sao mantidos. HSTS de subdominios e preload ficam desativados de proposito ate haver auditoria do dominio.

Sem `SITE_URL`, canonical e sitemap com URLs absolutas ficam omitidos; nenhum dominio de producao e inventado. JSON-LD Product so e emitido com URL configurada e fotografia autorizada, sem avaliacoes, estoque ou garantias presumidos. HTML personalizado pelo carrinho nao recebe cache compartilhado; robots/sitemap recebem cache de uma hora.

## Testes

```powershell
python manage.py check
python manage.py test --verbosity 2
python manage.py audit_storefront --write-inventory
node --check static/js/storefront.js
```

O comando de inventario gera `docs/MEDIA_INVENTORY.csv`, incluindo hash SHA-256, formato, tamanho, associacao conhecida, origem, destino e status de cada arquivo. Valida referencias, autorizacao, IDs e precos. Nao certifica autoria, conteudo, codec ou integridade visual automaticamente.

QA de navegador opcional, sem dependencias npm: inicie Chrome/Chromium com perfil **isolado** e depuracao restrita a `127.0.0.1:9333`, mantenha Django na porta 8000 e execute `node scripts/browser_qa.mjs`. Configure `QA_BASE_URL` e `QA_DEBUG_URL` para outras portas. Nunca exponha a porta de depuracao nem reutilize seu perfil pessoal. O script salva screenshots e relatorio em `artifacts/`, testa cinco larguras e o fluxo de carrinho, menu, teclado e movimento reduzido. Veja limites e resultados em [VALIDATION.md](docs/VALIDATION.md).

## Preparar Deploy

1. Confirmar dominio, identidade, contatos, catalogo, direitos de midia e politicas antes de vender.
2. Definir as variaveis de producao e instalar as dependencias em ambiente virtual. Atualizar patches de seguranca e repetir os testes antes de publicar.
3. Executar `python manage.py migrate`, `python manage.py check --deploy`, `python manage.py test` e `python manage.py audit_storefront`.
4. Executar `python manage.py collectstatic --noinput` em um diretorio de build novo. Caso reutilize uma saida de build, conferir o caminho absoluto de `STATIC_ROOT` antes de usar `--clear`. O finder inclui apenas midias aprovadas, fontes, CSS/JS ativos e estaticos administrativos do Django.
5. Servir `config.wsgi:application` ou `config.asgi:application` com servidor de aplicacao apropriado ao provedor e proxy reverso HTTPS. `runserver` nao serve para producao. Nao ha servidor WSGI de producao incluido nas dependencias.
6. Configurar Nginx/CDN para servir **somente `STATIC_ROOT`**, nunca a pasta de arquivo `static/`. Habilitar compressao e cache longo/immutable para arquivos com hash. Videos precisam de content-type correto e suporte a byte ranges.
7. Manter banco, backups, logs, segredos e perfis de QA fora da area publica. Nao fazer cache compartilhado de HTML com estado de sessao. Configurar monitoramento, backups e permissoes no host.

Se TLS terminar no proxy, configure o reconhecimento de HTTPS apenas depois de garantir que o proxy remove cabecalhos externos e injeta o cabecalho confiavel. Nao foi adicionado `SECURE_PROXY_SSL_HEADER` incondicional. Os dois avisos de `check --deploy` sobre HSTS de subdominios/preload sao esperados ate essa decisao. Nao ha deploy ou push automatico neste trabalho.
