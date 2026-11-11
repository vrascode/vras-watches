# Continuação do catálogo premium / Catalog continuation

Data: 2026-11-10. Diretório: C:/Projetos/vras-watches.
Repositório: https://github.com/vrascode/vras-watches, branch main.

## Resultado verificado

| Item | Quantidade |
| --- | ---: |
| Imagens reais baixadas e verificadas | 0 |
| Vídeos reais baixados e verificados | 0 |
| Mídias novas integradas às galerias | 0 |
| Produtos novos publicados para compra | 0 |
| Testes aprovados | 247 |
| Testes opcionais ignorados | 2 |
| Total de testes encontrados | 249 |
| Commits novos criados | 0 |
| Commits enviados | 0 |

Nenhum hash novo foi enviado. A comparação pela conexão GitHub confirmou
main idêntica a
[5a047639a7d2e79781fd27683bc254df867a0734](https://github.com/vrascode/vras-watches/commit/5a047639a7d2e79781fd27683bc254df867a0734).
As páginas de apresentação existentes não significam que ofertas para compra
tenham sido publicadas.

## Causa dos downloads

O DNS resolveu poedagareco.com, cdn.shopify.com e github.com. A tentativa de
conectar à porta TCP 443 falhou nos três com PermissionError / WinError 10013.
A requisição HTTPS da primeira imagem também falhou antes de receber resposta
HTTP. Não foi observado código 401, 403, 404 ou 429 do servidor de origem.
Nenhum proxy HTTP(S) estava configurado no processo.

A nova tentativa das 12 imagens pelo comando de mídia registrou exatamente
12 erros environment_network_denied. Não há comprovação de bloqueio feito pelo
site, nem justificativa para burlar autenticação. A restrição observada pertence
ao ambiente de execução.

## Variantes, integração e publicação

O inventário tem 12 imagens observadas. A seleção de cor da página identifica
uma URL para Prata, uma para Preto e uma para Azul. Outras nove permanecem sem
variante confirmada. Como nenhum arquivo foi baixado, não foi possível inspecionar
as fotografias nem validar visualmente todas as cores.

Não foram descobertas URLs verificadas de vídeos nesta execução. Isso não
significa que a fonte não tenha vídeos.

A associação com a galeria agora exige processamento completo e um arquivo
local efetivamente disponível. Arquivos ausentes ou resultados de processamento
com erro são rejeitados, mesmo que reste uma entrada antiga de asset.
O fluxo completo com imagem, variante, publicação e carrinho continua testado
somente com fixtures isoladas.

A tentativa de publicação passou pelos critérios existentes e encontrou
60 ofertas incompletas. Nenhuma disponibilidade, referência física ou variante
foi confirmada artificialmente. Os preços e aprovações existentes não foram
reimportados nem renovados pela rotina de mídia.

## Preservação

- Todos os arquivos alterados/novos foram inventariados antes do trabalho.
- Os 12 produtos anteriores continuam iguais aos dados de HEAD.
- Todos os 60 preços e suas aprovações permanecem iguais ao início desta tarefa.
- O SHA256 do banco permaneceu
  0f0395694d479fe41b86d0915d02b11575df2e785feecc920b9df2a7c13eb37b.
- Nenhum reset, checkout, remoção de produtos ou alteração de schema foi feito.

## Melhorias e comandos

Foi acrescentada uma rotina de tentativa apenas de mídias:

```powershell
python manage.py retry_reference_media --model Montelux
python manage.py retry_reference_media --model Montelux --apply --publish-ready --report artifacts/catalog-continuation/media-retry.json
```

Sem --apply há apenas simulação. O comando não reimporta produtos, não reaplica
preços e não grava no banco SQLite. As falhas distinguem restrição local,
autenticação exigida, acesso negado, arquivo ausente, limite de requisições,
timeout e erro de processamento.

Validações realizadas:

- python manage.py check: sem problemas.
- python manage.py test: 249 encontrados, 247 aprovados e dois ignorados,
  22.702 segundos.
- python manage.py test loja.tests.reference: 50 testes aprovados.
- git status --short: alterações preservadas em main.
- git diff --check: passou.
- Plano de 20 commits separado por funcionalidade: validado em simulação.

## Git e GitHub

A execução do plano real de commits foi tentada. git add falhou com
Permission denied ao criar .git/index.lock. git ls-remote também falhou na
conexão HTTPS pelo terminal.

A integração GitHub conseguiu ler o repositório, informou permissão de escrita
para a conta conectada e confirmou que a base remota era idêntica à local.
Contudo, a primeira operação de escrita, create_tree, foi rejeitada:
“MCP tool call requires approval, but approval policy is never”.
Nenhum create_commit ou update_ref foi executado. Não se tentou outra operação
de escrita para contornar a exigência de aprovação.

## Pendências

Downloads, descoberta de vídeos, conferência visual por cor e publicação de
ofertas exigem arquivos reais e confirmação das ofertas. Escrita Git/GitHub
exige um ambiente que permita essa operação. O trabalho implementado foi
preservado e o plano de commits foi atualizado com as correções desta execução.

English: all existing products, approved prices and database bytes were
preserved. Seven additional tests passed. All twelve real media retries failed
at the local transport layer, before HTTP. No media or offers were falsely
reported as published. Local Git writes were denied; connected GitHub reads
worked, but its first write required an approval unavailable under the current
policy. No new commits were created or sent.
