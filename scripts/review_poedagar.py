"""Capture public metadata on explicit --refresh; build an offline catalog review.

Never downloads photographs, writes storefront prices, or grants media permission.
Python standard library only. A denied request is recorded, never bypassed/retried.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "data/poedagar_sources.json"
SECOND = "https://lojaspoedagar.com.br"
FIRST = "https://poedagareco.com"
CANDIDATES = {
    "deluxe": "relogio-poedagar-deluxe-edition", "golden-star": "relogio-poedagar-goldenstar",
    "signature": "relogio-poedagar-signature", "king-royal": "poedagar-kingroyal",
    "army": "relogio-poedagar-army", "legitimus": "relogio-poedagar-legitimo",
    "relogio-poedagar-nautilus-azul": "relogio-poedagar-nautilus",
    "universy": "relogio-poedagar-universo", "machine": "relogio-poedagar-machine",
    "lattitude": "relogio-poedagar-latittude",
}


def fetch(url):
    request = Request(url, headers={"User-Agent": "VRAS-CatalogReview/1.0"})
    with urlopen(request, timeout=30) as response:
        raw = response.read()
    return raw.decode("utf-8"), hashlib.sha256(raw).hexdigest()


def capture_second(path):
    record = {"url": SECOND + path, "checked_at_utc": datetime.now(timezone.utc).isoformat()}
    try:
        html, record["html_sha256"] = fetch(record["url"])
        start = re.search(r"window\.data\s*=\s*", html)
        if not start:
            raise ValueError("Public product metadata not found; price not inferred")
        product = json.JSONDecoder().raw_decode(html[start.end():])[0]["product"]["data"]
        record.update(name=product["name"], slug=product["slug"], variants=[],
                      marketed_brand="Poedagar" if "poedagar" in product["name"].casefold() else None,
                      commercial_model=product["name"].removeprefix("Relógio Poedagar "),
                      manufacturer_reference=None,
                      method="public HTML window.data.product.data.skus.data[].prices.data.price",
                      vras_product_id=None, match_status="unconfirmed",
                      price_approval="not_submitted_no_exact_match")
        for sku in product["skus"]["data"]:
            prices = sku["prices"]["data"]
            record["variants"].append({
                "source_sku": sku["sku"], "source_sku_id": sku["id"], "title": sku["title"],
                "options": sku["variations"], "price_brl": prices["price"],
                "pix_brl": prices.get("pix", {}).get("price"),
                "source_blocked_sale": sku["blocked_sale"], "source_stock_status": sku["stock_status"],
                "case_color": None, "strap_color": None, "strap_type": None,
                "attribute_status": "not_verified; source color labels do not distinguish dial/case/strap",
                "image_urls_for_review_only": [entry["url"] for entry in sku["images"]["data"]],
            })
    except Exception as error:
        record["error"] = str(error)
    return record


def capture_first(pair):
    slug, handle = pair
    record = {"second_site_slug_candidate": slug, "url": FIRST + "/products/" + handle,
              "checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "image_reuse_authorized": False,
              "match_status": "name_candidate_only_requires_reference_and_variant_confirmation"}
    try:
        html, record["html_sha256"] = fetch(record["url"])
        identity = []
        for content in re.findall(r'<script[^>]*type=[\'"]application/ld\+json[\'"][^>]*>(.*?)</script>', html, re.S):
            try:
                value = json.loads(content)
                if isinstance(value, dict) and value.get("@type") == "Product":
                    identity.append({key: value[key] for key in ("name", "sku", "mpn", "brand", "image") if key in value})
            except json.JSONDecodeError:
                continue
        record["schema_identity"] = identity
        record["option_labels"] = list(dict.fromkeys(re.findall(r'<input[^>]*name="option1"[^>]*value="([^"]+)"', html)))
        record["variant_images_for_review_only"] = []
        for match in re.finditer(r'"products"\s*:\s*(\[)', html):
            try:
                entries = json.JSONDecoder().raw_decode(html[match.start(1):])[0]
            except json.JSONDecodeError:
                continue
            for entry in entries:
                if entry.get("handle") == handle:
                    for variant in entry.get("variants", []):
                        if not variant.get("title"):
                            continue
                        src = (variant.get("image") or {}).get("src")
                        record["variant_images_for_review_only"].append({
                            "label": variant["title"], "source_variant_id": variant["id"],
                            "source_sku": variant.get("sku"),
                            "image_url": "https:" + src if src and src.startswith("//") else src,
                        })
            if record["variant_images_for_review_only"]:
                break
    except Exception as error:
        record["error"] = str(error)
    return record


def refresh():
    category, _ = fetch(SECOND + "/masculinos?sort_by=best_sellers")
    paths = sorted(set(re.findall(r'href="([^"?]+/p)"', category)))
    if not paths:
        raise ValueError("No public product links found; existing snapshot preserved")
    with ThreadPoolExecutor(max_workers=4) as pool:
        products = list(pool.map(capture_second, paths))
        first = list(pool.map(capture_first, CANDIDATES.items()))
    report = {"consulted_at_utc": datetime.now(timezone.utc).isoformat(),
              "category_url": SECOND + "/masculinos?sort_by=best_sellers", "currency": "BRL",
              "scope": f"{len(products)} linked men's listings; {len(first)} first-site name candidates (not an exhaustive first-site inventory)",
              "prices_are_proposals_only": True, "photographs_downloaded": 0,
              "products": products, "first_site_candidates": first}
    SNAPSHOT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def brl(value):
    return f"R$ {Decimal(str(value)):,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def table(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
                     + ["| " + " | ".join(str(cell).replace("|", "/").replace("\n", " ") for cell in row) + " |" for row in rows])


def build_reports():
    report = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    catalog = json.loads((ROOT / "data/products.json").read_text(encoding="utf-8"))
    products = [entry for entry in report["products"] if "error" not in entry]
    first = {entry["second_site_slug_candidate"]: entry for entry in report["first_site_candidates"]}
    stamp = report["consulted_at_utc"]
    rows, variants, media_rows, identities = [], [], [], []
    for product in products:
        source = first.get(product["slug"])
        prices = sorted({Decimal(str(v["price_brl"])) for v in product["variants"]})
        colors = [" / ".join(option["value"] for option in v["options"]) or "Não discriminada" for v in product["variants"]]
        rows.append([f"[{product['name']}]({product['url']})", "; ".join(colors),
                     " a ".join(brl(price) for price in prices) if len(prices) > 1 else brl(prices[0]),
                     f"[Candidato por nome]({source['url']})" if source else "Sem candidato registrado", "Não confirmada"])
        for variant, color in zip(product["variants"], colors):
            variants.append([product["name"], color, variant["source_sku_id"], variant["source_sku"],
                             variant["price_brl"], variant.get("pix_brl"), product["url"], product["checked_at_utc"],
                             variant["source_stock_status"], variant["source_blocked_sale"],
                             "Sem associação local; não aplicar"])
            identities.append([product["name"], product.get("marketed_brand", "Poedagar"),
                               product.get("commercial_model", product["name"]), product.get("manufacturer_reference") or "",
                               variant["source_sku"], variant["source_sku_id"], color,
                               variant.get("case_color") or "Não confirmada", variant.get("strap_color") or "Não confirmada",
                               variant.get("strap_type") or "Não confirmado", len(variant["image_urls_for_review_only"]),
                               variant["price_brl"], variant["source_stock_status"], product["url"], product["checked_at_utc"]])
            target = f"static/img/products/poedagar/{product['slug']}/{variant['source_sku_id']}"
            media_rows.append([product["name"], color, variant["source_sku_id"],
                               source["url"] if source else "", product["url"],
                               "; ".join(variant["image_urls_for_review_only"]),
                               target + "-frente.webp", target + "-lateral.webp", target + "-verso.webp",
                               "Pendente: SKU VRAS + identidade/pulseira + originais + autorização"])
    docs = ROOT / "docs"
    comparison = [[p["id"], p["nome"], "Não confirmado", p["preco"], "", "", "", stamp,
                   "Sem correspondência exata; preservar preço publicado"] for p in catalog]
    for filename, headers, entries in [
        ("POEDAGAR_PRICES.csv", ["produto", "variante_fonte", "id_variante_fonte", "sku_fonte_nao_referencia_fabricante", "preco_BRL", "pix_condicionado_BRL", "url", "consulta_UTC", "estoque_na_fonte_nao_VRAS", "venda_bloqueada_na_fonte", "decisao"], variants),
        ("POEDAGAR_MEDIA_PENDING.csv", ["produto", "variante_fonte", "id_variante_fonte", "pagina_site1_candidata", "pagina_site2", "urls_somente_consulta", "destino_frente_sugerido", "destino_lateral_sugerido", "destino_verso_sugerido", "pendencia"], media_rows),
        ("POEDAGAR_COMPARISON.csv", ["id_VRAS", "produto_VRAS", "modelo_Poedagar", "preco_atual_BRL", "preco_referencia_BRL", "diferenca_BRL", "url_correspondente", "consulta_UTC", "pendencia"], comparison),
        ("POEDAGAR_VARIANT_IDENTITY.csv", ["nome_comercial", "marca_anunciada", "modelo_comercial", "referencia_fabricante", "sku_interno_fonte", "id_variante_fonte", "rotulo_cor_fonte", "cor_caixa", "cor_pulseira", "tipo_pulseira", "quantidade_fotos_fonte", "preco_BRL", "disponibilidade_fonte", "url", "consulta_UTC"], identities),
    ]:
        with (docs / filename).open("w", encoding="utf-8-sig", newline="") as output:
            writer = csv.writer(output)
            writer.writerow(headers)
            writer.writerows(entries)
    text = f"""# Pesquisa Poedagar e comparação de preços

