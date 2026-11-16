"""
Transforma os designs (HTML) em imagens JPEG usando o navegador Chromium.

Uso no código:
    with Renderizador() as r:
        r.gerar("oferta", campos, "saida/x.jpg")
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

from designs import DESIGNS

PASTA = Path(__file__).resolve().parent
TPL = PASTA / "templates"
STORIES = {"story", "story_foto"}


class Renderizador:
    def __enter__(self):
        self._pw = sync_playwright().start()
        self._nav = self._pw.chromium.launch()
        self._pag = self._nav.new_page(viewport={"width": 1080, "height": 1350})
        self.problemas = []
        return self

    def __exit__(self, *a):
        self._nav.close()
        self._pw.stop()

    def gerar(self, design, campos, destino):
        story = design in STORIES
        altura = 1920 if story else 1350
        self._pag.set_viewport_size({"width": 1080, "height": altura})
        TPL.mkdir(exist_ok=True)
        tmp = TPL / "_tmp_arte.html"
        tmp.write_text(DESIGNS[design](campos), encoding="utf-8")
        self._pag.goto(tmp.as_uri())
        self._pag.wait_for_load_state("networkidle")
        self._pag.wait_for_function("window.pronto === true", timeout=20000)
        self._pag.wait_for_timeout(150)  # deixa os scripts de posição terminarem
        prob = self._pag.evaluate("window.problemas || []")
        if prob:
            self.problemas.append((str(destino), prob))
        destino = Path(destino)
        destino.parent.mkdir(parents=True, exist_ok=True)
        self._pag.screenshot(path=str(destino), type="jpeg", quality=92,
                             clip={"x": 0, "y": 0, "width": 1080, "height": altura})
        tmp.unlink(missing_ok=True)
        return destino
