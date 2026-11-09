# Organização do workspace VRAS Watches

## Escopo e estado inicial

Organização aplicada em `C:\Projetos\vras-watches`, mantendo a arquitetura MTV.
A inspeção encontrou `main` limpa em `a7aba34`, precedida por `08efb62`, da
refatoração. `origin` aponta para `https://github.com/vrascode/vras-watches.git`.
HEAD e a referência local `origin/main` não tinham divergência. O servidor
remoto atual não pôde ser consultado por restrição de rede; `fetch` também
encontrou `.git` somente para leitura.

A revisão de `config`, `loja`, `templates`, `static`, `data`, `scripts` e `docs`
confirmou responsabilidades coerentes. Não foram movidos módulos da aplicação,
rotas, fotos, templates ou arquivos comerciais. O acúmulo estava em saídas de
QA, perfis de Chrome e arquivos pontuais de `artifacts`.

## Movimentos locais

| Origem em artifacts | Destino | Finalidade |
| --- | --- | --- |
| `home-*.png`, `catalog-*.png`, `detail-*.png`, `cart-*.png` | `browser/storefront/runs/pre-organization/screenshots/` | Capturas da vitrine anterior |
| `migration-*.png` | `browser/migration/runs/pre-organization/screenshots/` | Catálogo em rascunho |
| `owner-*.png` | `browser/owner/runs/pre-organization/screenshots/` | Gestão e publicação |
| Quatro `*-browser-report.json` / `browser-report.json` | `browser/<suite>/runs/pre-organization/reports/` | Relatórios de cada fluxo |
| Folhas de contato e índice JSON | `visual/contact-sheets/` | Inspeção das imagens legadas |
| `refactor/before-screenshots/` | `visual/refactor/before/screenshots/` | Baseline visual |
| `refactor/visual-comparison.json` | `visual/refactor/reports/` | Comparação de pixels |
| JSONs/TXTs de inventário e validação da refatoração | `reports/refactor/` | Evidências anteriores |
| `publication-*.json` | `reports/publication/` | Auditoria e simulação de publicação |
| `refactor/publication-dry-run.json` | `reports/publication/refactor-dry-run.json` | Simulação anterior |
| `poedagar*-source.html` | `research/poedagar/sources/` | Páginas de pesquisa |
| `refactor/*.py` | `archives/refactor/scripts/` | Scripts históricos, não ferramentas atuais |
| `chrome-*`, `refactor/chrome*` | `runtime/chrome/` | Perfis e caches intactos |
| `refactor/static-build/` | `runtime/static-build/refactor/` | Build anterior de collectstatic |

Foram realizados **98 movimentos, contendo 5.758 arquivos**, com SHA-256 igual
antes e depois. **Nenhum arquivo foi excluído ou deduplicado.** Mesmo cópias
repetidas de baselines foram mantidas como evidências independentes. Perfis e
builds foram classificados como regeneráveis, mas não apagados. Os caminhos
absolutos de origem e destino foram conferidos antes de mover diretórios.

O manifesto local `artifacts/reports/organization/move-manifest.json` registra
origem, destino, finalidade, tamanho e hash de cada arquivo. Ele é ignorado
pelo Git porque pode conter metadados de arquivos locais. As referências da
documentação aos arquivos movidos foram atualizadas. Arquivos históricos
arquivados permanecem intactos, inclusive comandos e caminhos daquela época;
não são scripts ativos. O script pontual de atualização desta documentação
fica em `artifacts/archives/organization/scripts/` para consulta.

## Saída de testes daqui em diante

`scripts/qa_artifacts.mjs` é o utilitário compartilhado pelos dois scripts de
QA. Resolve a raiz pelo local do módulo, sem depender do diretório atual do
terminal. Cada suite grava em:

```text
artifacts/browser/<suite>/runs/<timestamp-UTC>-<sufixo-único>/
  reports/
  screenshots/
```

Os subdiretórios são criados conforme usados. `mkdtemp` evita colisões entre
execuções; a data usa caracteres válidos no Windows. O caminho aparece no
terminal; a saída JSON existente continua em stdout. Não há limpeza automática
nem sobrescrita de execuções anteriores. As suites são `storefront`, `migration`,
`gallery` e `owner`. Os mesmos fluxos de QA continuam sendo executados.

Os artefatos movidos são locais e não são distribuídos pelo GitHub. Um clone
recebe somente `artifacts/README.md`; os testes criam seus diretórios de saída.
Nenhum PNG, relatório gerado ou perfil foi adicionado ao Git.

## VS Code e Git

`.vscode/settings.json` compartilha configurações específicas do projeto:

- Oculta `__pycache__`, bytecode Python, caches de pytest/mypy/ruff e cobertura.
- Oculta `artifacts/runtime/` e `staticfiles/`, ambos saídas regeneráveis.
- Evita busca e monitoramento volumoso em caches e runtime.
- Mantém código, templates, fotos comerciais, banco, dados, documentos e
  evidências organizadas visíveis. Não fixa interpretador ou formatador local.

