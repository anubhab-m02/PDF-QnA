def build_minimal_pdf(text: str = "Hello World") -> bytes:
    """Hand-build a minimal single-page PDF with a valid xref table so pypdf can parse it
    without external dependencies like reportlab."""
    objects = [
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n",
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n",
        b"3 0 obj<</Type/Page/Parent 2 0 R/Resources<</Font<</F1 4 0 R>>>>/MediaBox[0 0 200 200]/Contents 5 0 R>>endobj\n",
        b"4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n",
    ]
    stream_content = f"BT /F1 24 Tf 20 100 Td ({text}) Tj ET".encode()
    objects.append(
        b"5 0 obj<</Length " + str(len(stream_content)).encode() + b">>\nstream\n"
        + stream_content + b"\nendstream\nendobj\n"
    )

    body = b"%PDF-1.4\n"
    offsets = []
    for obj in objects:
        offsets.append(len(body))
        body += obj

    xref_offset = len(body)
    n = len(objects) + 1
    xref = b"xref\n0 " + str(n).encode() + b"\n0000000000 65535 f \n"
    for off in offsets:
        xref += ("%010d 00000 n \n" % off).encode()
    trailer = (
        b"trailer\n<</Size " + str(n).encode() + b"/Root 1 0 R>>\nstartxref\n"
        + str(xref_offset).encode() + b"\n%%EOF"
    )
    return body + xref + trailer
