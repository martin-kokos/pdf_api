from pdf_api.utils.pdf_parser import PdfParser


def test_pdf_file_parser():
    test_file_path = "tests/files/ZA7505_cdb.pdf"

    parser = PdfParser()

    text_elems = parser.get_text_fp(test_file_path)

    assert text_elems[12670] == {
        "pos": 12672,
        "string": "page 351",
        "font_size": 8,
        "type": "p",
    }
