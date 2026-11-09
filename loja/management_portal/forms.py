"""Owner attestations are explicit; source listings never preselect a sale variant."""
from urllib.parse import urlsplit

from django import forms


class MultipleImagesInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class ProductImagesField(forms.ImageField):
    widget = MultipleImagesInput(attrs={"accept": "image/jpeg,image/png,image/webp,image/avif"})

    def clean(self, data, initial=None):
        files = data if isinstance(data, (tuple, list)) else [data] if data else []
        if len(files) > 8:
            raise forms.ValidationError("Envie até oito fotos por vez.")
        cleaned = []
        for upload in files:
            if upload.size > 20 * 1024 * 1024:
                raise forms.ValidationError("Cada foto deve ter no máximo 20 MB.")
            image = super().clean(upload, initial)
            if image.image.format not in {"JPEG", "PNG", "WEBP", "AVIF"}:
                raise forms.ValidationError("Use JPG, PNG, WebP ou AVIF.")
            if image.image.width * image.image.height > 40_000_000:
                raise forms.ValidationError("A foto deve ter até 40 megapixels.")
            cleaned.append(image)
        return cleaned


class CatalogReceiptForm(forms.Form):
    catalog_version = forms.CharField(widget=forms.HiddenInput, min_length=64, max_length=64)
    referencia = forms.CharField(label="Referência real do fabricante", max_length=100, required=False)
    fonte = forms.URLField(label="Ficha, manual ou documento correspondente (HTTPS)", required=False)
    identidade_confirmada = forms.BooleanField(
        label="Conferi a marca, o modelo e a referência no produto e no documento informado", required=False)
    variante = forms.TypedChoiceField(label="Variante que a VRAS oferece", coerce=int, empty_value=None, required=False)
    cor_caixa = forms.CharField(label="Cor da caixa", max_length=100, required=False)
    cor_mostrador = forms.CharField(label="Cor do mostrador", max_length=100, required=False)
    cor_pulseira = forms.CharField(label="Cor da pulseira", max_length=100, required=False)
    tipo_pulseira = forms.CharField(label="Tipo da pulseira", max_length=120, required=False)
    variante_confirmada = forms.BooleanField(
        label="Conferi que a variante selecionada e as cores/pulseira correspondem ao produto real", required=False)
    oferta_confirmada = forms.BooleanField(label="A VRAS consegue atender à venda desta variante", required=False)
    registro_oferta = forms.CharField(label="Como a disponibilidade foi confirmada", max_length=500, required=False,
                                      widget=forms.Textarea(attrs={"rows": 2}))
    fotos = ProductImagesField(label="Fotografias reais desta variante", required=False)
    acao_galeria = forms.ChoiceField(label="Galeria", choices=[("append", "Adicionar às fotos existentes"),
                                                              ("replace", "Substituir a galeria por este envio")])
    origem = forms.CharField(label="Autor ou fornecedor das fotos", max_length=200, required=False)
    comprovante = forms.CharField(label="Referência da autorização comercial (sem dados pessoais)",
                                  max_length=300, required=False)
    fotos_autorizadas = forms.BooleanField(
        label="Tenho autorização comercial e conferi que todas as fotos mostram este modelo e variante", required=False)
    usar_banner = forms.BooleanField(
        label="Usar a primeira foto também no banner (autorização inclui esse uso)", required=False)

    def __init__(self, *args, product, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["identidade_confirmada"].label = (
            f"Conferi a marca Poedagar, o modelo {product['modelo']} e a referência no produto e documento")
        self.fields["variante"].choices = [("", "Selecione somente após conferir o produto")]+[
            (v["source_sku_id"], f"{v['title']} — ID de correspondência {v['source_sku_id']}")
            for v in product.get("variantes_fonte", [])]

    def clean(self):
        data = super().clean()
        if data.get("fonte"):
            origin = urlsplit(data["fonte"])
            if origin.scheme != "https" or origin.username or origin.password:
                self.add_error("fonte", "Informe uma fonte HTTPS sem credenciais.")
        if data.get("identidade_confirmada"):
            for name in ("referencia", "fonte"):
                if not data.get(name):
                    self.add_error(name, "Necessário para confirmar a identidade.")
        if data.get("variante_confirmada"):
            if not data.get("identidade_confirmada"):
                self.add_error("identidade_confirmada", "Confirme primeiro a identidade do relógio real.")
            for name in ("variante", "cor_caixa", "cor_mostrador", "cor_pulseira", "tipo_pulseira", "fonte"):
                if not data.get(name):
                    self.add_error(name, "Necessário para confirmar a variante.")
        if data.get("oferta_confirmada"):
            if not data.get("registro_oferta"):
                self.add_error("registro_oferta", "Registre estoque próprio ou a confirmação real de atendimento.")
            if not data.get("variante_confirmada"):
                self.add_error("variante_confirmada", "A disponibilidade precisa corresponder à variante confirmada.")
        if data.get("fotos"):
            for name in ("variante", "origem", "comprovante", "fotos_autorizadas", "variante_confirmada"):
                if not data.get(name):
                    self.add_error(name, "Necessário para importar fotos com correspondência e autorização.")
        elif data.get("usar_banner") or data.get("acao_galeria") == "replace":
            self.add_error("fotos", "Envie as fotografias para esta operação.")
        return data
