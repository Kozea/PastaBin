#!/usr/bin/python
# -*- coding: utf-8 -*-

   ###########################################################################
 ##                 _____           _         _     _                       ##
##                 |  __ \         | |       | |   (_)                      ##
##                 | |__) |__ _ ___| |_  __ _| |__  _ _ __                  ##
##                 |  ___// _` / __| __|/ _` | '_ \| | '_ \                 ##
##                 | |   | (_| \__ \ |_| (_| | |_) | | | | |                ##
##                 |_|    \__,_|___/\__|\__,_|_.__/|_|_| |_|                ##
##                                                                          ##
##                        --  http://pastabin.org/  --                      ##
##                                                                          ##
##                                                                          ##
## Pastabin - A pastebin with a lot of taste                                ##
##                                                                          ##
## Copyright (C) 2011  Kozea                                                ##
##                                                                          ##
## This program is free software: you can redistribute it and/or modify     ##
## it under the terms of the GNU Affero General Public License as published ##
## by the Free Software Foundation, either version 3 of the License, or     ##
## (at your option) any later version.                                      ##
##                                                                          ##
## This program is distributed in the hope that it will be useful,          ##
## but WITHOUT ANY WARRANTY; without even the implied warranty of           ##
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            ##
## GNU Affero General Public License for more details.                      ##
##                                                                          ##
## You should have received a copy of the GNU Affero General Public License ##
## along with this program.  If not, see <http://www.gnu.org/licenses/>.    ##
##                                                                          ##
##                                                                          ##
## Authored by: Amardine DAVID <amardine.david@kozea.fr>                    ##
## Authored by: Jérôme DEROCK <jerome.derock@kozea.fr>                      ##
## Authored by: Fabien LOISON <fabien.loison@kozea.fr>                      ##
##                                                                         ##
###########################################################################


__app_name__ = "PastaBin"
__version__ = "0.1"


from datetime import datetime

from flask import *
from multicorn.declarative import declare, Property
from multicorn.requests import CONTEXT as c

from access_points import *


app = Flask(__name__)

app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'


def get_page_informations(title="Unknown", menu_active=None):
    """Retun various informations like the menu, the page title,...

    Arguments:
        title -- The page title
        menu_active -- The name of the current page
    """
    menu_items = [
            {
                'name': "index",
                'title': "Home",
                'url': url_for("index"),
                'active': False,
            },
            {
                'name': "add",
                'title': "New snippet",
                'url': url_for("add_snippet_get"),
                'active': False,
            },
            ]
    if session.get("login", False):
        menu_items.append({
            'name': "my_snippets",
            'title': "My snippets",
            'url': url_for("my_snippets"),
            'active': False,
            })
    for item in menu_items:
        if menu_active == item['name']:
            item['active'] = True
            break
    return {
            'menu': menu_items,
            'title': title,
            'appname': __app_name__,
            }


def get_user_id():
    """Return the user id if logged, 0 else"""
    return session.get("id", 0)


def get_user_login():
    """Return the user login if logged, Guest else"""
    return session.get("login", "Guest")


@app.route("/", methods=["GET"])
def index():
    return render_template(
            "index.html.jinja2",
            snippets=Snippet.all.sort(-c.id)[:10].execute(),
            page=get_page_informations(title="Home"),
            )


@app.route("/snippet/<int:snippet_id>", methods=["GET"])
@app.route("/s/<int:snippet_id>", methods=["GET"])
def get_snippet_by_id(snippet_id):
    item = Snippet.all.filter(c.id == snippet_id).one(None).execute()
    if item is not None:
        return render_template(
                "snippet.html.jinja2",
                snippet=item,
                page=get_page_informations(title=item['title']),
                )
    else:
        return "ERROR ouaaaaah", 404 #FIXME


@app.route("/my_snippets", methods=["GET"])
def my_snippets():
    item = Snippet.all.filter(c.id == session['id']).execute()
    return render_template(
            "my_snippets.html.jinja2",
            snippets=item,
            page=get_page_informations(
                title="My snippets",
                menu_active="my_snippets",
                ),
            )


@app.route("/add", methods=["GET"])
def add_snippet_get():
    return render_template(
            "add.html.jinja2",
            page=get_page_informations(
                title="Add a new Snippet",
                menu_active="add"
                ),
            )


@app.route("/add", methods=["POST"])
def add_snippet_post():
    item = Snippet.create({
        'person': get_user_id(),
        'date': datetime.now(),
        'language': request.form['snip_language'],
        'title': request.form['snip_title'],
        'text': request.form['snip_text'],
        })
    item.save()
    return redirect(url_for("get_snippet_by_id", snippet_id=item['id']))


