import secrets
import hashlib
import datetime as dt

from typing import Annotated

from logging import getLogger

from fastapi import FastAPI, UploadFile, Depends, Form
from fastapi import Request, Response, status, HTTPException

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from sqlalchemy import select, or_
from sqlalchemy.orm import defer

import jwt

from pdf_api.utils.pdf_parser import PdfParser
from pdf_api.config import JWT_SECRET
from pdf_api.db import Session
from pdf_api.models import User
from pdf_api.models import Document

log = getLogger(__name__)

limiter = Limiter(lambda: "any")
app = FastAPI()

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

pdf_parser = PdfParser()


@app.get("/status")
async def root():
    return {"status": "OK"}


@app.post("/pdf_text_chunks")
@limiter.limit("100/minute")
async def text_chunks(request: Request, file: UploadFile):
    chunks, elapsed_s = pdf_parser.get_text(file.file)

    return {
        "metadata": {
            "filesize_b": file.size,
            "job_time_s": round(elapsed_s, 2),
        },
        "chunks": chunks,
    }


# Auth
async def jwt_auth_user_id(request: Request) -> Annotated[int | None, "user_id"]:
    encoded_jwt = request.cookies.get("jwt_token")
    if not encoded_jwt:
        return None

    try:
        token = jwt.decode(encoded_jwt, key=JWT_SECRET, algorithms="HS256")
    except jwt.exceptions.DecodeError:
        log.error("Request containing corrupted JWT token")
        return None

    with Session.begin() as sess:
        user = sess.get(User, token["user_id"])

    if (user is None) or not secrets.compare_digest(user.secret, token["secret"]):
        return None

    return user.id


# Users
@app.get("/users")
async def users_get():
    """
    List users
    """
    with Session.begin() as sess:
        users = sess.execute(select(User)).scalars().fetchall()
    return {"users": [{"user_id": user.id, "username": user.username, "created_at": user.created_at} for user in users]}


@app.post("/user/new")
@limiter.limit("100/minute")
async def user_create(request: Request, response: Response, username: Annotated[str, Form()]):
    """
    Create user
    """
    new_user = User(username=username, created_at=dt.datetime.utcnow(), secret=secrets.token_hex(32))

    with Session.begin() as sess:
        sess.add(new_user)
        sess.commit()

    encoded_jwt = jwt.encode({"user_id": new_user.id, "secret": new_user.secret}, JWT_SECRET, algorithm="HS256")
    response.set_cookie(key="jwt_token", value=encoded_jwt)
    response.set_cookie(key="uid", value=str(new_user.id))
    response.status_code = status.HTTP_201_CREATED
    return


@app.delete("/user/{_id}")
async def user_delete(user_id: Annotated[str, Depends(jwt_auth_user_id)], _id: int):
    """
    Delete user
    """
    if user_id is None or (user_id != _id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    with Session.begin() as sess:
        user = sess.get(User, user_id)
        sess.delete(user)
        sess.commit()

    return


@app.get("/user/{_id}")
async def user_get(user_id: Annotated[str, Depends(jwt_auth_user_id)], _id: int):
    """
    Get user details
    """
    if user_id is None or (user_id != _id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    with Session.begin() as sess:
        user = sess.get(User, user_id)

    return {"user": {"user_id": user.id, "username": user.username, "created_at": user.created_at}}


@app.put("/user/{_id}/update")
async def user_update(user_id: Annotated[str, Depends(jwt_auth_user_id)], _id: int, username: str | None = None):
    """
    Modify user
    """
    if user_id is None or (user_id != _id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    with Session.begin() as sess:
        user = sess.get(User, user_id)

        if username is not None:
            user.username = username

        sess.commit()

    return


# Documents
@app.get("/documents")
async def documents_get(user_id: Annotated[str, Depends(jwt_auth_user_id)]):
    """
    Get all documents
    """
    with Session.begin() as sess:
        documents = (
            sess.execute(select(Document).join(User.documents).where(or_(Document.public is True, Document.owner_id == user_id)))
            .scalars()
            .fetchall()
        )

    return {
        "documents": [
            {
                "filename": d.filename,
                "submitted_at": d.submitted_at,
                "public": d.public,
                "content_size": d.content_size,
            }
            for d in documents
        ]
    }


@app.get("/user/{_id}/documents")
async def user_get_documents(user_id: Annotated[str, Depends(jwt_auth_user_id)], _id: int):
    """
    Get user's documents
    """
    if user_id is None or (user_id != _id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    with Session.begin() as sess:
        documents = sess.execute(select(Document).where(Document.owner_id == user_id)).scalars().fetchall()

    return {
        "documents": [
            {
                "id": d.id,
                "filename": d.filename,
                "submitted_at": d.submitted_at,
                "public": d.public,
                "content_size": d.content_size,
            }
            for d in documents
        ]
    }


@app.get("/document/{document_id}")
async def user_get_document(user_id: Annotated[str, Depends(jwt_auth_user_id)], document_id: int):
    """
    Get document
    """
    with Session.begin() as sess:
        readable = (
            sess.execute(
                select(Document)
                .join(User)
                .where(Document.id == document_id)
                .where(or_(Document.public is True, Document.owner_id == user_id))
            )
            .scalars()
            .one_or_none()
        )
        if readable:
            document = sess.get(Document, readable.id)
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )

    return {
        "document": {
            "filename": document.filename,
            "submitted_at": document.submitted_at,
            "public": document.public,
            "content_size": document.content_size,
            "chunks": document.chunks,
        }
    }


@app.post("/document/new")
async def user_post_document(
    response: Response, user_id: Annotated[str, Depends(jwt_auth_user_id)], file: UploadFile, public: bool = False
):
    """
    Post document
    """

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    chunks, elapsed_s = pdf_parser.get_text(file.file)
    file.file.seek(0)
    file_content = file.file.read()
    file.file.seek(0)

    new_document = Document(
        filename=file.filename,
        submitted_at=dt.datetime.utcnow(),
        owner_id=user_id,
        hash=hashlib.sha256(file_content).digest(),
        public=public,
        chunks=chunks,
        content_size=file.size,
    )

    with Session.begin() as sess:
        sess.add(new_document)
        sess.commit()

    response.status_code = status.HTTP_201_CREATED
    return


@app.delete("/document/{document_id}")
async def user_delete_document(user_id: Annotated[str, Depends(jwt_auth_user_id)], document_id: int):
    """
    Delete document
    """

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    with Session.begin() as sess:
        readable = (
            sess.execute(select(Document).join(User).where(Document.id == document_id).where(Document.owner_id == user_id))
            .scalars()
            .one_or_none()
        )
        if readable:
            document = sess.get(Document, readable.id)
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )

        sess.delete(document)

    return
