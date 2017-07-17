# UFS-ItemCatalogue
- Udacity Full Stack - Item Catalogue
- [Udacity Full Stack Web Developer Nanodegree](
https://www.udacity.com/course/full-stack-web-developer-nanodegree--nd004)
- Martin Currie (Aqueum) - 13 July 2017

# Purpose & design
An application that provides a list of items within a variety of categories. 
Registered users have the ability to post, edit and delete their own items.

# Getting Started
## install software
1. Install [virtual box](https://www.virtualbox.org/)
2. Install [vagrant](https://www.vagrantup.com/downloads.html)
3. Clone [this repo](https://github.com/Aqueum/UFS-ItemCatalogue) to your local machine
## Get Google OAuth2 Credentials
4. Go to the [Google developer console API site](https://console.developers.google.com/apis)
5. Navagate through Credentials > Create Credentials > OAuth Client ID > Web application, 
6. Name your application `UFS-IC', 
7. Add http://localhost:8000 as an Authorised JavaScript origin 
8. Add http://localhost:8000/gconnect as Authorised redirect URI, and click create
9. In the UFS-IC credentials click download json and save the file as `client_secrets.json` in the root of your repo clone
## Start the server
10. Navigate to your repo clone in terminal (or your command line)
11. Enter `vagrant up`
12. Enter `vagrant ssh`
## Launch the database
13. Enter `python /vagrant/catalogue/application.py`
14. Access [localhost port 8000](http://localhost:8000) in your browser

# Known issues
## Not pretty
Given that this is a database project, I didn't spend too long on the aesthetics.  It may not be as pretty as the Project Display Example, & doesn't have a latest items display (not mentioned in the rubric) but it does include cute images.

# Files
## catalogue_setup.py
SQLAlchemy file that sets up the database.

## catalogue.db
An SQLite database automatically generated by catalogue_setup.py
and populated by the web-app / API.

## application.py
The python flask server that runs the application

## templates & styles
including:
- categories.html
- category.html
- deleteCategory.html
- deleteItem.html
- editCategory.html
- editItem.html
- header.html
- item.html
- login.html
- main.html
- newCategory.html
- newItem.html
most of which are rendered as required by application.py
and static/styles/style.css which styles the above

## Vagrantfile
Vagrant recipe to set up the server & software to run the above - taken from [fullstack-nanodegree-vm](https://github.com/udacity/fullstack-nanodegree-vm/blob/master/vagrant/Vagrantfile)

# Contributing
This is an assessed project, so I'd probably get in trouble for accepting external input.

# Code Status
Can Udacity add a badge here..?

# License
This is an assessed project, but also may be further developed to help a local community interest company,
as such **all rights are reserved**, feel free to [contact me](http://www.aqueum.com/contact/)
if you have any questions.