Consulta pública: {stamp} (UTC). Os horários individuais também estão registrados no snapshot.
Fonte principal de preço: [{report['category_url']}]({report['category_url']}). Cada página individual foi consultada; horários e hashes SHA-256 estão em `data/poedagar_sources.json`.

## Resultado e limite da identificação

{len(products)} anúncios/modelos comerciais e {len(variants)} variantes identificados no site 2. Dez candidatos por nome foram consultados no site 1; isso não é um inventário completo desse site nem comprova equivalência. Nenhum dos 12 produtos VRAS foi associado com segurança. Zero fotografias autorizadas incorporadas. Nenhum preço publicado foi alterado.

Os nomes são nomes comerciais das lojas, não referências oficiais do fabricante. O SKU `201447598` aparece em anúncios diferentes do site 2; os IDs de variante identificam registros dessa loja e não referências do fabricante. Cor semelhante ou nome parecido não comprovam o mesmo modelo, acabamento ou pulseira. Valores de estoque da fonte são apenas evidência da consulta e nunca foram copiados como estoque VRAS.

O [inventário de identidade por variante](POEDAGAR_VARIANT_IDENTITY.csv) registra marca anunciada, nome comercial, SKU/ID interno, rótulo de cor, quantidade de fotografias, disponibilidade, URL e data. Referência do fabricante, cor da caixa, cor e tipo de pulseira ficam explicitamente não confirmados quando não há evidência inequívoca; o rótulo “Azul” não foi reinterpretado como cor da caixa ou da pulseira.

