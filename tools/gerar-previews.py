"""Gera assets/previews/<tema>.webp a partir de preview/demo.html, um por tema.

Uso (na raiz do repositório):  python tools/gerar-previews.py
Requer: pip install playwright pillow  e  python -m playwright install chromium
(ou Chrome instalado: o script tenta o Chrome do sistema primeiro).
Rode depois de mudar cores/estilos, para o guia (index.html) mostrar o visual atual.
"""
import io
import pathlib

from PIL import Image
from playwright.sync_api import sync_playwright

RAIZ = pathlib.Path(__file__).resolve().parent.parent
DEMO = RAIZ / "preview" / "demo.html"
SAIDA = RAIZ / "assets" / "previews"


def temas():
    """'darkglass' (o base) + cada bj-zerfeus-theme-<nome>.css que não seja bundle."""
    nomes = ["darkglass"]
    for f in sorted(RAIZ.glob("bj-zerfeus-theme-*.css")):
        if not f.name.endswith(".full.css"):
            nomes.append(f.stem.removeprefix("bj-zerfeus-theme-"))
    return nomes


def abrir_navegador(p):
    try:
        return p.chromium.launch(channel="chrome")
    except Exception:
        return p.chromium.launch()


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = abrir_navegador(p)
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        for nome in temas():
            url = DEMO.as_uri() + ("" if nome == "darkglass" else f"?tema={nome}")
            page.mouse.move(640, 700)  # tira o mouse do menu aberto no tema anterior
            page.goto(url, wait_until="networkidle")
            page.evaluate("document.fonts.ready")
            page.wait_for_timeout(400)
            # menu aberto mostra o dropdown do tema; o atraso de abertura é 0.3s
            caixa = page.locator("#nav_torrents > a").bounding_box()
            page.mouse.move(caixa["x"] + caixa["width"] / 2, caixa["y"] + caixa["height"] / 2)
            page.wait_for_timeout(800)
            png = page.screenshot()
            destino = SAIDA / f"{nome}.webp"
            Image.open(io.BytesIO(png)).save(destino, "WEBP", quality=82, method=6)
            print("gerado:", destino.relative_to(RAIZ))
        browser.close()


if __name__ == "__main__":
    main()
