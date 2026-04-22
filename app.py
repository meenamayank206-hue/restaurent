from flask import Flask, request, send_file, render_template_string
import pandas as pd
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter
import os, zipfile, re

app = Flask(__name__)

TEMPLATE = "shaadi.pdf"
OUTPUT = "output"
os.makedirs(OUTPUT, exist_ok=True)

# ---------- UI ----------
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Card Generator</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body { font-family: Arial; background:#f4f4f4; text-align:center; }
.box {
    background:white; padding:20px; margin:20px auto;
    width:90%; max-width:400px;
    border-radius:12px;
}
input, select {
    width:90%; padding:8px; margin:5px;
}
button {
    background:#8B0000; color:white;
    padding:10px; border:none;
    border-radius:6px; margin:5px;
}
</style>

<script>
function addRow() {
    let div = document.createElement("div");
    div.innerHTML = `
        <input name="name" placeholder="Name">
        <input name="address" placeholder="Address">
    `;
    document.getElementById("entries").appendChild(div);
}
</script>
</head>

<body>

<div class="box">
<h2>🎉 Card Generator</h2>

<form method="post" enctype="multipart/form-data">

<p><b>Upload CSV</b></p>
<input type="file" name="file"><br><br>

<p><b>OR Enter Manually</b></p>

<div id="entries">
    <input name="name" placeholder="Name">
    <input name="address" placeholder="Address">
</div>

<button type="button" onclick="addRow()">➕ Add More</button><br><br>

<p><b>Download Type</b></p>
<select name="download_type">
    <option value="zip">ZIP (All Cards)</option>
    <option value="individual">Individual PDFs</option>
</select><br><br>

<button type="submit">🚀 Generate</button>

</form>

</div>

</body>
</html>
"""

# ---------- GENERATE CARDS ----------
def generate_cards(data):
    pdf_paths = []

    for i, row in data.iterrows():
        overlay = f"overlay_{i}.pdf"

        c = canvas.Canvas(overlay)
        c.setFont("Helvetica-Bold", 14)
        c.setFillColorRGB(0.5, 0, 0)

        name = str(row.get('name', '')).strip().upper()
        address = str(row.get('address', '')).strip().upper()

        c.drawString(400, 438, name)
        c.drawString(400, 412, address)

        c.save()

        template_pdf = PdfReader(TEMPLATE)
        overlay_pdf = PdfReader(overlay)

        writer = PdfWriter()

        # Merge first page
        first_page = template_pdf.pages[0]
        first_page.merge_page(overlay_pdf.pages[0])
        writer.add_page(first_page)

        # Add remaining pages
        for p in range(1, len(template_pdf.pages)):
            writer.add_page(template_pdf.pages[p])

        filename = re.sub(r'[^A-Za-z0-9_]', '', name.replace(" ", "_")) + ".pdf"
        path = os.path.join(OUTPUT, filename)

        with open(path, "wb") as f:
            writer.write(f)

        pdf_paths.append(path)
        os.remove(overlay)

    # Create ZIP
    zip_path = os.path.join(OUTPUT, "cards.zip")
    with zipfile.ZipFile(zip_path, "w") as z:
        for f in pdf_paths:
            z.write(f, os.path.basename(f))

    return pdf_paths, zip_path

# ---------- ROUTES ----------
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":

        download_type = request.form.get("download_type")

        # CSV upload
        if request.files.get("file") and request.files["file"].filename != "":
            data = pd.read_csv(request.files["file"]).fillna("")
        else:
            names = request.form.getlist("name")
            addresses = request.form.getlist("address")

            rows = []
            for n, a in zip(names, addresses):
                if n.strip():
                    rows.append({"name": n, "address": a})

            data = pd.DataFrame(rows)

        pdf_paths, zip_path = generate_cards(data)

        # ZIP download
        if download_type == "zip":
            return send_file(zip_path, as_attachment=True)

        # Individual download page
        else:
            links = ""
            for path in pdf_paths:
                fname = os.path.basename(path)
                links += f'<a href="/download/{fname}">{fname}</a><br>'

            return f"<h2>Download PDFs</h2>{links}"

    return render_template_string(HTML)

# Download route
@app.route("/download/<filename>")
def download_file(filename):
    return send_file(os.path.join(OUTPUT, filename), as_attachment=True)

# ---------- START ----------
if __name__ == "__main__":
    app.run()
