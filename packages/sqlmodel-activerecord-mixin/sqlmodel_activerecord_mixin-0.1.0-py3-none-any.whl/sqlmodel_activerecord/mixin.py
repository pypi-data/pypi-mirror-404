from flask_sqlalchemy import SQLAlchemy
from sqlmodel import SQLModel

db = SQLAlchemy(metadata=SQLModel.metadata)


class _QueryDescriptor:
    """Descriptor so Model.query returns db.session.query(Model)."""

    def __get__(self, obj, owner):
        return db.session.query(owner)


class ActiveRecordMixin:
    """
    A mixin to add Active Record style convenience methods
    (Model.query, save, delete) to SQLModel classes.
    """
    query = _QueryDescriptor()

    def save(self):
        """Convenience method to add and commit the current object."""
        db.session.add(self)
        db.session.commit()
        db.session.refresh(self)
        return self

    def delete(self):
        """Convenience method to delete and commit the current object."""
        db.session.delete(self)
        db.session.commit()
