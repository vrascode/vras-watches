from django.contrib.staticfiles.finders import FileSystemFinder

from loja.media import approved_paths


class ApprovedMediaFinder(FileSystemFinder):
    """Keep the legacy archive out of both local static serving and collectstatic."""

    legacy_assets = {"css/theme.css", "css/style.css", "css/swiper-reviews.min.css",
                     "css/welcome-modal.css", "js/welcome-modal.js"}

    @classmethod
    def allowed(cls, path, approved):
        path = path.replace("\\", "/")
        if path in cls.legacy_assets:
            return False
        return not path.startswith(("img/", "videos/")) or path in approved

    def find(self, path, find_all=False, **kwargs):
        if not self.allowed(path, approved_paths()):
            return [] if find_all else None
        return super().find(path, find_all=find_all, **kwargs)

    def list(self, ignore_patterns):
        approved = approved_paths()
        for path, storage in super().list(ignore_patterns):
            if self.allowed(path, approved):
                yield path, storage
