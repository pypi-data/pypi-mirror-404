from pypdf import PdfReader, PdfWriter



################################################################################################################################
################################################################################################################################
####################################### Rota los grados y paginas deseadas de un pdf ###########################################
################################################################################################################################
################################################################################################################################
def rotarPaginasPdf(pdf_entrada, pdf_salida, paginas_a_rotar, grados):
    """
    Rota páginas específicas de un PDF.

    pdf_entrada: str -> ruta del PDF original
    pdf_salida: str -> ruta del PDF modificado
    paginas_a_rotar: list[int] -> índices de páginas a rotar (0 = primera)
    grados: int -> grados de rotación (90, 180, 270)
    """

    reader = PdfReader(pdf_entrada)
    writer = PdfWriter()

    for i, page in enumerate(reader.pages):
        if i in paginas_a_rotar:
            page.rotate(grados)
        writer.add_page(page)

    with open(pdf_salida, "wb") as f:
        writer.write(f)
