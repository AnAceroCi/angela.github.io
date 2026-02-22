#!/usr/bin/env python3
"""
Genera un archivo HTML autocontenido con la hoja de vida y credenciales.

Convierte la foto de perfil y cada pagina de los PDFs a imagenes base64
para incrustarlos en un unico archivo HTML sin dependencias externas.

Requisitos:
    pip install PyMuPDF

Uso:
    python generar_credenciales.py

Salida:
    credenciales_final.html
"""

import base64
import os
import re
import sys

try:
    import fitz  # PyMuPDF
except ImportError:
    print("=" * 60)
    print("ERROR: PyMuPDF no esta instalado.")
    print("Instalalo con:")
    print("    pip install PyMuPDF")
    print("=" * 60)
    sys.exit(1)


def encode_file_b64(path):
    """Lee un archivo y lo codifica en base64."""
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def pdf_to_images_b64(path, dpi=200, rotate_cw=False):
    """Convierte cada pagina de un PDF a imagen PNG en base64.
    Si rotate_cw=True, rota cada pagina 90 grados a la derecha (clockwise).
    """
    images = []
    doc = fitz.open(path)
    total = len(doc)
    for i in range(total):
        page = doc[i]
        if rotate_cw:
            page.set_rotation((page.rotation + 90) % 360)
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        b64 = base64.b64encode(img_bytes).decode('utf-8')
        images.append(b64)
        print(f"    Pagina {i + 1}/{total} convertida")
    doc.close()
    return images


def main():
    # Cambiar al directorio del script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Archivos requeridos
    photo_file = '26.jpg.jpeg'
    html_template = 'credenciales.html'
    pdf_files = ['T1.pdf', 'tp1.pdf', 'T2.pdf', 'tp2.pdf']

    required = [photo_file, html_template] + pdf_files
    missing = [f for f in required if not os.path.exists(f)]
    if missing:
        print("ERROR: No se encontraron los siguientes archivos:")
        for f in missing:
            print(f"    - {f}")
        sys.exit(1)

    # 1. Codificar foto de perfil
    print("[1/3] Procesando foto de perfil...")
    photo_b64 = encode_file_b64(photo_file)
    print(f"    Foto codificada ({os.path.getsize(photo_file) / 1024:.0f} KB)")

    # 2. Convertir PDFs a imagenes
    print("[2/3] Convirtiendo PDFs a imagenes...")
    # T2.pdf se rota 90 grados a la derecha (clockwise)
    rotate_map = {'T2.pdf': True}
    pdf_sections = {}
    for pdf_name in pdf_files:
        print(f"  Procesando {pdf_name}...")
        rotate = rotate_map.get(pdf_name, False)
        images_b64 = pdf_to_images_b64(pdf_name, dpi=200, rotate_cw=rotate)
        # Generar HTML para las imagenes de este PDF
        img_tags = []
        for i, img_b64 in enumerate(images_b64):
            img_tags.append(
                f'<img src="data:image/png;base64,{img_b64}" '
                f'alt="Pagina {i + 1}" '
                f'style="width:100%;display:block;margin:0;padding:0;">'
            )
        pdf_sections[pdf_name] = '\n'.join(img_tags)

    # 3. Leer HTML y reemplazar assets
    print("[3/3] Generando HTML autocontenido...")
    with open(html_template, 'r', encoding='utf-8') as f:
        html = f.read()

    # Reemplazar foto
    html = html.replace(
        f'src="{photo_file}"',
        f'src="data:image/jpeg;base64,{photo_b64}"'
    )

    # Reemplazar cada <object> PDF con imagenes inline
    for pdf_name in pdf_files:
        pattern = (
            r'<object[^>]*data="'
            + re.escape(pdf_name)
            + r'"[^>]*>.*?</object>'
        )
        html = re.sub(pattern, pdf_sections[pdf_name], html, flags=re.DOTALL)

    # Escribir archivo final
    output_file = 'index.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    size_mb = os.path.getsize(output_file) / 1024 / 1024
    print()
    print("=" * 50)
    print(f"  Archivo generado: {output_file}")
    print(f"  Tamano: {size_mb:.1f} MB")
    print("=" * 50)
    print()
    print("Puedes abrir el archivo en cualquier navegador.")
    print("Es completamente autocontenido (un solo archivo HTML).")


if __name__ == '__main__':
    main()