O `.gitignore` mantém proteção de segredos, SQLite, originais privados,
dependências e builds. Acrescenta caches Python e cobertura. As exceções
permitem versionar somente `.vscode/settings.json` e `artifacts/README.md`
nessas pastas. Nenhum arquivo já versionado foi removido do índice.

## Preservação

Evidências que sustentam validação, comparação visual ou decisões comerciais
merecem retenção. Perfis isolados e builds podem ser recriados, mas sua remoção
exige identificar uso e referências. Não há descarte automático. Documentação
operacional ativa fica em `docs/`; ferramentas ativas permanecem em `scripts/`.
Banco, preços, produtos, imagens comerciais e registros privados foram
preservados nas localizações originais.

## Validação

| Verificação | Resultado |
| --- | --- |
| `python manage.py check` | Sem problemas antes e depois |
| `python manage.py test` antes | 137 testes, OK, dois de navegador pulados por padrão; 19,875 s |
| Suíte final com `VRAS_BROWSER_QA=1` | **137 testes passaram, sem skips; 35,503 s** |
| `python manage.py audit_storefront` | Igual antes/depois: 12 produtos, 12 IDs únicos, 580 mídias locais, 0 aprovadas, 0 posts e 12 rascunhos |
| QA da vitrine real | Passou: 15 capturas, 12 redirecionamentos e 12 rascunhos protegidos; sem erros inesperados |
| Saída de navegador organizada | Novas execuções de migration, gallery e owner com relatórios próprios; 15 e 20 capturas nos fluxos que geram imagens |
| Sintaxe Node | Os três scripts `.mjs` alterados/criados passaram em `node --check` |
| Integridade dos movimentos | 5.758 arquivos conferidos novamente; todos com o hash original |
| Integridade comercial e SQLite | 619 arquivos protegidos idênticos; nenhuma alteração no banco, catálogo ou arquivos comerciais |
| Referências | 24 caminhos concretos de artifacts e 15 links locais conferidos |
| Código da aplicação | Nenhum diff em config, loja, templates, static ou data |
| Regras de ignore | Guia de artifacts e settings compartilhados permitidos; runtime, evidências e caches ignorados |
| `git diff --check` | Sem erros |

Os novos resultados e o mapa de execução estão em
`artifacts/reports/organization/validation.json`. Os testes de upload/publicação
usam usuários, banco e arquivos fictícios isolados. A instalação do Chrome
exigiu `--no-sandbox` apenas no processo de QA deste ambiente restrito; essa
opção não foi adicionada aos scripts da aplicação. Não foram alterados estados
comerciais para executar os testes.

## Commits e publicação

**Nenhum commit novo foi criado nesta execução.** A tentativa real de `git add`
falhou ao criar `.git/index.lock`, com acesso negado. O ambiente não permite
elevação. As alterações estão salvas para revisão. Não houve push; a consulta
HTTPS ao GitHub também foi bloqueada. Os commits anteriores da refatoração
aparecem no log local; não foram recriados.

Execute os comandos em um PowerShell normal na raiz do projeto para registrar
duas etapas coesas. Os movimentos de artifacts são locais e já estavam ignorados.

```powershell
Set-Location C:\Projetos\vras-watches
git status --short --branch
git add -- scripts/browser_qa.mjs scripts/owner_browser_qa.mjs scripts/qa_artifacts.mjs
git commit -m "chore: organize browser QA outputs by suite and run"
git add -- .gitignore .vscode/settings.json artifacts/README.md README.md docs PORTFOLIO_PROGRESS.md
git commit -m "chore: organize workspace navigation and document artifact retention"
git fetch origin
git status --short --branch
```

Confira a sincronização e eventuais mudanças remotas. Para publicar os dois
commits separadamente, use o hash confirmado do primeiro e depois `main`:

```powershell
git log -2 --oneline
git push origin HASH_DO_PRIMEIRO_COMMIT:main
git push origin main
```

Substitua `HASH_DO_PRIMEIRO_COMMIT` pelo hash mostrado no log. Não use force push.
Se o remoto avançou, integre as mudanças e repita a validação antes do envio.
Considere a publicação confirmada apenas após resposta do remoto.

## English

The existing Django architecture is unchanged. All 5,758 moved artifacts were
preserved byte for byte. Browser evidence is grouped by suite and unique run,
while visual baselines, research, reports and runtime have separate folders.
Shared VS Code settings hide only caches and regenerable outputs. Source and
documentation remain visible. Only the artifact guide and project editor settings
are tracked inside these otherwise ignored directories. No cleanup or deletion
was introduced. Commercial data and SQLite are unchanged. Local commits and
remote publication remain blocked by the environment; commands are provided.