## Preços encontrados por anúncio

Preço de venda `prices.data.price`, em BRL, sem adotar preço antigo, percentual de desconto ou preço do site 1. As {len(variants)} variantes foram consultadas individualmente. Valores Pix condicionados ficam apenas no CSV de evidência e não são propostos como preço VRAS.

{table(['Modelo e URL individual', 'Variantes anunciadas no site 2', 'Preço de referência', 'Site 1: possível correspondência', 'Associação VRAS'], rows)}

### Disponibilidade na fonte

{'; '.join(p['name'] + ' — ' + v['title'] + ' (' + v['source_stock_status'] + ')' for p in products for v in p['variants'] if v['source_blocked_sale'] or v['source_stock_status'] != 'in_stock') or 'Nenhuma variante indicada como indisponível nessa consulta.'}

Um preço cadastrado para variante indisponível é apenas evidência histórica, não uma proposta aplicável à VRAS. Preservar o preço local e consultar novamente após identificação e disponibilidade confirmadas.

## Comparação com o catálogo VRAS

Não há diferença calculada nem preço proposto por SKU enquanto não existir correspondência exata. Esta tabela preserva os preços da VRAS e explicita a lacuna, sem comparar relógios diferentes.

{table(['Produto VRAS', 'Modelo Poedagar', 'Preço atual', 'Preço de referência', 'Diferença em reais', 'URL correspondente', 'Consulta UTC'], [[p['nome'], 'Não confirmado', brl(p['preco']), 'Não confirmado', 'Não calculável', 'Não confirmada', stamp[:10]] for p in catalog])}

