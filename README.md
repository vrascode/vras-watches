# VRAS Watches

Projeto Django da loja VRAS Watches. A aplicacao usa templates Django, arquivos estaticos em `static/`, catalogo em JSON e carrinho baseado em sessao.

## Requisitos

- Python 3 instalado
- Pip instalado
- Terminal PowerShell, CMD ou outro terminal de sua preferencia

## Como iniciar o projeto

Entre na pasta do projeto Django:

```powershell
cd C:\Users\mathe\Downloads\saveweb2zip-com-usevoxo-com-br\vras-watches
```

Opcional, mas recomendado: crie e ative um ambiente virtual.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instale as dependencias:

```powershell
pip install -r requirements.txt
```

Execute as migracoes do banco:

```powershell
python manage.py migrate
```

Inicie o servidor local:

```powershell
python manage.py runserver 127.0.0.1:8001
```

## Como acessar o site

Com o servidor rodando, abra no navegador:

```text
http://127.0.0.1:8001/
```

Se preferir usar a porta padrao do Django, rode:

```powershell
python manage.py runserver
```

E acesse:

```text
http://127.0.0.1:8000/
```

## Paginas principais

- Home: `http://127.0.0.1:8001/`
- Produtos: `http://127.0.0.1:8001/produtos/`
- Carrinho: `http://127.0.0.1:8001/carrinho/`

## Estrutura do projeto

- `manage.py`: comando principal do Django.
- `config/`: configuracoes gerais do projeto.
- `loja/`: app principal da loja.
- `loja/templates/loja/`: templates HTML.
- `static/`: CSS, fontes, imagens e JavaScript.
- `data/products.json`: catalogo de produtos.
- `db.sqlite3`: banco local SQLite.

## Comandos uteis

Verificar se o projeto esta configurado corretamente:

```powershell
python manage.py check
```

Rodar migracoes:

```powershell
python manage.py migrate
```

Iniciar o servidor:

```powershell
python manage.py runserver 127.0.0.1:8001
```

Parar o servidor:

```text
Pressione Ctrl+C no terminal onde o servidor esta rodando.
```

## Observacoes

- Edite HTML em `loja/templates/loja/`.
- Edite CSS, imagens e JavaScript em `static/`.
- O arquivo `index.html` e as pastas `css/`, `js/` e `images/` no nivel acima de `vras-watches` nao sao usados pelo servidor Django.
