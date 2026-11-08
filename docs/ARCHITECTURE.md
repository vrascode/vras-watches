# Arquitetura do VRAS Watches

Este documento registra a organizacao do projeto.

## Aplicacao
- Backend em Django.
- Templates para renderizacao das paginas.
- Arquivos estaticos para CSS, JavaScript e imagens.
- Catalogo armazenado em data/products.json.

## Componentes
- loja/services.py: regras do catalogo.
- loja/views.py: visualizacoes e rotas.
- loja/pricing.py: aprovacao de precos.
- loja/media_import.py: importacao de midias.

## Evolucao
Manter as regras de negocio separadas da apresentacao.
