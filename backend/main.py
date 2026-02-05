from fastapi import FastAPI, File, UploadFile, Form, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Client, Dataset
import shutil, os

app = FastAPI()

UPLOAD_DIR = "../uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/register/")
def register_client(
    name: str = Form(...),
    email: str = Form(...),
    password_hash: str = Form(...),
    color: str = Form("#0A3D62"),
    db: Session = Depends(get_db)
):
    client = Client(
        name=name,
        email=email,
        password_hash=password_hash,
        color=color
    )
    db.add(client)
    db.commit()
    db.refresh(client)

    return {
        "status": "registered",
        "client_id": client.id
    }

@app.post("/upload/")
def upload_dataset(
    client_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    path = os.path.join(UPLOAD_DIR, file.filename)

    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    dataset = Dataset(
        client_id=client_id,
        file_name=file.filename
    )
    db.add(dataset)
    db.commit()

    return {
        "status": "uploaded",
        "file": file.filename
    }
