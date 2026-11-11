# Catálogo premium VRAS / Premium catalog

Django existente preservado. Tema próprio em grafite e champanhe, seleção por
cor, ficha técnica, conteúdo editorial, miniaturas, zoom, controle de vídeo,
acessibilidade por teclado e preferência por movimento reduzido.

## Executar / Run

Use as dependências de requirements.txt e o interpretador configurado para
Django 6.0.6 / Pillow 13.0.0 neste projeto. A instalação padrão do Django 6
requer Python 3.12 ou posterior.

```powershell
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

- Página de apresentação: /colecao/montelux/
- Seleção azul: /colecao/montelux/?cor=Azul
- Catálogo: /produtos/
- Gestão de ofertas: /gestao/catalogo/
- Painel de procedência: /admin/catalogo-referencia/
- CSV protegido: /admin/catalogo-referencia/inventario.csv

As páginas de coleção podem apresentar modelos ainda indisponíveis. Esses
registros exibem o preço VRAS autorizado e a disponibilidade pendente. A compra
fica habilitada quando os requisitos de oferta, identificação e mídia do
projeto são atendidos. Uma URL de coleção não permite adicionar rascunhos ao
carrinho. As páginas normais de venda continuam em /produto/<id>/.

Pagamento online/checkout transacional não está implementado nesta base; o
carrinho existente mantém o encaminhamento de atendimento VRAS. A integração
de pagamentos não foi solicitada nem simulada.

## Importar / Import

Simular a leitura das observações já registradas:

```powershell
python manage.py import_reference_catalog
python manage.py import_reference_catalog --model Montelux --apply
python manage.py audit_reference_catalog
```

Consultar novamente a página pública e importar preço unitário, IDs de variantes,
imagens, versões de vídeo e mídias editoriais/globais encontradas no HTML:

```powershell
python manage.py import_reference_catalog --refresh --url https://poedagareco.com/products/relogio-poedagar-montelux%C2%AE --apply --download-media --publish-ready
```

Descobrir os demais relógios pela listagem pública paginada:

```powershell
python manage.py import_reference_catalog --refresh --discover --apply --download-media --publish-ready
```

--refresh usa os endpoints públicos da Shopify e o HTML da página.
--discover percorre até dez páginas por padrão; --max-pages aceita 1–100.
Uma falha de acesso interrompe a coleta, sem substituir uma observação por
dados inventados. Download exige --apply. A simulação não baixa arquivos.
--publish-ready usa as confirmações já existentes; não inventa estoque,
referência de fabricante ou aprovação física. É possível continuar a
conferência no portal de gestão, como no fluxo anterior.

A importação é incremental: preserva registros anteriores, mantém IDs estáveis,
rejeita variantes repetidas no lote, valida preços positivos e limita alterações
ao subconjunto observado. O preço promocional unitário público é aplicado como
preço VRAS; Pix, preço anterior, cupons e promoções de quantidade não são usados.
O comando anterior de preços ignora os novos registros de outra origem.

## Originais, otimização e associação / Originals and optimization

- Originais: media-originals/<modelo>/<variante-ou-pendente>/<hash-url>/<nome-original>.
- WebP: static/img/products/poedagar/<modelo>/<variante>/<id>-<hash>-<largura>.webp.
- Vídeo otimizado e poster: static/videos/poedagar/<modelo>/<variante>/.
- Inventário versionado: data/reference_media_inventory.json e .csv.
- Galerias publicáveis: data/media.json.

Os bytes originais são preservados e conferidos por SHA256. Reimportações
reutilizam o arquivo se o hash coincide. Um original existente nunca é
sobrescrito por conteúdo diferente. Transformações de largura da CDN são
normalizadas para buscar o original; URLs observadas também ficam registradas.
Imagens recebem orientação EXIF, tratamento de perfil de cor e WebP de qualidade
88, sem ampliar nem cortar, em larguras de até 480/800/1200/1920 pixels.

ffmpeg e ffprobe são ferramentas opcionais externas para vídeos. ffmpeg cria
MP4 H.264 sem áudio, faststart e poster de um quadro real; o arquivo original
permanece intacto. Se a ferramenta estiver ausente, o processamento fica
pendente com erro explícito. Elas não estão instaladas neste ambiente.

Somente uma associação inequívoca de modelo e variante entra na galeria.
Imagens e vídeos de âmbito geral permanecem no inventário para conferência.
O usuário pode completar a variante da entrada após conferir a mídia e executar
novamente a importação. Não se deve atribuir uma cor por adivinhação.

Autorização comercial declarada pelo proprietário e verificação da titularidade
de terceiros são campos separados. Este fluxo registra a autorização recebida,
sem alegar possuir uma licença do titular.

## Verificar / Validate

```powershell
python manage.py check
python manage.py test
python manage.py test loja.tests.reference
python manage.py audit_reference_catalog
python manage.py audit_reference_catalog --strict-media
python manage.py audit_storefront
node --check static/js/storefront.js
node --check static/js/product-experience.js
git diff --check
```

A auditoria estrita falha enquanto houver mídia pendente. Testes usam imagens
geradas apenas dentro de diretórios temporários e confirmações fictícias de
QA. Eles cobrem importação repetida, preço por variante, originais, WebP,
galerias, zoom, troca de cor, linhas de carrinho, preço adulterado, atualização de
preço, painel e restrição de acesso. Nenhum teste publica uma confirmação real.

Há dois testes opcionais já existentes de navegador (VRAS_BROWSER_QA=1), que
dependem de um Chrome com CDP na porta configurada. Neste ambiente, a abertura
de Chrome com depuração remota foi rejeitada pela revisão automática.
Uma tentativa de captura headless sem depuração também falhou na inicialização
de GPU/permissões. Não há evidência visual de navegador nesta execução.
As páginas foram verificadas pelo cliente Django e por HTTP local.

## Commits e push / Commits and push

O plano em docs/premium_commit_plan.json contém 20 grupos de mudanças reais e
não sobrepostos. A gravação de .git/index.lock foi negada e o acesso HTTPS ao
GitHub falhou neste ambiente. Portanto, não há 20 commits novos nem push
confirmado desta implementação.

Em um terminal que tenha as permissões normais do repositório, após conferir os
resultados e executar os testes:

```powershell
python scripts/commit_premium_catalog.py
python scripts/commit_premium_catalog.py --execute --push
```

Sem --execute o script apenas valida e lista o plano. Ele rejeita commits
vazios, alterações fora do plano, arquivos já staged, branch incorreta e
histórico divergente. Usa a identidade Git configurada, permite retomar somente
o prefixo exato dos commits previstos, verifica ancestralidade do remoto e
não faz force-push.

## English

This is an additive import and an original VRAS storefront design. The 12
existing records are unchanged; 48 observed color variants were added across
13 retailer models. Montelux uses the observed R$259 unit price. Source facts,
unconfirmed platform IDs, unknown dimensions, owner-declared authorization,
and download failures remain explicit in structured data.

Collection pages provide an honest preview of unavailable offers. Purchasing
continues to require the existing publication checks. The end-to-end tests
publish only isolated QA fixtures and verify gallery associations, color
selection, separate cart lines and server-calculated prices. Online payment
processing remains outside the existing application's capabilities.

The execution environment blocked external downloads, Git index writes and
the GitHub connection. Browser QA also could not run. The import command and
reviewed 20-commit runner are reusable when those environment capabilities
are available. See PORTFOLIO_PROGRESS.md for the exact final validation results.

## Continuação: tentativa sem alterar preços / Retry without price changes

Para tentar somente as mídias e manter os produtos, os preços aprovados e SQLite:

```powershell
python manage.py retry_reference_media --model Montelux
python manage.py retry_reference_media --model Montelux --apply --publish-ready --report artifacts/catalog-continuation/media-retry.json
```

O primeiro comando simula. O segundo registra o resultado real por arquivo,
associa apenas mídia processada com arquivo local válido e publica somente
ofertas que já atendam aos requisitos. Restrição local de socket não é tratada
como resposta HTTP do site.

Nesta continuação: 247 testes aprovados, dois opcionais ignorados; zero
downloads, zero ofertas publicadas e zero commits enviados. A leitura pela
integração GitHub funcionou, mas a escrita exigiu aprovação indisponível sob a
política never. Relatório atual: [CATALOG_PUBLICATION_STATUS.md](CATALOG_PUBLICATION_STATUS.md).

English: use retry_reference_media to retry only media while preserving all
prices and catalogue records. It never writes SQLite or invents availability.
See the linked report for verified counts and execution restrictions.
