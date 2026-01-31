# sqlmodel-activerecord-mixin

Active Record–style convenience methods for [SQLModel](https://sqlmodel.tiangolo.com/) when using [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/): `Model.query`, `.save()`, and `.delete()`.

## Install

```bash
pip install sqlmodel-activerecord-mixin
```

## Usage

1. Create a Flask app and init Flask-SQLAlchemy with SQLModel metadata (this package exposes the same `db` instance):

```python
from flask import Flask
from sqlmodel_activerecord import db

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
db.init_app(app)
```

2. Define models by inheriting from SQLModel, this mixin, and set `table=True`:

```python
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlmodel_activerecord import ActiveRecordMixin

class Hero(SQLModel, ActiveRecordMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    secret_name: str
```

3. Use Active Record–style APIs (inside a Flask request or `app.app_context()`):

```python
# Create and save
hero = Hero(name="Iron Man", secret_name="Tony Stark")
hero.save()

# Query
Hero.query.all()
Hero.query.get(1)
Hero.query.filter_by(name="Iron Man").first()
Hero.query.count()

# Update (mutate then save)
hero.age = 50
hero.save()

# Delete
hero.delete()
```

## Requirements

- Python >= 3.9
- Flask, Flask-SQLAlchemy, SQLModel

## Development

```bash
pip install -e .
python usage_test.py   # run module tests
```

## License

MIT
