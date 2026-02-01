from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of your README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name='fastapi-sqlalchemy-ease',
    version='0.1.4',
    description="A reusable SQLAlchemy extension for FastAPI",
    packages=find_packages(),
    long_description=long_description,
    long_description_content_type='text/markdown',
    python_requires='>=3.8',
    install_requires=[
        'sqlalchemy>=2.0.0'
    ],
) 