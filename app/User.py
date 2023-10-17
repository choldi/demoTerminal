from Model import db
from sqlalchemy.orm import Mapped, mapped_column

class User(db.Model):
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    username: Mapped[str] = mapped_column(db.String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(db.String, unique=False, nullable=False)
    email: Mapped[str] = mapped_column(db.String)

