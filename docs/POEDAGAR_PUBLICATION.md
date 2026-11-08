# Fotografias e publicação Poedagar

Verificação em 07/11/2026, America/Sao_Paulo (08/11/2026 UTC).
Entrada: `main`, commit `1edf8bf`, sem alterações locais.

## Resultado real

- Fotografias/vídeos incorporados: **0**.
- Variantes físicas confirmadas para venda pela VRAS: **0**.
- Produtos publicados ou disponíveis para compra: **0**.
- Rascunhos: **12**, IDs 13–24.
- Os 12 preços e seus registros de aprovação foram preservados.

`midias-instagram/` contém instruções, exemplos e um manifesto local com 12
entradas pendentes, todas sem autorização. Não contém arquivos de imagem ou vídeo.
As 12 pastas em `static/img/products/poedagar/` contêm somente instruções.
O manifesto público `data/media.json` não tem fotografias autorizadas. Os arquivos
legados não possuem correspondência/autorizações suficientes e não foram usados.
As buscas específicas por Poedagar e VRAS no Drive conectado não retornaram arquivos.
O acesso público ao Instagram foi limitado; nenhuma mídia foi extraída.

`import_store_media --apply` foi executado: zero mídias, zero derivados,
12 entradas sem autorização ignoradas. O novo `publish_ready_products --apply`
também foi executado: zero transições, com os quatro bloqueios abaixo por produto.
Nenhum catálogo, manifesto público ou registro de preço precisou ser regravado.

## Arquivos e informações que faltam

Para **cada modelo que a VRAS realmente oferecer**, é necessário receber:

1. Uma fotografia frontal original real, mostrando exatamente a variante vendida.
   Os caminhos abaixo correspondem às entradas ainda vazias do manifesto local;
   não são arquivos existentes. Outros nomes podem ser usados se o manifesto
   apontar para o arquivo correto.
2. Autoria/origem e comprovação de autorização para uso comercial. A permissão
   deve abranger a utilização pretendida; uma URL de loja não é uma licença.
3. Referência física verdadeira do fabricante, evidência da associação com o
   nome comercial e ficha/manual/fonte HTTPS confiável correspondente. O SKU
   repetido da loja de referência não substitui a referência do relógio.
4. A variante que a VRAS efetivamente vende: cor do mostrador, caixa e pulseira,
   tipo de pulseira e o ID correspondente em `variantes_fonte`, sem escolher uma
   opção apenas para preencher o cadastro.
5. Confirmação expressa de que a VRAS consegue atender à venda dessa variante.
   Disponibilidade na loja de referência não comprova essa capacidade.

| ID | Modelo | Original principal pendente, relativo a `midias-instagram/` |
| --- | --- | --- |
| 13 | Army | `army/frente.jpg` |
| 14 | Deluxe | `deluxe/frente.jpg` |
| 15 | Deluxe Golden | `deluxe-golden/frente.jpg` |
| 16 | Golden Mars | `golden-mars/frente.jpg` |
| 17 | Golden Moon | `golden-moon/frente.jpg` |
| 18 | Golden Neptune | `golden-neptune/frente.jpg` |
| 19 | Golden Star | `golden-star/frente.jpg` |
| 20 | King Royal | `king-royal/frente.jpg` |
| 21 | Machine | `machine/frente.jpg` |
| 22 | Nautilus | `nautilus/frente.jpg` |
| 23 | Signature | `signature/frente.jpg` |
| 24 | Tempus | `tempus/frente.jpg` |

A lista [POEDAGAR_NEW_MEDIA_PENDING.csv](POEDAGAR_NEW_MEDIA_PENDING.csv) relaciona
os 57 IDs de variantes pesquisados e nomes alternativos de arquivo por variante.
**Não é necessário fornecer as 57 variantes**: primeiro confirmar quais a VRAS
oferece. Nenhuma delas foi escolhida nesta etapa. Laterais, verso e vídeos são
opcionais; vídeos precisam de poster autorizado e legendas quando houver fala.
Banner/editorial exigem um original com enquadramento e permissão apropriados;
nenhuma foto de produto inexistente foi usada como substituta.

