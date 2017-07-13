from sqlalchemy import Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()


class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    description = Column(String)


class Item(Base):
    __tablename__ = 'item'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    description = Column(String)
    image = Column(String)
    category_id = Column(Integer, ForeignKey('restaurant.id'))
    relationship = relationship(Category)


engine = create_engine('sqlite:///catalogue.db')

Base.metadata.create_all(engine)
