# Vras Watches Django

Aplicacao Django para a loja Vras Watches. O projeto preserva os assets do site original, usa templates Django, CSS separado e substitui interacoes em JavaScript por rotas Python.

## Como instalar

```bash
pip install -r requirements.txt
```

## Como rodar

```bash
python manage.py migrate
python manage.py runserver
```

Depois acesse `http://127.0.0.1:8000`.

## Estrutura

- `config`: configuracao principal do projeto Django.
- `loja/views.py`: views e logica de navegacao.
- `loja/urls.py`: rotas da loja.
- `loja/services.py`: carregamento de produtos e regras do carrinho.
- `loja/templates/loja`: templates das paginas.
- `static`: CSS, fontes e imagens.
- `data/products.json`: catalogo simples dos relogios.

## Funcionalidades

- Pagina inicial com produtos em destaque.
- Listagem de produtos em `/produtos/`.
- Filtro por categoria e busca por query string.
- Detalhe do produto em `/produto/<id>/`.
- Carrinho em sessao Django.
- Adicionar e remover itens por rotas POST.
- Layout responsivo em azul e branco, sem JavaScript para as acoes principais.

## Comandos principais

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