@app.route("/modify/<int:id>", methods=["GET"])
def modify_snippet_get(id):
    if not session.get('login'):
        return redirect(url_for("connect"))
    item = Snippet.all.filter(c.id == id).one(None).execute()
    if item is not None:
        return render_template(
                "modify.html.jinja2",
                snip_id=item['id'],
                snip_title=item['title'],
                snip_language=item['language'],
                snip_text=item['text'],
                page=get_page_informations(
                    title="Modify a snippet (%s)" % item['title'])
                )
    else:
        return "Groaaah!", 404 #FIXME


@app.route("/modify/<int:id>", methods=["POST"])
def modify_snippet_post(id):
    if not session.get('login'):
        return redirect(url_for("connect"))
    item = Snippet.all.filter(c.id == id).one(None).execute()
    if item is not None:
        item['date'] = datetime.now()
        item['language'] = request.form['snip_language']
        item['title'] = request.form['snip_title']
        item['text'] = request.form['snip_text']
        item.save()
    return redirect(url_for("get_snippet_by_id", snippet_id=item['id']))


@app.route("/delete/<int:id>", methods=["GET"])
def delete_snippet_get(id):
    if not session.get('logged_in'):
        return redirect(url_for("connect"))
    item = Snippet.all.filter(c.id == id).one(None).execute()
    if item is not None:
        return render_template(
                "delete.html.jinja2",
                snip_id=id,
                snip_title=item['title'],
                page=get_page_informations(title="Delete a snippet"),
                )
    else:
        return "Groaaah!", 404 #FIXME


@app.route("/delete/<int:id>", methods=["POST"])
def delete_snippet_post(id):
    if not session.get('logged_in'):
        return redirect(url_for("connect"))
    item = Snippet.all.filter(c.id == id).one(None).execute()
    if item is not None:
        item.delete()
        return redirect(url_for("index"))
    else:
        return "Groaaah!", 404 #FIXME


@app.route('/connect', methods=('GET',))
def get_connect():
    return render_template(
            'connect.html.jinja2',
            page=get_page_informations(title="Connexion"),
            )


@app.route('/connect', methods=['POST'])
def connect():
    item = Person.all.filter(
        c.login.lower() == request.form['login'].lower()).one(None)
    item = item.execute()
    if '' == request.form.get('login', '') \
        or '' == request.form.get('password', ''):
            flash("Empty field !")
            return redirect(url_for("connect"))
    if item['password'] == request.form['password']:
        session['login'] = item['login']
        session['id'] = item['id']
        flash("Welcome %s !" % escape(session["login"]), "ok")
        return redirect(url_for("index"))
    else:
        flash("Invalid login or password !")
        return redirect(url_for("connect"))


@app.route('/disconnect', methods=['GET'])
def disconnect():
    session.pop('login', None)
    flash('You are disconnected !')
    return redirect(url_for("index"))


@app.route('/register', methods=['GET'])
def get_register():
    return render_template(
            'register.html.jinja2',
            page=get_page_informations(title="Register"),
            )


@app.route('/register', methods=['POST'])
def register():
    if '' == request.form.get('login', '') \
        or '' == request.form.get('password1', '') \
        or '' == request.form.get('password2', '') \
        or '' == request.form.get('email', '') :
        flash("Some fields are empty !")
        return redirect(url_for("register"))
    if request.form['password1'] != request.form['password2']:
        flash("Passwords are not same !")
        return redirect(url_for("register"))
    person = Person.create({
        'login': request.form['login'], 
        'password': request.form['password2'], 
        'email': request.form['email'],
        })
    person.save()
    session['login'] = person['login']
    session['id'] = person['id']
    flash("Welcome %s !" % escape(session["login"]), "ok")
    return redirect(url_for("index"))


@app.route('/account', methods=['POST'])
def account():
    if not session.get("id"):
        return redirect(url_for("connect"))
    item = Person.all.filter(c.id == session["id"]).one(None).execute()
    if request.form["password1"] != request.form["password2"]:
        flash("Passwords are not same !")
        return redirect(url_for("account"))
    if item is not None:
        item["login"] = request.form["login"]
        item["password"] = request.form["password1"]
        item["email"] = request.form["email"]
        item.save()
        session["login"] = request.form["login"]
        flash("Your account is been modify !")
    return redirect(url_for("index"))


@app.route('/account', methods=['GET'])
def get_account():
    item = Person.all.filter(c.id == session['id']).one(None).execute()
    return render_template(
            'account.html.jinja2',
            page=get_page_informations(title="Manage my account"),
            person=item
            )


if __name__ == '__main__':
#    app.run()
    app.run(debug=True)

