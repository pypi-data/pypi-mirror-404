from setuptools import setup, find_packages

setup(
    name='fastapi-sqlalchemy-ease',
    version='0.1.3',
    description="A reusable SQLAlchemy extension for FastAPI",
    packages=find_packages(),
    python_requires='>=3.8',
    install_requires=[
        'sqlalchemy>=2.0.0'
    ],
) 