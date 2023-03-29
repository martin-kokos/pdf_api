from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams
from bs4 import BeautifulSoup

import io
import re
import time
from statistics import mean


class PdfParser:
    def __init__(self):
        pass

    @staticmethod
    def str_clean(s: str) -> str:
        s = s.replace("-\n", "")  # remove hyphenation
        s = s.replace("\n", " ")
        s = s.replace("\n", " ")
        s = re.sub(r"\s+", " ", s)
        s = s.strip()
        return s

    def get_text_fp(self, file_path: str) -> list[dict]:
        """
        Accepts file_path to a PDF file.

        Returns a list of dicts representing extracted text elements with attributes.
        """
        with open(file_path, "rb") as fin:
            return self.get_text(fin)


    def get_text(self, buffer) -> tuple[list[dict], int]:
        """
        Accepts file-like buffer containing PDF file.

        Returns:
            a list of dicts representing extracted text elements with attributes,
            elapsed seconds
        """
        outbuff = io.StringIO()
        elems = []

        timer_start = time.time()

        extract_text_to_fp(
            buffer, outbuff, laparams=LAParams(), output_type="html", codec=None
        )
        html_repr = outbuff.getvalue()
        soup = BeautifulSoup(html_repr, features="lxml")

        for pos, tag in enumerate(soup.find_all("div")):
            if tag.get_text():
                e = {}
                e["pos"] = pos
                e["string"] = self.str_clean(tag.get_text())
                font_sizes = re.findall(r"font-size:(\d*)", str(tag))
                e["font_size"] = (
                    mean(int(n) for n in font_sizes) if font_sizes else None
                )

                if e["font_size"] is None or e["font_size"] <= 12:
                    e["type"] = "p"
                else:
                    e["type"] = "h1"
                elems.append(e)

        timer_stop = time.time()

        return elems, (timer_stop - timer_start)
