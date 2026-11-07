# Fotografias Poedagar autorizadas

Nenhuma fotografia foi incorporada em 07/11/2026: não foi apresentada autorização nem
associação segura entre o estoque VRAS e os modelos das fontes.

Receber os originais e a autorização escrita antes de incluir arquivos. A lista de
solicitação por modelo/variante fica em `docs/POEDAGAR_MEDIA_PENDING.csv`.

Organização sugerida: `<modelo>/<sku-vras>-frente.webp`, `-lateral.webp`, `-verso.webp`.
Os nomes com IDs das fontes no CSV são provisórios, não SKUs nem estoque da VRAS.

Exportar WebP/AVIF em boa resolução (por exemplo, até 1600 px no maior lado, sem
ampliar originais menores), preservar proporções, cor e detalhes do produto.
Não retirar marcas d'água ou logotipos; não gerar fotos artificiais de relógios.

Cadastrar cada foto em `data/media.json`, em `products.<id-vras>.images`, com `src`,
`alt`, `origem` e `autorizado: true` somente após conferir a licença e a identidade
exata do produto. Registrar o comprovante e a referência do fabricante na origem.
Adicionar ângulos diferentes apenas quando realmente existirem; resoluções da
mesma fotografia não são novos ângulos. A galeria usa a ordem do manifesto.
