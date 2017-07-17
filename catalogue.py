from flask import Flask, render_template, request, flash, redirect, url_for, jsonify, make_response
from flask import session as login_session
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from catalogue_setup import Base, Category, Item, User
import random
import string
import json
import httplib2

# initialise flask application
app = Flask(__name__)

# connect to database & create database session
engine = create_engine('sqlite:///catalogue.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# launch login page after generating anti-forgery state token
@app.route("/login/")
def login_page():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(32))
    login_session['state'] = state
    return render_template('fbLogin.html', STATE=state)


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/v2.4/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    # Extract the access token from response
    token = 'access_token=' + data['access_token']

    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout,
    # let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = get_user_id(login_session['email'])
    if not user_id:
        user_id = create_user(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;'
    output += '-webkit-border-radius: 150px;-moz-border-radius: 150px;">'

    flash("Now logged in as %s" % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


def create_user(auth_session):
    new_user = User(name=auth_session['username'], email=auth_session[
                   'email'], picture=auth_session['picture'])
    session.add(new_user)
    session.commit()
    user = session.query(User).filter_by(email=auth_session['email']).one()
    return user.id


def get_user_info(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def get_user_id(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except Exception as e:
        print e
        return None


# show list of categories
@app.route("/")
@app.route("/categories/")
def show_categories():
    categories = session.query(Category).order_by(asc(Category.name))
    loggedin = 'username' in login_session
    return render_template('categories.html', categories=categories, loggedin=loggedin)


@app.route("/categories/JSON/")
def show_categories_json():
    categories = session.query(Category).order_by(asc(Category.name))
    return jsonify(categories=[c.serialise for c in categories])


# add a category
@app.route("/categories/new/", methods=['GET', 'POST'])
def add_category():
    if 'username' in login_session:
        if request.method == 'POST':
            new_category = Category(name=request.form['name'],
                                    description=request.form['description'])
            session.add(new_category)
            flash('New category %s added successfully' % new_category.name)
            session.commit()
            return redirect(url_for('show_categories'))
        else:
            return render_template('newCategory.html')
    else:
        return redirect(url_for('login_page'))


# edit a category
@app.route("/categories/<int:category_id>/edit/", methods=['GET', 'POST'])
def edit_category(category_id):
    if 'username' in login_session:
        edited_category = session.query(Category).filter_by(id=category_id).one()
        if request.method == 'POST':
            if request.form['name'] == edited_category.name \
                    and request.form['description'] == edited_category.description:
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
    else:
        return redirect(url_for('login_page'))


# delete a category
@app.route("/categories/<int:category_id>/delete/", methods=['GET', 'POST'])
def delete_category(category_id):
    if 'username' in login_session:
        deleted_category = session.query(Category).filter_by(id=category_id).one()
        if request.method == 'POST':
            session.delete(deleted_category)
            return redirect(url_for('show_categories'))
        else:
            return render_template('deleteCategory.html', category=deleted_category)
    else:
        return redirect(url_for('login_page'))


# show category page and its item list
@app.route("/categories/<int:category_id>")
def show_category(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).order_by(asc(Item.name))
    loggedin = 'username' in login_session
    return render_template('category.html', category=category, items=items, loggedin=loggedin)


@app.route("/categories/<int:category_id>/JSON/")
def show_categories_json(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).order_by(asc(Item.name))
    return jsonify(category=category.serialise, items=[i.serialise for i in items])


# add an item
@app.route("/<int:category_id>/new_item/", methods=['GET', 'POST'])
def add_item(category_id):
    if 'username' in login_session:
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
    else:
        return redirect(url_for('login_page'))


# edit an item
@app.route("/categories/<int:category_id>/<int:item_id>/edit/", methods=['GET', 'POST'])
def edit_item(category_id, item_id):
    if 'username' in login_session:
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
    else:
        return redirect(url_for('login_page'))


# delete an item
@app.route("/categories/<int:category_id>/<int:item_id>/delete/", methods=['GET', 'POST'])
def delete_item(category_id, item_id):
    if 'username' in login_session:
        category = session.query(Category).filter_by(id=category_id).one()
        deleted_item = session.query(Item).filter_by(id=item_id).one()
        if request.method == 'POST':
            session.delete(deleted_item)
            return redirect(url_for('show_category', category_id=category_id))
        else:
            return render_template('deleteItem.html', category=category, item=deleted_item)
    else:
        return redirect(url_for('login_page'))


# show item page
@app.route("/categories/<int:category_id>/<int:item_id>")
def show_item(category_id, item_id):
    category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(Item).filter_by(id=item_id).one()
    loggedin = 'username' in login_session
    return render_template('item.html', category=category, item=item, loggedin=loggedin)


@app.route("/categories/<int:category_id>/<int:item_id>/JSON/")
def show_item_json(category_id, item_id):
    category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(category=category.name, item=item.serialise)

# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        # if login_session['provider'] == 'google':
        #     gdisconnect()
        #     del login_session['gplus_id']
        #     del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('show_categories'))

# run flask development server
if __name__ == '__main__':
    app.secret_key = 'aHr^8jH29Ne%k)puVr34Gj&wsh'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
