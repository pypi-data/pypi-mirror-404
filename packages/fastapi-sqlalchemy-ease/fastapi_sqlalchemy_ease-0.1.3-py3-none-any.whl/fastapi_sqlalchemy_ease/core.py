from sqlalchemy import (
    create_engine,
    Column, Integer, String, Text, Float, Boolean, 
    Date, DateTime, Time,
    JSON, LargeBinary, 
    Numeric,
    ForeignKey,
    UniqueConstraint, CheckConstraint,
    Index, Table
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from typing import Generator, Optional
from .exceptions import DatabaseNotInitializedError


class SQLAlchemy:
    # Singleton - ensures only one instance exists in the app
    _instance = None

    # All sqlalchemy types as class attributes
    '''Data types'''
    Column = Column
    String = String
    Integer = Integer
    Float = Float
    Boolean = Boolean
    Text = Text
    Date = Date
    DateTime = DateTime
    Time = Time
    JSON = JSON
    LargeBinary = LargeBinary
    Numeric = Numeric

    '''Relationships and Constraints'''
    ForeignKey = ForeignKey
    UniqueConstraint = UniqueConstraint
    CheckConstraint = CheckConstraint
    Index = Index
    Table = Table
    relationship = relationship

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    

    def __init__(self):
        # Everything starts as None Until db.init_app() is called
        self.engine = None
        self._SessionLocal = None
        self._Model = None
        self._initialized = False


    def init_app(self, DATABASE_URI: str, connect_args: Optional[dict]=None):
        '''
        Docstring for init_app
        
        used to Initialized database.

        DATABASE_URI: database url, type : string
        connect_args: used only when initializing sqlite db
        '''

        engine_kwargs={}

        if connect_args:
            engine_kwargs['connect_args'] = connect_args # sqlite need this
        else:
            engine_kwargs['pool_pre_ping'] = True # Keeps connection alive for PostgreSQL/MySQL

        # Engine connection to database
        self.engine = create_engine(DATABASE_URI, **engine_kwargs)

        # SessionLocal - Factory data creates new sessions
        self._SessionLocal = sessionmaker(autoflush=False ,bind=self.engine)

        # Model - base class, all our database models will inherit from
        self._Model = declarative_base()

        self._initialized = True


    @property
    def Model(self):
        '''
        Docstring for Model
        
        Base class for creating database models
        User writes: class User(db.Model):
        '''

        if not self._initialized:
            raise DatabaseNotInitializedError('Database not Intialized, call db.init_app() first.')
        
        return self._Model
    

    def create_all(self):
        '''
        Docstring for create_all
        
        create all tables in the database
        '''

        if not self._initialized:
            raise DatabaseNotInitializedError('Database not Intialized, call db.init_app() first.')
        
        self._Model.metadata.create_all(self.engine)


    def drop_all(self):
        '''
        Docstring for drop_all
        
        delete all tables from the database.
        '''
        if not self._initialized:
            raise DatabaseNotInitializedError('Database not Intialized, call db.init_app() first.')

        self._Model.metadata.drop_all(self.engine)


    def Session(self) -> Generator[Session, None, None]:
        '''
        Docstring for Session
        
        creates a new session per request.
        must use with Depends in FastAPI().
        Auto closes sessions after request is done.

        '''

        if not self._initialized:
            raise DatabaseNotInitializedError('Database not Intialized, call db.init_app() first.')
            
        session = self._SessionLocal()
        try:
            yield session # Give session to the route
        finally:
            session.close() #always close after one requst