# Originais autorizados da VRAS

O catálogo atual é a geração `poedagar-v1`, com IDs 13–24. Os IDs 1–12 foram
aposentados e não podem receber as fotos dos novos modelos. A lista específica
está em `docs/POEDAGAR_NEW_MEDIA_PENDING.csv`, com 57 variantes anunciadas na fonte;
ela não afirma que a VRAS vende todas essas variantes.

Para `destino: product`, preencha também `variante_fonte_id` com o ID da variante
da fonte que corresponde exatamente à fotografia. Essa associação precisa de
conferência humana do produto real, não de semelhança visual. O importador grava
produto, modelo, geração e variante nas fotos, vídeos e posters. A publicação
exige que toda a galeria corresponda à variante escolhida no catálogo.

O `manifest.json` local contém apenas entradas pendentes e não autorizadas. Não
existem fotos ou vídeos fornecidos nesta pasta. Os nomes sugeridos não são arquivos
existentes. Informar permissão, origem, comprovante e a associação real antes de
alterar os sinalizadores; a publicação e aprovação do preço são etapas separadas.

Coloque aqui fotos e vídeos reais da loja. Os originais, `manifest.json` e eventuais
comprovantes ficam locais, ignorados pelo Git. Não há importação por nome de arquivo
ou associação automática de um relógio a um modelo.

Copie `manifest.example.json` para `manifest.json` e preencha `assets`. Cada entrada
aprovada exige ID único, arquivo local, texto alternativo, origem, comprovante de
autorização comercial e `autorizado: true`. Marque apenas depois da conferência.
O sinalizador não concede direitos nem certifica o arquivo por conta própria.

Destinos disponíveis:

| `destino` | Informações adicionais | Resultado |
| --- | --- | --- |
| `product` | `produto_id` existente, `produto_confirmado: true` após conferir o relógio/variante | Galeria do SKU, em `static/img/products/poedagar/<id>/` |
| `hero` | Foto horizontal ou vídeo | Banner principal |
| `hero_mobile` | Fotografia com enquadramento mobile aprovado | Versão mobile do banner fotográfico |
| `editorial` | Foto ou vídeo | Seção sobre a marca |
| `campaign` | Foto ou vídeo | Banner de campanha |
| `instagram` | `permalink` real de `/p/`, `/reel/` ou `/tv/` | VRAS WATCHES — NOSSO ESTILO |

Para `tipo: "video"`, informe também `poster` com fotografia local autorizada,
`video_otimizado: true` depois de conferir MP4 H.264 ou WebM apropriado para web, e
`legendas` com caminho de um `.vtt` quando houver fala. A autorização da entrada
precisa abranger o vídeo, poster e legendas. Os arquivos de vídeo são copiados;
esse comando não transcodifica nem certifica codecs. Não há FFmpeg instalado nesta
estação. Nenhum vídeo é publicado sem poster aprovado.

```powershell
python manage.py import_store_media
python manage.py import_store_media --apply
python manage.py publish_ready_products
python manage.py publish_ready_products --apply
python manage.py audit_storefront
```

A primeira execução simula e valida todo o lote. `--apply` integra somente entradas
aprovadas. Imagens viram WebP com tamanhos responsivos, sem recorte ou ampliação de
resolução. A orientação EXIF é aplicada e o perfil de cor é convertido para sRGB;
os originais permanecem intactos. Câmera/posição GPS não são copiadas ao derivado.
Imagens animadas e CMYK sem perfil precisam de revisão e não são convertidas de
forma ambígua. Marcas d'água e inscrições do relógio permanecem na imagem.

O mesmo ID atualiza apenas a sua entrada; os demais registros são preservados.
Arquivos de saída usam hash e novas versões não apagam as anteriores. Guarde os
comprovantes fora do diretório público; o campo `comprovante` deve conter uma
referência legível, sem dados pessoais ou credenciais. Nenhum preço, estoque ou
identidade de fabricante é alterado pelo importador.

O publicador usa as validações existentes e altera somente o status de ofertas
completas. Não seleciona variantes, confirma estoque ou reaplica preços.
Os arquivos e informações ainda necessários por modelo estão em
`docs/POEDAGAR_PUBLICATION.md`.
