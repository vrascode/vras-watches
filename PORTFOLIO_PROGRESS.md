# VRAS Watches — progresso / progress

## 08/11/2026 — Refatoração MTV / MTV refactor

Implementado no checkout `C:\Projetos\vras-watches`, originalmente limpo em
`main` / `c7b2ff6`. Catálogo, preços, publicação, carrinho, mídia, vitrine e portal
foram separados por domínio dentro do app `loja`. Templates compartilhados e
testes foram reorganizados. Banco, dados, preços e fotografias foram preservados.

Delivered: domain packages, shared publication service, organized templates,
regression coverage and updated operating documentation. The Django app label,
public URLs and session contract are unchanged.

Validação / validation:

- `python manage.py check`: OK.
- Antes / before: `python manage.py test`: 135 tests, OK, skipped=2;
  both optional browser tests also passed when explicitly enabled.
- Depois / after: `python manage.py test`: 137 tests, OK, skipped=2;
  both optional browser tests also passed when explicitly enabled.
- Final combined run with `VRAS_BROWSER_QA=1`: all 137 tests passed, no skips, 35.641s.
- `python manage.py audit_storefront`: 12 products / 12 drafts; same baseline.
- `node scripts/browser_qa.mjs`: passed before and after; no browser/network errors.
- Four `node --check` calls passed for storefront/manager and QA scripts.
- Production manifest `collectstatic`: passed in a separate artifact directory.
- `makemigrations loja --check --dry-run`: no changes detected.
- 619 protected files unchanged; 35 routes unchanged; 35 identical screenshots.
- `git diff --check`: passed.

Pendência / remaining: Git metadata is read-only. `git add` failed with permission
denied on `.git/index.lock`; no commits, push or deploy were performed. Remote
HTTPS access was also blocked. Next action: review the working tree, create the
two coherent commits documented in `docs/REFACTOR_REPORT.md`, fetch/check the
actual remote state and push only when intended. Existing commercial draft
requirements remain pending owner confirmation.

Detalhes, comandos e mapa completo / details, commands and file map:
[docs/REFACTOR_REPORT.md](docs/REFACTOR_REPORT.md).


## 08/11/2026 — Organização do workspace / Workspace organization

A refatoração anterior está registrada nos commits locais `08efb62` e `a7aba34`;
o usuário informou sua publicação no GitHub. Esta tarefa começou com árvore
limpa em `main`, na mesma referência local de `origin/main`. Não foi possível
consultar o estado atual do servidor remoto por restrição de rede.

Entregue / delivered:

- 98 movimentos em artifacts, com 5.758 arquivos preservados por hash.
- Capturas/relatórios agrupados por suite e execução; evidências visuais,
  pesquisa, relatórios gerais, scripts históricos e runtime separados.
- Novos testes não sobrescrevem execuções anteriores; política comum em
  `scripts/qa_artifacts.mjs`.
- `.vscode/settings.json` oculta somente caches e saídas regeneráveis.
- `.gitignore` permite o guia de artifacts e settings compartilhados e
  mantém saídas de QA, dados privados, runtime e caches fora do Git.
- README, guia de artifacts e referências operacionais atualizados.
- Nenhum arquivo excluído; fonte Django, URLs e dados comerciais preservados.

Validação / validation:

- `python manage.py check`: OK antes e depois.
- `python manage.py test` antes: 137 testes, OK, skipped=2, 19.875s.
- `VRAS_BROWSER_QA=1 python manage.py test` depois: 137 testes, OK, sem skips,
  35.503s, incluindo login, upload, publicação, galeria e carrinho.
- `python manage.py audit_storefront`: mesmo resultado antes/depois,
  12 produtos / 12 rascunhos.
- `node scripts/browser_qa.mjs`: passou com 15 screenshots e sem erros inesperados.
- `node --check` nos três scripts de QA: passou.
- 5.758 hashes de arquivos movidos e 619 hashes protegidos: iguais.
- 24 caminhos concretos de artifacts e 15 links locais: válidos.
- Nenhum diff no código/dados de config, loja, templates, static ou data.
- `git diff --check`: passou.

Pendência / remaining: `git add` novamente bloqueado por `.git/index.lock`
somente para leitura. Nenhum novo commit, push ou deploy nesta execução.
Comandos para registrar e publicar os dois commits separadamente estão em
[docs/PROJECT_ORGANIZATION.md](docs/PROJECT_ORGANIZATION.md).

English: workspace artifacts were organized without deleting files or changing
commercial data. Shared editor settings hide only temporary/runtime output.
All 137 tests passed with browser QA enabled. Next action: review the changes,
create the documented commits in a normal PowerShell, check the current remote
state and publish each commit separately. Publication is not confirmed here.
