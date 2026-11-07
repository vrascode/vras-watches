# Procedencia e fluxo de midias VRAS

## Fontes consultadas

- Perfil fornecido pelo proprietario: https://www.instagram.com/usevras/
- Repositorio indicado e confirmado pelo remoto Git: https://github.com/vrascode/vras-watches
- Arquivo local: `static/img/products/` do checkout, baseline `72264fa`.
- Catalogo local: `data/products.json` (12 produtos, referencias originais preservadas).

Em 2026-11-06, a abertura publica do Instagram pela ferramenta de navegacao retornou `Failed to fetch / Cache miss`. A busca complementar nao retornou publicacoes oficiais verificaveis. O mesmo fetch do GitHub nao retornou conteudo; o checkout local foi a fonte de analise do codigo. Isso e uma limitacao desta consulta, nao uma afirmacao de que a conta ou o repositorio nao existem ou sejam privados.

Nao foram disponibilizados login autorizado, token da API, exportacao de conta, pasta com originais da VRAS ou comprovacoes de licenca. Nao se tentou contornar autenticacao ou bloqueios. Nao ha scraping em tempo real.

## Inventario completo

O arquivo [MEDIA_INVENTORY.csv](MEDIA_INVENTORY.csv) registra individualmente os 580 arquivos visuais preexistentes, com formato, tamanho, SHA-256, produto associado quando conhecido, origem, destino e status. Nao foi inferida uma publicacao do Instagram a partir do nome de arquivo. Variantes nao confirmadas nao foram tratadas como novos angulos do mesmo modelo.

| Grupo | Encontrado | Decisao |
| --- | --- | --- |
| PNG | 278 | Preservados no arquivo, bloqueados ate confirmacao |
| JPG | 267 | Preservados no arquivo, bloqueados ate confirmacao |
| WebP | 32 | Preservados no arquivo, bloqueados ate confirmacao |
| SVG legado | 3 | Nao utilizados como identidade VRAS |
| MP4 / WebM / MOV | 0 | Nenhum video real publicado |
| Logo VRAS confirmado | 0 | Nome da marca em texto, sem alegar logo oficial |
| Posts com permalink e autoria verificados | 0 | Convite ao perfil, sem miniaturas inventadas |

Exemplos auditados: `41_1200x.webp` exibe VOXO no mostrador; `DSC00761.png`, hero anterior, exibe relogios de outra marca; `Gemini_Generated_Image_*` indica possivel origem sintetica no proprio nome. Outros ativos, inclusive o favicon antigo, tambem nao tiveram procedencia VRAS demonstrada. Nenhum arquivo foi apagado ou renomeado.

## Midias efetivamente usadas

Nenhuma fotografia ou video do arquivo legado foi aprovado para a nova interface. Nao ha dependencia de URLs temporarias do Instagram. O nome da marca e textos do briefing sao renderizados em HTML; a fonte Crimson Text foi reaproveitada de `static/fonts/`, nao identificada como fonte oficial da marca.

Sem aprovacao, imagens legadas nao sao encontradas pelo servidor de estaticos nem coletadas para deploy. A coleta inclui os estaticos administrativos padrao do Django, que nao sao fotografias ou identidade da loja.

## Arquivos e informacoes pendentes

1. Logotipo oficial raster, com versoes para fundo claro/escuro e favicon autorizado.
2. Video horizontal da marca para hero, com poster; versao vertical ou enquadramento aprovado para mobile.
3. Video editorial mostrando detalhes reais e poster correspondente.
4. Fotos de cada um dos 12 modelos, com associacao inequivoca por ID e confirmacao dos nomes/precos.
5. Segunda foto e videos adicionais por modelo, quando existirem. Nao reutilizar uma variante de tamanho como segundo angulo.
6. Foto/campanha e respectiva chamada aprovadas; sem inventar nome, data ou lancamento.
7. Originais de Reels/fotos e permalinks exatos do feed @usevras, com licenca ou autorizacao registrada.
8. Legendas/transcricoes e autorizacao de audio, pessoas e campanhas quando aplicavel.
9. Confirmacao se o arquivo VOXO faz parte de uma operacao autorizada da VRAS. Ate essa confirmacao, permanece bloqueado.
10. Biografia, posicionamento, cores e tipografia reais para validar a proposta visual.
11. Validacao externa dos contatos preservados e documentos legais oficiais para privacidade, trocas e termos.
12. Dominio oficial, configuracao HTTPS, operacao de entrega e eventual gateway. Nenhum foi presumido.

## Associacao de destinos

| Entrada em data/media.json | Destino |
| --- | --- |
| `brand.logo` | Header com imagem oficial |
| `hero.image` / `hero.video` | Hero com poster/fallback e preload seletivo |
| `editorial.image` / `editorial.video` | Cada detalhe importa |
| `campaign.image` / `campaign.video` | Campanha visual condicional |
| `products.<id>.cover` / `images` / `videos` | Capa, segunda foto, galeria, preview e detalhe do produto |
| `instagram[]` | Galeria social local com link para publicacao original |
| `policies` | Links HTTPS oficiais do rodape |

Cada objeto publicado precisa de caminho local existente, `origem` documentada e `autorizado: true`. Videos tambem precisam de poster aprovado. O flag registra uma decisao humana, nao substitui direitos de uso. Nao altere esse flag para fazer uma imagem de concorrente aparecer.

## Como atualizar

Receber os originais por um meio autorizado; confirmar titularidade e contexto; registrar origem e comprovacao; exportar arquivos otimizados sem alterar a aparencia real do produto; salva-los nas pastas indicadas no README; cadastrar o manifesto; executar auditoria e testes; conferir no navegador qualidade, contraste, enquadramento e reproducao; regenerar o inventario; revisar a diferenca no Git. Publicar somente apos aprovacao do proprietario.

Se houver API oficial autorizada futuramente, usar o fluxo permitido para obter os arquivos e metadados, respeitando permissao, expiracao e termos. O site deve continuar usando a copia local autorizada e o manifesto, independentemente da disponibilidade da API. Nunca commitar tokens.
