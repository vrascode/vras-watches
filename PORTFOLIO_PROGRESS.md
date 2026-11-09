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
