from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from catalogue_setup import Base, Category, Item, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Category Menu Application"


# Connect to Database and create database session
engine = create_engine('sqlite:///catalogue.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


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

    # The token must be stored in the login_session in order to properly logout, let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

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


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON APIs to view Category Information
@app.route('/restaurant/<int:restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
    restaurant = session.query(Category).filter_by(id=restaurant_id).one()
    items = session.query(Item).filter_by(
        restaurant_id=restaurant_id).all()
    return jsonify(Items=[i.serialize for i in items])


@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def menuItemJSON(restaurant_id, menu_id):
    Menu_Item = session.query(Item).filter_by(id=menu_id).one()
    return jsonify(Menu_Item=Menu_Item.serialize)


@app.route('/restaurant/JSON')
def restaurantsJSON():
    restaurants = session.query(Category).all()
    return jsonify(restaurants=[r.serialize for r in restaurants])


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


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
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
    else:
        flash("You were not logged in")
        return redirect(url_for('show_categories'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)