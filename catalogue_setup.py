from sqlalchemy import Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


# construct a base class for declarative class definitions
Base = declarative_base()


# build the category table
class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    description = Column(String(1024))

    @property
    def serialise(self):
        return {
            'name': self.name,
            'id': self.id,
            'description': self.description,
        }


# build the item table
class Item(Base):
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    description = Column(String(1024))
    image = Column(String(128))
    # establish relationship between item and category tables
    category_id = Column(Integer, ForeignKey('category.id'))
    relationship = relationship(Category)

    @property
    def serialise(self):
        return {
            'name': self.name,
            'id': self.id,
            'description': self.description,
            'image': self.image,
        }


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

    @property
    def serialise(self):
        return {
            'name': self.name,
            'id': self.id,
            'email': self.email,
            'picture': self.picture,
        }

# Create the database engine and database
engine = create_engine('sqlite:///catalogue.db')
Base.metadata.create_all(engine)
