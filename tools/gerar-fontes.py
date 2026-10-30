"""Gera as duas fontes embutidas em bj-zerfeus-theme.css e grava o base64 delas no CSS.

O site manda o release como texto solto ("[MKV / H.264 / WEB-DL / ...]"), sem um elemento por
item, então o CSS sozinho não consegue esconder colchetes e barras nem desenhar uma pílula por
item. As fontes fazem isso no desenho do texto:

- BJ Sep: só "/", "[" e "]", sem desenho ("/" vira um espaço). Usada no ano e nos títulos.
- BJ Tag: subconjunto Latin da Inter 500 (sem kerning) em que cada caractere tem um fundo
  (COLRv0, camada na cor da paleta + a letra em currentColor). Letras vizinhas formam uma faixa
  contínua; regras calt (GSUB) trocam o espaço colado à barra por bordas arredondadas, a barra
  pelo vão entre pílulas e os colchetes por bordas (ou nada). Resultado: uma pílula por item.
- BJ Title: subconjunto Latin da Inter 700 (com kerning) para o título do lançamento. Uma regra
  calt em cascata troca tudo de "[" até "]" por versões 88% menores, pintadas na cor do texto
  com 55% de opacidade (COLRv1): "A Anatomia de Grey [Grey's Anatomy]" fica com a parte entre
  colchetes secundária, em qualquer tema. Sem COLRv1 (Safari), a parte fica só menor.

Uso (na raiz do repositório):  python tools/gerar-fontes.py
Requer: pip install fonttools  (baixa a Inter 500 e 700 do Google Fonts)
A Inter é licenciada sob a SIL Open Font License 1.1; o aviso de copyright e a licença ficam
na tabela "name" da BJ Tag e da BJ Title.
"""
import base64
import copy
import io
import pathlib
import re
import urllib.request

from fontTools import subset
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import C_P_A_L_
from fontTools.ttLib.tables.C_O_L_R_ import LayerRecord
from fontTools.ttLib.tables import otTables as ot
from fontTools.colorLib.builder import buildCOLR, buildCPAL

RAIZ = pathlib.Path(__file__).resolve().parent.parent
CSS = RAIZ / "bj-zerfeus-theme.css"

# BJ Tag (unidades de 2048 por em)
PAD, GAP, R = 700, 820, 700   # borda da pílula, vão entre pílulas, raio dos cantos
Y0, Y1 = -420, 1910           # faixa do fundo, centrada na altura das maiúsculas
TINT = (150, 155, 170, 52)    # cor do fundo (RGBA): cinza translúcido, serve no claro e no escuro
# BJ Title
ESCALA, ALFA = 0.88, 0.55     # parte entre colchetes: tamanho e opacidade


def baixar_inter(peso):
    req = urllib.request.Request(f"https://fonts.googleapis.com/css2?family=Inter:wght@{peso}",
                                 headers={"User-Agent": "Mozilla/4.0"})  # UA antigo: link .ttf
    css = urllib.request.urlopen(req, timeout=30).read().decode()
    url = re.search(r"url\((https://[^)]+\.ttf)\)", css).group(1)
    return TTFont(io.BytesIO(urllib.request.urlopen(url, timeout=60).read()))


def vazio():
    return TTGlyphPen(None).glyph()


def retangulo(x0, x1, rl=0, rr=0):
    """Retângulo da faixa, com cantos arredondados à esquerda (rl) e/ou à direita (rr)."""
    pen = TTGlyphPen(None)
    pen.moveTo((x0 + rl, Y0))
    if rr:
        pen.lineTo((x1 - rr, Y0)); pen.qCurveTo((x1, Y0), (x1, Y0 + rr))
        pen.lineTo((x1, Y1 - rr)); pen.qCurveTo((x1, Y1), (x1 - rr, Y1))
    else:
        pen.lineTo((x1, Y0)); pen.lineTo((x1, Y1))
    if rl:
        pen.lineTo((x0 + rl, Y1)); pen.qCurveTo((x0, Y1), (x0, Y1 - rl))
        pen.lineTo((x0, Y0 + rl)); pen.qCurveTo((x0, Y0), (x0 + rl, Y0))
    else:
        pen.lineTo((x0, Y1)); pen.lineTo((x0, Y0))
    pen.closePath()
    return pen.glyph()


