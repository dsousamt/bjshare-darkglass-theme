"""Gera assets/previews/<tema>.webp a partir de preview/demo.html, um por tema, e o
mosaico assets/todos-os-temas.jpg (todas as prévias numa imagem, para posts no fórum).

Uso (na raiz do repositório):  python tools/gerar-previews.py
Requer: pip install playwright pillow  e  python -m playwright install chromium
(ou Chrome instalado: o script tenta o Chrome do sistema primeiro).
Rode depois de mudar cores/estilos, para o guia (index.html) mostrar o visual atual.
"""
import base64
import io
import pathlib

from PIL import Image
from playwright.sync_api import sync_playwright

RAIZ = pathlib.Path(__file__).resolve().parent.parent
DEMO = RAIZ / "preview" / "demo.html"
SAIDA = RAIZ / "assets" / "previews"
MOSAICO = RAIZ / "assets" / "todos-os-temas.jpg"
GUIA = "dsousamt.github.io/bjshare-darkglass-theme"

# Nome exibido e ordem do mosaico (a mesma do guia, index.html)
NOMES = {
    "darkglass": "DarkGlass (padrão)", "light": "Light", "dracula": "Dracula", "oled": "OLED",
    "monochrome": "Monochrome", "solarized": "Solarized", "sepia": "Sépia",
    "highcontrast": "Alto Contraste", "matrix": "Matrix", "cyberpunk": "Cyberpunk", "win95": "Windows 95",
}

MOSAICO_HTML = """<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
<style>
  * { box-sizing: border-box; margin: 0; }
  body { width: 1240px; padding: 32px; background: #0b0d10; color: #c4c9d2; font-family: 'Inter', sans-serif; }
  header { display: flex; align-items: baseline; gap: 14px; margin-bottom: 24px; }
  h1 { color: #f5f6f8; font-size: 34px; font-weight: 800; letter-spacing: -0.02em; }
  h1 span { color: #dc2626; }
  header p { font-size: 17px; color: #8a919c; }
  .grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 20px; }
  figure img { display: block; width: 100%; border-radius: 8px; border: 1px solid rgb(255 255 255 / 0.1); }
  figcaption { margin-top: 8px; color: #f5f6f8; font-size: 16px; font-weight: 600; }
  .info { display: flex; flex-direction: column; justify-content: center; gap: 10px; padding: 20px;
          border: 1px solid rgb(255 255 255 / 0.1); border-radius: 8px; background: #12151b; }
  .info b { color: #f5f6f8; }
  .info .url { color: #ef4444; font-size: 17px; font-weight: 800; }
  .info .nw { white-space: nowrap; }
  .info ol { padding-left: 18px; font-size: 14px; line-height: 1.5; }
</style></head><body>
<header><h1>Dark<span>Glass</span></h1><p>@@N@@ temas para o BJ-Share</p></header>
<div class="grid">@@ITENS@@
  <div class="info">
    <b>Prévias, links e instruções:</b>
    <div class="url">@@GUIA@@</div>
    <ol><li>Configurações → Aparência do Site</li><li>Cole o link em <b>URL de Estilo Externa</b></li><li>Salvar Configurações</li></ol>
  </div>
</div></body></html>"""


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
            page.wait_for_timeout(500)
            # no mega-menu, mostra também o painel de gêneros de Filmes
            filmes = page.locator("#nav_torrents > ul > li > ul > li > a", has_text="Filmes").first.bounding_box()
            page.mouse.move(filmes["x"] + 20, filmes["y"] + filmes["height"] / 2, steps=10)
            page.wait_for_timeout(600)
            png = page.screenshot()
            destino = SAIDA / f"{nome}.webp"
            Image.open(io.BytesIO(png)).save(destino, "WEBP", quality=82, method=6)
            print("gerado:", destino.relative_to(RAIZ))
        gerar_mosaico(browser)
        browser.close()


def gerar_mosaico(browser):
    ordem = [t for t in NOMES if (SAIDA / f"{t}.webp").exists()]
    ordem += [t for t in temas() if t not in NOMES]  # variantes novas ainda sem nome
    itens = ""
    for t in ordem:
        dados = base64.b64encode((SAIDA / f"{t}.webp").read_bytes()).decode()
        itens += f'<figure><img src="data:image/webp;base64,{dados}"><figcaption>{NOMES.get(t, t)}</figcaption></figure>'
    html = MOSAICO_HTML.replace("@@ITENS@@", itens).replace("@@N@@", str(len(ordem))).replace("@@GUIA@@", "/<wbr>".join(f'<span class="nw">{p}</span>' for p in GUIA.split("/")))
    page = browser.new_page(viewport={"width": 1240, "height": 800})
    page.set_content(html, wait_until="networkidle")
    page.evaluate("document.fonts.ready")
    png = page.screenshot(full_page=True)
    page.close()
    Image.open(io.BytesIO(png)).convert("RGB").save(MOSAICO, "JPEG", quality=90, optimize=True, progressive=True)
    print("gerado:", MOSAICO.relative_to(RAIZ))


if __name__ == "__main__":
    main()
