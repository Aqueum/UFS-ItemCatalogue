from flask import Flask, render_template, request, flash, redirect, url_for
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from catalogue_setup import Base, Category

# initialise flask application
app = Flask(__name__)

# connect to database & create database session
engine = create_engine('sqlite:///catalogue.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# show list of categories
@app.route("/")
@app.route("/categories/")
def show_categories():
    categories = session.query(Category).order_by(asc(Category.name))
    return render_template('categories.html', categories=categories)


# add a category
@app.route("/categories/new/", methods=['GET', 'POST'])
def add_category():
    if request.method == 'POST':
        new_category = Category(name=request.form['name'],
                                description=request.form['description'])
        session.add(new_category)
        flash('New category %s added successfully' % new_category.name)
        session.commit()
        return redirect(url_for('show_categories'))
    else:
        return render_template('newCategory.html')


# show list of categories
@app.route("/categories/<int:category_id>")
def show_category(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    return render_template('category.html', category=category)

# run flask development server
if __name__ == '__main__':
    app.secret_key = 'aHr^8jH29Ne%k)puVr34Gj&wsh'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