def bj_sep():
    fb = FontBuilder(1000, isTTF=True)
    nomes = [".notdef", "slash", "bracketleft", "bracketright"]
    fb.setupGlyphOrder(nomes)
    fb.setupCharacterMap({0x2F: "slash", 0x5B: "bracketleft", 0x5D: "bracketright"})
    fb.setupGlyf({n: vazio() for n in nomes})
    fb.setupHorizontalMetrics({".notdef": (0, 0), "slash": (350, 0), "bracketleft": (0, 0), "bracketright": (0, 0)})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({"familyName": "BJ Sep", "styleName": "Regular"})
    fb.setupOS2(sTypoAscender=800, sTypoDescender=-200, usWinAscent=800, usWinDescent=200)
    fb.setupPost()
    buf = io.BytesIO(); fb.save(buf)
    return buf.getvalue()


def bj_tag(f):
    opts = subset.Options()
    opts.layout_features = []
    opts.hinting = False
    opts.notdef_outline = True
    opts.drop_tables += ["GPOS", "GSUB", "GDEF", "STAT", "gasp", "prep"]
    opts.name_IDs = [0, 1, 2, 13, 14]  # mantém copyright e licença (OFL)
    sub = subset.Subsetter(opts)
    sub.populate(unicodes=list(range(0x20, 0x7F)) + list(range(0xA0, 0x100)))
    sub.subset(f)

    cmap, glyf, hmtx = f.getBestCmap(), f["glyf"], f["hmtx"]
    space, slash, bl, br, nbsp = (cmap[c] for c in (0x20, 0x2F, 0x5B, 0x5D, 0xA0))
    ordem = list(f.getGlyphOrder())
    letras = [g for g in ordem if g not in (".notdef", space, slash, bl, br, nbsp) and hmtx[g][0] > 0]

    novos, colr = {}, {}
    def fundo(w):
        nome = f"bg.{w}"
        novos.setdefault(nome, (retangulo(0, w), w))
        return nome
    for g in letras:
        w = hmtx[g][0]
        novos[g + ".fg"] = (copy.deepcopy(glyf[g]), w)
        colr[g] = [(fundo(w), 0), (g + ".fg", 0xFFFF)]   # 0xFFFF = cor do texto
    space_w = hmtx[space][0]  # largura do espaço entre palavras do mesmo item ("Full HD")
    # espaço, barra e colchetes sem fundo; o espaço sem largura (o vão vem só da barra)
    for g, w in ((space, 0), (nbsp, 0), (slash, GAP), (bl, 0), (br, 0)):
        glyf[g] = vazio(); hmtx[g] = (w, 0)
    for nome, (rl, rr, w) in {"pad.mid": (0, 0, space_w), "pad.r": (0, R, PAD), "pad.l": (R, 0, PAD)}.items():
        novos[nome + ".bg"] = (retangulo(0, w, rl, rr), w)
        novos[nome] = (vazio(), w)
        colr[nome] = [(nome + ".bg", 0)]
    novos["gap"] = (vazio(), GAP)  # espaço depois de "]" ("Free] INTERNAL" vem sem barra)

    for nome, (g, w) in novos.items():
        glyf[nome] = g; hmtx[nome] = (w, 0)
    f.setGlyphOrder(ordem + list(novos))
    glyf.glyphOrder = f.getGlyphOrder()
    f["maxp"].numGlyphs = len(f.getGlyphOrder())

    c = newTable("COLR"); c.version = 0
    c.ColorLayers = {b: [LayerRecord(name=n, colorID=i) for n, i in camadas] for b, camadas in colr.items()}
    f["COLR"] = c
    p = newTable("CPAL"); p.version = 0; p.numPaletteEntries = 1
    p.palettes = [[C_P_A_L_.Color(red=TINT[0], green=TINT[1], blue=TINT[2], alpha=TINT[3])]]
    f["CPAL"] = p

    addOpenTypeFeaturesFromString(f, f"""
        languagesystem DFLT dflt; languagesystem latn dflt;
        @L = [{" ".join(letras)}];
        @SP = [{space} {nbsp}];
        feature calt {{
            sub @L @SP' @L by pad.mid;
            sub @L @SP' by pad.r;
            sub @SP' @L by pad.l;
            sub {bl}' @L by pad.l;
            sub @L {br}' by pad.r;
            sub {br} @SP' by gap;
        }} calt;
    """)
    for nid, valor in ((1, "BJ Tag"), (4, "BJ Tag"), (6, "BJTag")):
        f["name"].setName(valor, nid, 3, 1, 0x409)
    buf = io.BytesIO(); f.save(buf)
    return buf.getvalue()


