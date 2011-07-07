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


from datetime import datetime

from flask import *
from multicorn.declarative import declare, Property
from multicorn.requests import CONTEXT as c

from access_points import *


app = Flask(__name__)
#g.user_id = None
#g.user_login = "Guest"
#g.user_password = None
#g.email = None

app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'


@app.route("/", methods=("GET",))
def index():
    data =  {"snippets" : Snippet.all.execute()}
    return render_template("index.html.jinja2", **data)


@app.route("/snippet/<int:snippet_id>", methods=["GET"])
@app.route("/s/<int:snippet_id>", methods=["GET"])
def get_snippet_by_id(snippet_id):
    item = Snippet.all.filter(
        c.id == snippet_id).one(None).execute()
    if item is not None:
        data = {"snippet" : item}
        return render_template("snippet.html.jinja2", **data)
    else:
        return "ERREUR ouaaaaah",404


@app.route("/add", methods=["GET"])
def add_snippet_get():
    return render_template("add.html.jinja2")


@app.route("/add", methods=["POST"])
def add_snippet_post():
    item = Snippet.create({
        'person_id': None,
        'date': datetime.now(),
        'language': request.form['snip_language'],
        'title': request.form['snip_title'],
        'text': request.form['snip_text'],
        }).save()
    return redirect("/s/IDontKnow") #FIXME


@app.route("/modify/<int:id>", methods=["GET"])
def modify_snippet_get(id):
    #if not session.get('logged_in'):
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
                )
    else:
        return "Groaaah!", 404


@app.route("/modify/<int:id>", methods=["POST"])
def modify_snippet_post(id):
    #if not session.get('logged_in'):
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


@app.route('/connect', methods=('GET',))
def get_connect():
    return render_template('connect.html.jinja2')


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
        session['login'] = request.form['login']
        #session['logged_in'] = True
        flash("Welcome %s !" % escape(session["login"]))
        return redirect("/") #FIXME
    else:
        flash("Invalid login or password !")
        return redirect(url_for("connect"))


@app.route('/disconnect', methods=['GET'])
def disconnect():
    session.pop('login', None)
    #session.pop('logged_in', None)
    flash('You are disconnected !')
    return redirect("/") #FIXME


@app.route('/register', methods=['POST'])
def register():
    if '' == request.form.get('login', '') \
        or '' == request.form.get('password', '') \
        or '' == request.form.get('email', '') :
        flash("Empty field")
        return redirect(url_for("register"))
    else:
        person = Person.create({
            'login': request.form['login'], 
            'password': request.form['password'], 
            'email': request.form['email'],
            }).save()
        session['login'] = request.form['login']
        #session['logged_in'] = True
        flash("Welcome %s !" % escape(session["login"]))
        return redirect("/") #FIXME


@app.route('/register', methods=['GET'])
def get_register():
    return render_template('register.html.jinja2')

@app.route('/account', methods=['POST'])
def account(id):
    #if not session.get('logged_in'):
    if not session.get('login'):
        return redirect(url_for("connect"))
    item = Person.all.filter(c.id == id).one(None).execute()
    if item is not None:
        item['login'] = request.form['login']
        item['password'] = request.form['password']
        item['email'] = request.form['email']
        item.save()
    flash("Your account is been modify !")
    return redirect("/") #FIXME

@app.route('/account', methods=['GET'])
def get_account():
    return render_template('account.html.jinja2')


if __name__ == '__main__':
#    app.run()
    app.run(debug=True)