## Implementação entregue

`python manage.py publish_ready_products` simula a publicação sem reaplicar
preços. `--apply` grava somente a transição `rascunho` → `publicado` dos produtos
que passam em `services.publication_issues`, o mesmo validador da vitrine.
O comando não preenche confirmação de identidade, variante, mídia ou oferta.
Não consulta preços externos nem altera valores ou aprovações existentes.

O relatório JSON informa aptos, publicados, já publicados e bloqueados por ID.
Sem transições, nenhum arquivo é escrito. IDs duplicados/status inválidos são
recusados. Alterações concorrentes detectadas no catálogo ou manifesto de mídia
interrompem a operação; o catálogo é gravado por substituição de arquivo temporário.
Não há opção para forçar publicação ou dispensar algum requisito.

A página inicial passa a mostrar até quatro produtos públicos quando ainda não
há destaques escolhidos manualmente. Os destaques existentes mantêm prioridade.
Isso não modifica `destaque`, categoria, popularidade ou dados comerciais dos
produtos. Rascunhos continuam fora da vitrine, detalhes e carrinho.

Depois de receber e conferir os dados verdadeiros, o fluxo é:

```powershell
python manage.py import_store_media
python manage.py import_store_media --apply
python manage.py publish_ready_products
python manage.py publish_ready_products --apply
python manage.py audit_storefront
```

O importador e o publicador são etapas independentes. Importar uma foto não
comprova estoque ou identidade e não altera os preços. Não é necessária uma nova
aprovação dos preços já autorizados.

## Validação

- `python manage.py check`: sem problemas.
- `python manage.py test`, com `VRAS_BROWSER_QA=1` e Chrome isolado: **123 testes
  passaram**, incluindo o teste de navegador existente.
- Dez novos testes integram importação local, publicação e vitrine/carrinho em
  diretórios temporários: permissões não fornecem identidade/estoque; variante
  incorreta, preço sem aprovação e oferta indisponível bloqueiam; simulação,
  idempotência, preservação de todos os campos exceto status, IDs duplicados,
  edições concorrentes, exibição na home e centavos/subtotais do carrinho.
- O navegador com dados isolados validou miniaturas, setas, toque, zoom, teclado,
  seleção de variantes, navegação e carrinho. As imagens de teste são blocos de
  cor fictícios, nunca fotos apresentadas como reais ou gravadas no catálogo.
- Navegador no servidor real: 15 capturas em **360, 390, 768, 1024 e 1440 px**;
  home, catálogo e carrinho, menu, pesquisa/filtros, 12 redirecionamentos legados
  e proteção dos 12 rascunhos. Sem erros inesperados de JavaScript/rede.
- `python manage.py audit_storefront`: 12 produtos, 12 IDs únicos, 12 rascunhos,
  580 mídias arquivadas, zero arquivos aprovados/posts. Sem erro crítico.
- Sintaxe dos scripts `static/js/storefront.js` e `scripts/browser_qa.mjs`
  verificada; `git diff --check` sem erros.
- Dados JSON de produtos, fontes, verificação de preços e manifesto público
  conferidos contra `1edf8bf`: conteúdo preservado.

Evidências locais, ignoradas pelo Git: `artifacts/publication-report.json`,
`artifacts/migration-browser-report.json`, `artifacts/gallery-browser-report.json`
e capturas de tela. Não há como validar visualmente fotos/vídeos reais ainda não
fornecidos. Não foram testados aparelhos físicos nem feito push/deploy.

Implementações: `7b2ab1e` (publicação sem alterar preços) e `fc5513c` (home com
primeiros modelos públicos). Visualização: http://127.0.0.1:8001/.
