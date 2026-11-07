"""Render migration proposals from the source snapshot; never write store prices."""
import csv
from decimal import Decimal
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PREVIOUS = {"Army": "196.92", "Deluxe": "199.90", "Deluxe Golden": "194.90", "Golden Mars": "197.90",
            "Golden Moon": "197.20", "Golden Neptune": "197.40", "Golden Star": "179.90", "King Royal": "219.90",
            "Machine": "194.90", "Nautilus": "189.90", "Signature": "177.90", "Tempus": "187.90"}


def brl(value):
    return f"R$ {Decimal(str(value)):,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def main():
    catalog = json.loads((ROOT / "data/products.json").read_text(encoding="utf-8"))
    snapshot = json.loads((ROOT / "data/poedagar_sources.json").read_text(encoding="utf-8"))
    sources = {p["url"]: p for p in snapshot["products"] if "error" not in p}
    rows, variants, unavailable, media_requests = [], [], [], []
    for product in catalog:
        source = sources.get(product["fontes"]["url_modelo_e_preco"])
        if not source:
            raise ValueError(f"Modelo sem consulta válida: {product['nome']}; não inferir preço")
        prices = sorted({Decimal(str(v["price_brl"])) for v in source["variants"]})
        proposal = " a ".join(brl(price) for price in prices) if len(prices) > 1 else brl(prices[0])
        previous = Decimal(PREVIOUS[product["modelo"]])
        delta = brl(prices[0] - previous) if len(prices) == 1 else "Ver variantes"
        rows.append(f"| {product['id']} | {product['nome']} | {brl(previous)} | {proposal} | {delta} | [Página individual]({source['url']}) | {source['checked_at_utc'][:19]} | Rascunho |")
        for variant in source["variants"]:
            variants.append([product["id"], product["nome"], variant["title"], variant["source_sku_id"],
                             variant["source_sku"], variant["price_brl"], variant["source_stock_status"],
                             variant["source_blocked_sale"], source["url"], source["checked_at_utc"], "Não aprovado"])
            prefix = f"{product['slug']}/{variant['source_sku_id']}"
            media_requests.append([product["id"], product["nome"], variant["source_sku_id"], variant["title"], source["url"],
                                  prefix + "-frente.jpg", prefix + "-lateral.jpg; " + prefix + "-verso.jpg",
                                  "static/img/products/poedagar/" + product["slug"] + "/",
                                  "Confirmar variante VRAS, referência e pulseira; receber original real e autorização comercial. Nomes/ângulos sugeridos, não arquivos existentes."])
            if variant["source_stock_status"] != "in_stock" or variant["source_blocked_sale"]:
                unavailable.append(variant["title"] + " — " + variant["source_stock_status"])
    with (ROOT / "docs/POEDAGAR_NEW_PRICE_VARIANTS.csv").open("w", encoding="utf-8-sig", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(["id_VRAS", "modelo", "variante_fonte", "id_variante_fonte", "sku_fonte_nao_referencia_fabricante",
                         "preco_proposto_BRL", "disponibilidade_na_fonte", "venda_bloqueada_na_fonte", "url", "consulta_UTC", "aprovacao"])
        writer.writerows(variants)
    with (ROOT / "docs/POEDAGAR_NEW_MEDIA_PENDING.csv").open("w", encoding="utf-8-sig", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(["produto_id_VRAS", "modelo", "id_variante_fonte_nao_SKU_VRAS", "variante_anunciada",
                         "origem_para_consulta_sem_licenca", "arquivo_principal_a_solicitar", "angulos_opcionais", "destino_final", "pendencia"])
        writer.writerows(media_requests)
    report = """# Novos preços propostos — catálogo Poedagar

Os 12 modelos comerciais desejados foram encontrados nas páginas individuais do site 2 nesta consulta.
Cada modelo possui ao menos uma variante anunciada disponível. A seleção original foi mantida; nenhuma substituição adicional foi necessária.
São anúncios comerciais da fonte, não confirmação de referências físicas de fabricante ou estoque VRAS.

**Nenhum preço foi aprovado ou publicado.** `preco` é `null` nos 12 novos registros.
Os valores abaixo são propostas com base no preço cadastrado por variante da fonte, sem Pix condicionado, descontos ou preços antigos.
A diferença compara apenas a pesquisa Poedagar anterior fornecida no briefing com a consulta atual do mesmo anúncio.
Não é uma diferença entre os antigos relógios VRAS e os novos Poedagar: são produtos distintos.

| ID VRAS novo | Modelo | Referência anterior | Proposta atual | Diferença da pesquisa anterior | Fonte | Consulta UTC | Estado |
| --- | --- | --- | --- | --- | --- | --- | --- |
""" + "\n".join(rows) + f"""

## Variantes, disponibilidade e aprovação

Foram consultadas {len(variants)} variantes dos modelos selecionados. O arquivo
[POEDAGAR_NEW_PRICE_VARIANTS.csv](POEDAGAR_NEW_PRICE_VARIANTS.csv) registra cada cor anunciada,
ID interno da fonte, SKU da fonte, preço proposto, disponibilidade, URL e horário.
O SKU repetido da fonte não foi tratado como referência do fabricante nem como SKU da VRAS.
Cor anunciada não confirma cor da caixa, mostrador ou pulseira separadamente.

Variantes indisponíveis na fonte: {'; '.join(unavailable) or 'nenhuma'}.
O preço dessa variante é evidência da consulta e deve ser reconfirmado após disponibilidade.
Nenhum estado de estoque externo foi copiado para a VRAS.

Antes da publicação: confirmar referência física do fabricante e a variante efetivamente vendida,
receber fotografias autorizadas correspondentes, confirmar a oferta VRAS e obter aprovação explícita
do proprietário para o preço exato por SKU. Registrar valor aprovado, data e referência da autorização.
O servidor exige que o valor da aprovação corresponda ao preço de venda, além dos demais requisitos.
Marcar apenas `status: publicado` não torna um produto comprável.

## Fotografias e origem

Zero fotos e vídeos foram incorporados. Veja [POEDAGAR_NEW_MEDIA_PENDING.csv](POEDAGAR_NEW_MEDIA_PENDING.csv)
para os arquivos a solicitar por variante e os destinos `static/img/products/poedagar/<modelo>/`.
Os nomes de arquivos e ângulos são solicitações, não fotografias existentes.
Nenhuma imagem antiga dos IDs 1–12 foi associada aos novos IDs 13–24.
As páginas do site 1 registradas como candidatas continuam sem equivalência física confirmada;
não se transferem fotos, variantes ou especificações de um anúncio para outro por nome semelhante.

Consulta completa: {snapshot['consulted_at_utc']}. Evidência: `data/poedagar_sources.json`.
Regerar este relatório: `python scripts/report_poedagar_migration.py`, após atualizar a pesquisa
com `python scripts/review_poedagar.py --refresh`. Nenhum dos comandos aprova preços.
"""
    (ROOT / "docs/POEDAGAR_NEW_PRICES.md").write_text(report, encoding="utf-8")
    print(f"{len(catalog)} draft models; {len(variants)} variant proposals; zero selling prices changed.")


if __name__ == "__main__":
    main()
