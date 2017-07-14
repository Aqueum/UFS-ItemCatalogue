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


# edit a category
@app.route("/categories/<int:category_id>/edit/", methods=['GET', 'POST'])
def edit_category(category_id):
    edited_category = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        if request.form['name'] == edited_category.name and request.form['description'] == edited_category.description:
            return redirect(url_for('show_categories'))
        else:
            if request.form['name']:
                edited_category.name = request.form['name']
            if request.form['description']:
                edited_category.description = request.form['description']
            session.add(edited_category)
            session.commit()
            flash('Category %s edited' % edited_category.name)
            return redirect(url_for('show_categories'))
    else:
        return render_template('editCategory.html', category=edited_category)


# delete a category
@app.route("/categories/<int:category_id>/delete/", methods=['GET', 'POST'])
def delete_category(category_id):
    deleted_category = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        session.delete(deleted_category)
        return redirect(url_for('show_categories'))
    else:
        return render_template('deleteCategory.html', category=deleted_category)

# show category page
@app.route("/categories/<int:category_id>")
def show_category(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    return render_template('category.html', category=category)

# run flask development server
if __name__ == '__main__':
    app.secret_key = 'aHr^8jH29Ne%k)puVr34Gj&wsh'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
