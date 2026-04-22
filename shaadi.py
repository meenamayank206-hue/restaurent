import pandas as pd
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter
import os
import re

# ✅ Load CSV safely (fix NaN issue)
data = pd.read_csv("J:/shaadi/data.csv").fillna("")

# Template PDF (4-page card)
template = "J:/shaadi/shaadi.pdf"

for i, row in data.iterrows():
    overlay_file = f"overlay_{i}.pdf"

    # Create overlay
    c = canvas.Canvas(overlay_file)

    c.setFont("Helvetica-Bold", 16)

    # 🔴 Dark red color
    c.setFillColorRGB(0.5, 0, 0)

    # ✅ Clean text (safe + uppercase)
    name = str(row.get('name', '')).strip().upper()
    address = str(row.get('address', '')).strip().upper()

    # 🎯 Final coordinates
    c.drawString(400, 438, name)
    c.drawString(400, 414, address)
    

    c.save()

    # Read PDFs
    template_pdf = PdfReader(template)
    overlay_pdf = PdfReader(overlay_file)

    writer = PdfWriter()

    # Merge only first page
    first_page = template_pdf.pages[0]
    first_page.merge_page(overlay_pdf.pages[0])
    writer.add_page(first_page)

    # Add remaining pages (2,3,4)
    for page_num in range(1, len(template_pdf.pages)):
        writer.add_page(template_pdf.pages[page_num])

    # ✅ Safe filename
    safe_name = re.sub(r'[^A-Za-z0-9_]', '', name.replace(" ", "_"))

    output_path = f"J:/shaadi/{safe_name}.pdf"

    # Save final PDF
    with open(output_path, "wb") as f:
        writer.write(f)

    # 🧹 Delete overlay file
    os.remove(overlay_file)

print("✅ All cards generated successfully!")