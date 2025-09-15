from io import BytesIO
from typing import Iterable, Tuple
from pypdf import PdfReader, PdfWriter

class PdfMergeError(Exception): pass

def merge_pdfs_from_bytes(pdf_blobs: Iterable[bytes]) -> Tuple[bytes, int]:
    writer, total = PdfWriter(), 0
    any_input = False
    for blob in pdf_blobs:
        any_input = True
        if not blob: raise PdfMergeError("Se recibió un PDF vacío.")
        r = PdfReader(BytesIO(blob))
        if getattr(r, "is_encrypted", False):
            try: r.decrypt("")
            except Exception: raise PdfMergeError("PDF protegido con contraseña.")
        for page in r.pages:
            writer.add_page(page); total += 1
    if not any_input or total == 0:
        raise PdfMergeError("No se encontraron páginas válidas.")
    out = BytesIO(); writer.write(out); writer.close(); out.seek(0)
    return out.read(), total

async def merge_pdfs_from_uploadfiles(files) -> Tuple[bytes, int]:
    blobs = [await f.read() for f in files]
    return merge_pdfs_from_bytes(blobs)
