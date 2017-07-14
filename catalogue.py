from flask import Flask, render_template, request, flash, redirect, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from catalogue_setup import Base, Category

# initialise flask application
app = Flask(__name__)

# connect to database & create database session
engine = create_engine('sqlite:///catalogue.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# render index.html at root
@app.route("/")
def index():
    return render_template('index.html')


@app.route("/categories/new/", methods=['GET', 'POST'])
def add_category():
    if request.method == 'POST':
        new_category = Category(name=request.form['name'],
                                description=request.form['description'])
        session.add(new_category)
        flash('New category %s added successfully' % new_category.name)
        session.commit()
        return redirect(url_for('index'))
    else:
        return render_template('newCategory.html')


# run flask development server
if __name__ == '__main__':
    app.secret_key = 'aHr^8jH29Ne%k)puVr34Gj&wsh'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
