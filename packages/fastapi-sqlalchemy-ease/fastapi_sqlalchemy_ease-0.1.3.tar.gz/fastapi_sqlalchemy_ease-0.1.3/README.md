# fastapi-sqlalchemy-ease
A reusable SQLAlchemy extension for FastAPI.

## Installation
```bash
pip install fastapi-sqlalchemy-ease
```

## Usage
```python
from fastapi_sqlalchemy_ease import SQLAlchemy

db = SQLAlchemy()
DATABASE_URI = "sqlite:///site.db"
db.init_app(DATABASE_URI)
```