"""The owner upload UI publishes only temporary, explicitly fictional test offers."""
import json
import os
import shutil
import subprocess
from unittest import skipUnless

from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from loja.catalog import services
from loja.tests.management_portal.test_receipts import ReceiptWorkspace, ROOT


@skipUnless(os.environ.get("VRAS_BROWSER_QA") == "1", "Requires isolated Chrome CDP and Node")
class CatalogReceiptBrowserTests(ReceiptWorkspace, StaticLiveServerTestCase):
    def test_owner_upload_to_public_storefront_in_browser(self):
        self.prepare_workspace()
        for folder in ("css", "js", "fonts"):
            shutil.copytree(ROOT / "static" / folder, self.root / "static" / folder)
        photos = []
        for name, color in (("front", "gray"), ("side", "navy")):
            path = self.root / f"qa-only-{name}.png"
            path.write_bytes(self.photo(color=color).read())
            photos.append(str(path))
        env = {**os.environ, "QA_BASE_URL": self.live_server_url, "QA_OWNER_PHOTOS": json.dumps(photos),
               "QA_OWNER_VARIANT": str(self.catalog[0]["variantes_fonte"][0]["source_sku_id"])}
        result = subprocess.run(["node", "scripts/owner_browser_qa.mjs"], cwd=ROOT, env=env,
                                capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(len(services.get_products()), 1)
        self.assertIn('"ownerUploadAndPublication": "passed"', result.stdout)
