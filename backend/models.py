from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    color = Column(String, default="#0A3D62")

    datasets = relationship(
        "Dataset",
        back_populates="client",
        cascade="all, delete-orphan"
    )


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    file_name = Column(String, nullable=False)
    uploaded_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    client = relationship(
        "Client",
        back_populates="datasets"
    )
