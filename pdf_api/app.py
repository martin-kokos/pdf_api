from fastapi import FastAPI
from fastapi import UploadFile

from pdf_api.utils.pdf_parser import PdfParser

import tempfile

app = FastAPI()

pdf_parser = PdfParser()


@app.get("/status")
async def root():
    return {"status": "OK"}


@app.post("/pdf_text_chunks")
async def text_chunks(file: UploadFile):
    chunks, elapsed_s = pdf_parser.get_text(file.file)
    filesize = file.size
    response = {
        'metadata': {
            'filesize_b': filesize,
            'job_time_s': round(elapsed_s, 2),
        },
        'chunks': chunks,
    }
    return response
