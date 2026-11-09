# Artefatos locais de desenvolvimento / Local development artifacts

Esta pasta guarda saídas de testes, evidências e arquivos regeneráveis.
**Somente este guia é versionado.** Imagens, relatórios, perfis e scripts
históricos continuam locais; não são arquivos comerciais da loja.

```text
artifacts/
  browser/<suite>/runs/<execução>/
    screenshots/                 capturas da interface
    reports/                     resultados JSON do mesmo fluxo
  visual/
    contact-sheets/              folhas de contato e índice de imagens legadas
    refactor/before/screenshots/ baseline visual da refatoração
    refactor/reports/            comparação de pixels
  reports/
    publication/                simulações e auditorias de publicação
    refactor/                   inventários, hashes e validação da refatoração
    organization/               manifesto dos movimentos e validação desta organização
  research/poedagar/sources/     HTMLs de pesquisa preservados
  archives/                     scripts pontuais históricos por tarefa
  runtime/
    chrome/                     perfis isolados de QA e caches
    static-build/               saídas locais de collectstatic
```

Suites de navegador: `storefront`, `migration`, `gallery` e `owner`.
`pre-organization` preserva as evidências que antes estavam soltas na raiz.
Novas execuções usam data/hora UTC e um sufixo aleatório válido no Windows;
`reports/` e `screenshots/` são criados conforme usados. Isso evita sobrescrever
as evidências anteriores. `scripts/qa_artifacts.mjs` define essa política comum
para os dois scripts de navegador, com caminhos relativos ao projeto.
O caminho da execução aparece no terminal como `QA artifacts: ...`.

## Preservação e manutenção

- Capturas, relatórios, baselines, folhas de contato e HTMLs são evidências.
  Preserve as execuções que sustentam uma entrega ou comparação.
- Perfis de Chrome e builds em `runtime/` são regeneráveis. Os existentes foram
  movidos intactos. Crie um perfil novo para o QA ativo, em vez de reutilizar
  automaticamente um perfil histórico.
- Scripts em `archives/` registram operações pontuais já realizadas. Não devem
  ser reexecutados como ferramentas atuais: podem conter comandos/caminhos
  históricos e operações que já foram concluídas.
- Não há limpeza automática. Antes de remover uma execução, identifique a
  finalidade, confira referências e avalie a retenção das evidências.
- O VS Code oculta somente `runtime/` desta pasta. As evidências organizadas
  e este guia continuam visíveis; busca e monitoramento evitam o runtime volumoso.
- Banco, preços, imagens comerciais e comprovantes privados permanecem em
  suas pastas originais, fora desta organização de artefatos.

O mapa dos 98 movimentos está em `reports/organization/move-manifest.json`, com
origem, destino, finalidade, tamanho e SHA-256 dos 5.758 arquivos movidos.
Os hashes foram conferidos antes e depois da movimentação.
Leia [o registro de organização](../docs/PROJECT_ORGANIZATION.md).

## English

Only this navigation guide is tracked. Browser runs are isolated by suite and
unique UTC timestamps. Existing evidence is retained under pre-organization.
Visual baselines, research and validation have separate folders. Chrome profiles
and builds are regenerable runtime data, hidden in VS Code but preserved on disk.
No files were deleted and no automatic cleanup was introduced. Historical
one-off scripts are archived records, not active migration tools.