O [CSV de comparação por produto VRAS](POEDAGAR_COMPARISON.csv) mantém os mesmos campos. Valores e URLs não correspondidos ficam vazios, em vez de presumir zero ou comparar modelos diferentes.

## Aprovação dos preços

Todos os 18 preços de referência estão separados do catálogo e pendentes de correspondência e aprovação. Não há substituição apta a ser aprovada por SKU ainda. Depois de o proprietário informar quais modelos vende, referências e combinações de cor/pulseira, apresentar nova tabela por ID com preço atual, preço proposto, diferença, URL e data. Somente uma aprovação explícita dessa tabela autoriza alterar `preco` em `data/products.json`.

## Fotografias e especificações pendentes

Os 18 modelos comerciais da tabela precisam de fotografias autorizadas e identificação dos SKUs efetivamente vendidos pela VRAS. A lista [POEDAGAR_MEDIA_PENDING.csv](POEDAGAR_MEDIA_PENDING.csv) contém {len(media_rows)} linhas por variante, URLs para consulta e destinos sugeridos para frente, lateral e verso. Os ângulos são uma lista de arquivos a solicitar, não uma afirmação de que essas fotos existem nas fontes. Nenhuma dessas URLs é usada em templates ou como hotlink.

Solicitar originais do fabricante/fornecedor com referência, cor do mostrador, acabamento da caixa, tipo/cor da pulseira e autorização escrita para uso comercial na VRAS. Registrar titular, abrangência e comprovante antes de marcar `autorizado: true`. O destino aprovado é `static/img/products/poedagar/`; até lá há somente instruções nesse diretório.

Não transportar garantias das lojas concorrentes para a VRAS. Há divergências nas fontes: Deluxe indica 40 mm no site 1 e 41 mm no site 2; Golden Star contém 40 e 41 mm na mesma página; Signature contém medidas e descrições de resistência conflitantes. Não foram publicados material, resistência à água, mecanismo, garantia, diâmetro ou outras especificações Poedagar com base nesses textos.

## Evidências e reprodução

- [POEDAGAR_PRICES.csv](POEDAGAR_PRICES.csv): cada variante, ID interno da fonte, preço, Pix condicionado, URL e horário.
- `data/poedagar_sources.json`: metadados públicos, URLs de imagens apenas para análise, hashes e candidatos do site 1.
- [POEDAGAR_CATALOG.md](POEDAGAR_CATALOG.md): inspeção dos arquivos locais e tabela de correspondência.
- `python scripts/review_poedagar.py`: regenera os relatórios offline, sem rede e sem modificar preços.
- `python scripts/review_poedagar.py --refresh`: consulta novamente páginas públicas. Falhas são registradas e nunca substituídas por preços inventados; não há login, download de fotos nem contorno de bloqueios.

O snapshot é histórico, não um preço em tempo real. Falhas de consulta: {len(report['products']) - len(products)} no site 2; {sum('error' in entry for entry in first.values())} nos candidatos do site 1.
"""
    (docs / "POEDAGAR_PRICES.md").write_text(text, encoding="utf-8")
    print(f"Review: {len(products)} listings, {len(variants)} source variants, {len(catalog)} local products. No prices or media published.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Explicitly refresh public metadata; no photographs")
    if parser.parse_args().refresh:
        refresh()
    build_reports()