def bj_title(f):
    opts = subset.Options()
    opts.layout_features = ["kern"]
    opts.hinting = False
    opts.notdef_outline = True
    opts.drop_tables += ["GSUB", "STAT", "gasp", "prep"]
    opts.name_IDs = [0, 1, 2, 13, 14]
    sub = subset.Subsetter(opts)
    sub.populate(unicodes=list(range(0x20, 0x7F)) + list(range(0xA0, 0x100)))
    sub.subset(f)

    cmap, glyf, hmtx = f.getBestCmap(), f["glyf"], f["hmtx"]
    bl, br = cmap[0x5B], cmap[0x5D]
    ordem = list(f.getGlyphOrder())
    base = [g for g in ordem if g not in (".notdef", bl, br) and g in cmap.values()]
    novos, cores = {}, {}
    def menor(g):
        """Composta com a glifo original reduzida (sobre a linha de base)."""
        pen = TTGlyphPen(glyf)
        if glyf[g].numberOfContours != 0:
            pen.addComponent(g, (ESCALA, 0, 0, ESCALA, 0, 0))
        return pen.glyph()
    for g in base + [bl, br]:
        w = round(hmtx[g][0] * ESCALA)
        novos[g + ".alt"] = (menor(g), w)
        novos[g + ".alt.o"] = (menor(g), w)
        cores[g + ".alt"] = {
            "Format": ot.PaintFormat.PaintGlyph, "Glyph": g + ".alt.o",
            "Paint": {"Format": ot.PaintFormat.PaintSolid, "PaletteIndex": 0xFFFF, "Alpha": ALFA},
        }
    for nome, (g, w) in novos.items():
        glyf[nome] = g; hmtx[nome] = (w, 0)
    f.setGlyphOrder(ordem + list(novos))
    glyf.glyphOrder = f.getGlyphOrder()
    f["maxp"].numGlyphs = len(f.getGlyphOrder())
    f["COLR"] = buildCOLR(cores, version=1, glyphMap=f.getReverseGlyphMap())
    f["CPAL"] = buildCPAL([[(0, 0, 0, 1.0)]])

    # Uma consulta por vez: primeiro "[" vira .alt; depois, da esquerda para a direita, cada
    # glifo precedido de um .alt também vira .alt (a regra vê as trocas já feitas), até "]".
    B = " ".join(base); A = " ".join(g + ".alt" for g in base)
    addOpenTypeFeaturesFromString(f, f"""
        languagesystem DFLT dflt; languagesystem latn dflt;
        @B = [{B}];
        @A = [{A}];
        @ANTES = [{bl}.alt @A];
        lookup abre {{ sub {bl} by {bl}.alt; }} abre;
        lookup cascata {{
            sub @ANTES @B' by @A;
            sub @ANTES {br}' by {br}.alt;
        }} cascata;
        feature calt {{ lookup abre; lookup cascata; }} calt;
    """, tables=["GSUB"])
    for nid, valor in ((1, "BJ Title"), (4, "BJ Title"), (6, "BJTitle")):
        f["name"].setName(valor, nid, 3, 1, 0x409)
    buf = io.BytesIO(); f.save(buf)
    return buf.getvalue()


def gravar(css, familia, dados):
    padrao = re.compile(r"(font-family: '" + familia + r"';\s*src: url\(data:font/ttf;base64,)[A-Za-z0-9+/=]*(\))")
    css, n = padrao.subn(lambda m: m.group(1) + base64.b64encode(dados).decode() + m.group(2), css)
    if n != 1:
        raise SystemExit(f"@font-face de {familia} não encontrado no CSS")
    return css


if __name__ == "__main__":
    css = CSS.read_text(encoding="utf-8")
    sep, tag, title = bj_sep(), bj_tag(baixar_inter(500)), bj_title(baixar_inter(700))
    css = gravar(gravar(gravar(css, "BJ Sep", sep), "BJ Tag", tag), "BJ Title", title)
    CSS.write_text(css, encoding="utf-8", newline="")
    print(f"BJ Sep: {len(sep)} bytes, BJ Tag: {len(tag)} bytes, BJ Title: {len(title)} bytes -> {CSS.name}")
