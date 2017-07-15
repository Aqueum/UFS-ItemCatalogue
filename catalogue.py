from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from catalogue_setup import Base, Category, Item

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


@app.route("/categories/JSON/")
def show_categories_json():
    categories = session.query(Category).order_by(asc(Category.name))
    return jsonify(categories=[c.serialise for c in categories])


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


# show category page and its item list
@app.route("/categories/<int:category_id>")
def show_category(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).order_by(asc(Item.name))
    return render_template('category.html', category=category, items=items)


@app.route("/categories/<int:category_id>/JSON/")
def show_categories_json(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).order_by(asc(Item.name))
    return jsonify(category=category.serialise, items=[i.serialise for i in items])


# add an item
@app.route("/<int:category_id>/new_item/", methods=['GET', 'POST'])
def add_item(category_id):
    if request.method == 'POST':
        new_item = Item(name=request.form['name'],
                        description=request.form['description'],
                        image=request.form['image'],
                        category_id=category_id)
        session.add(new_item)
        flash('New item %s added successfully' % new_item.name)
        session.commit()
        return redirect(url_for('show_category', category_id=category_id))
    else:
        return render_template('newItem.html')


# edit an item
@app.route("/categories/<int:category_id>/<int:item_id>/edit/", methods=['GET', 'POST'])
def edit_item(category_id, item_id):
    category = session.query(Category).filter_by(id=category_id).one()
    edited_item = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        if request.form['name'] == edited_item.name and request.form[
                'description'] == edited_item.description and request.form[
                'image'] == edited_item.image:
            return redirect(url_for('show_category', category_id=category_id))
        else:
            if request.form['name']:
                edited_item.name = request.form['name']
            if request.form['description']:
                edited_item.description = request.form['description']
            if request.form['image']:
                edited_item.image = request.form['image']
            session.add(edited_item)
            session.commit()
            flash('Item %s edited' % edited_item.name)
            return redirect(url_for('show_category', category_id=category_id))
    else:
        return render_template('editItem.html', category=category, item=edited_item)


# delete an item
@app.route("/categories/<int:category_id>/<int:item_id>/delete/", methods=['GET', 'POST'])
def delete_item(category_id, item_id):
    category = session.query(Category).filter_by(id=category_id).one()
    deleted_item = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        session.delete(deleted_item)
        return redirect(url_for('show_category', category_id=category_id))
    else:
        return render_template('deleteItem.html', category=category, item=deleted_item)


# show item page
@app.route("/categories/<int:category_id>/<int:item_id>")
def show_item(category_id, item_id):
    category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(Item).filter_by(id=item_id).one()
    return render_template('item.html', category=category, item=item)


@app.route("/categories/<int:category_id>/<int:item_id>/JSON/")
def show_item_json(category_id, item_id):
    category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(category=category.name, item=item.serialise)


# run flask development server
if __name__ == '__main__':
    app.secret_key = 'aHr^8jH29Ne%k)puVr34Gj&wsh'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
