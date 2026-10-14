"""
Gera ícone SVG para o RAGQuery (converter para .ico manualmente ou com ferramenta).
Para converter: https://convertio.co/svg-ico/ ou Pillow.
"""
from pathlib import Path

SVG_CONTENT = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
  <rect width="256" height="256" rx="40" fill="#1a1a2e"/>
  <rect x="20" y="20" width="216" height="216" rx="30" fill="#16213e" stroke="#4fc3f7" stroke-width="3"/>
  <text x="128" y="105" text-anchor="middle" font-family="Segoe UI,Arial,sans-serif" font-size="48" font-weight="bold" fill="#4fc3f7">RAG</text>
  <text x="128" y="155" text-anchor="middle" font-family="Segoe UI,Arial,sans-serif" font-size="32" fill="#a0a0b0">Query</text>
  <line x1="55" y1="175" x2="201" y2="175" stroke="#0f3460" stroke-width="2"/>
  <text x="128" y="200" text-anchor="middle" font-family="Consolas,monospace" font-size="18" fill="#66bb6a">DDL Oracle</text>
</svg>'''

output = Path(__file__).parent / "ragquery.svg"
output.write_text(SVG_CONTENT, encoding="utf-8")
print(f"SVG salvo: {output}")
print("Converta para .ico com: https://convertio.co/svg-ico/")
print("Ou instale Pillow e use cairosvg para converter programaticamente.")

# Tentar gerar .ico com Pillow se disponível
try:
    from PIL import Image
    import io
    import cairosvg

    png_data = cairosvg.svg2png(bytestring=SVG_CONTENT.encode(), output_width=256, output_height=256)
    img = Image.open(io.BytesIO(png_data))
    ico_path = Path(__file__).parent / "ragquery.ico"
    img.save(str(ico_path), format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print(f"ICO gerado: {ico_path}")
except ImportError:
    print("Pillow/cairosvg não disponíveis. Converta o SVG manualmente.")
