"""Crop the original figures out of the two Lab0 papers as vector PDFs.

Run from the repository root (needs PyMuPDF: pip install pymupdf):
    python lab0/translation/extract_figures.py
Clip rectangles are in PDF points (x0, y0, x1, y1) on 1-based pages.
"""
from pathlib import Path

import fitz

LAB0 = Path(__file__).resolve().parents[1]
OUT = LAB0 / "translation" / "figures"

ZHANG = LAB0 / "张正友标定99FlexibleCameraCalibrationByViewingaPlaneFromUnknownOrientations.pdf"
FUSIELLO = LAB0 / "2000！Acompactalgorithmforrectificationofstereopairs.pdf"

CROPS = {
    ZHANG: {
        "zhang_fig1": (4, (305, 69, 550, 140)),
        "zhang_fig2": (5, (48, 69, 288, 140)),
        "zhang_fig3": (5, (48, 169, 288, 236)),
        "zhang_fig4": (6, (50, 71, 545, 142)),
        "zhang_fig5": (5, (331, 71, 523, 140)),
        "zhang_fig6": (7, (50, 76, 262, 153)),
        "zhang_fig7": (7, (285, 71, 545, 159)),
    },
    FUSIELLO: {
        "fusiello_fig1": (2, (305, 53, 480, 269)),
        "fusiello_fig2": (3, (41, 53, 250, 283)),
        "fusiello_fig3": (4, (41, 53, 288, 247)),
        "fusiello_fig4": (4, (41, 294, 288, 489)),
        "fusiello_fig5": (5, (42, 61, 387, 339)),
        "fusiello_fig6": (5, (42, 367, 387, 726)),
        "fusiello_fig7": (6, (40, 53, 262, 394)),
        "fusiello_fig8": (6, (300, 53, 522, 394)),
    },
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for source, crops in CROPS.items():
        src = fitz.open(source)
        for name, (page, box) in crops.items():
            clip = fitz.Rect(box)
            doc = fitz.open()
            doc.new_page(width=clip.width, height=clip.height).show_pdf_page(
                fitz.Rect(0, 0, clip.width, clip.height), src, page - 1, clip=clip
            )
            doc.save(OUT / f"{name}.pdf", garbage=4, deflate=True)
            print(f"{name}.pdf  page {page}  {clip}")


if __name__ == "__main__":
    main()
