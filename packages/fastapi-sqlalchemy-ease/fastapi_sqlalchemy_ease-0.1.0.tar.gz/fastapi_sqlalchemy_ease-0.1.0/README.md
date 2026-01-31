# fastapi-sqlalchemy
A reusable SQLAlchemy extension for FastAPI.

## Installation
```bash
pip install fastapi-sqlalchemy
```

## Usage
```python
from fastapi_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
DATABASE_URI = "sqlite:///site.db"
db.init_app(DATABASE_URI)
```