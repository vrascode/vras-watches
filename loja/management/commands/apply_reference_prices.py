import copy
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from loja.catalog import repository, services
from loja.catalog.pricing import price_update


class Command(BaseCommand):
    help = "Apply explicitly authorized verified unit prices; retain all publication gates."

    def add_arguments(self, parser):
        parser.add_argument("--approval-record", required=True, help="Record of the owner's explicit price authorization")
        parser.add_argument("--apply", action="store_true")

    def handle(self, *args, **options):
        target = Path(repository.PRODUCTS_PATH)
        original = target.read_bytes()
        catalog = json.loads(original)
        path = settings.BASE_DIR / "data/poedagar_price_verification.json"
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError) as error:
            raise CommandError(f"Verificação atual inacessível: {error}") from error
        evidence = {p["product_id"]: p for p in report["products"]}
        now = datetime.now(timezone.utc)
        try:
            checked = datetime.fromisoformat(report["checked_at_utc"])
            if checked.tzinfo is None or not -timedelta(minutes=5) <= now - checked <= timedelta(hours=24):
                raise ValueError("Consulta não é recente")
        except (KeyError, ValueError, TypeError) as error:
            raise CommandError("Refaça scripts/verify_poedagar_prices.py antes de aplicar preços.") from error
        local_day = now.astimezone(ZoneInfo("America/Sao_Paulo")).date().isoformat()
        updated, errors = [], []
        for product in catalog:
            try:
                item = price_update(product, evidence.get(product["id"], {}), options["approval_record"], local_day)
                updated.append(item)
            except (ValueError, KeyError, TypeError) as error:
                item = copy.deepcopy(product)
                item["status"] = "rascunho"
                item["preco"] = None
                item["aprovacao_preco"] = {"aprovado": False, "motivo": str(error)}
                item.setdefault("pendencias", []).append("Preço atual não confirmado: " + str(error))
                updated.append(item)
                errors.append({"product_id": product["id"], "error": str(error)})
        published = []
        if options["apply"]:
            if target.read_bytes() != original:
                raise CommandError("Catálogo mudou durante a conferência; nenhuma aplicação realizada.")
            self.write_catalog(target, updated)
            # Owner authorized publication only when every other requirement passes.
            readiness = {p["id"]: p for p in services.get_products(include_drafts=True)}
            for product in updated:
                issues = set(readiness[product["id"]]["publication_issues"]) - {"produto_em_rascunho"}
                if product["status"] == "rascunho" and not issues:
                    product["status"] = "publicado"
                    published.append(product["id"])
            if published:
                self.write_catalog(target, updated)
        self.stdout.write(json.dumps({"applied": options["apply"], "updated_prices": len(updated) - len(errors),
                                     "published_products": published, "pending": errors}, ensure_ascii=True))

    @staticmethod
    def write_catalog(target, catalog):
        temporary = target.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(target)
