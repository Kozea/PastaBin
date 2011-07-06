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
from multicorn.requests import CONTEXT as c


app = Flask(__name__)
#g.user_id = None
#g.user_login = "Guest"
#g.user_password = None
#g.email = None

app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'


@app.route("/add", methods=("GET", "POST"))
def add_snippet():
    if request.method == "POST":
        item = Snippet.create({
            'person_id': None,
            'date': datetime.now(),
            'language': request.form['snip_language'],
            'title': request.form['snip_title'],
            'text': request.form['snip_text'],
            }).save()
        return redirect("/s/IDontKnow") #FIXME
    else:
        return render_template("add.html.jinja2")

@app.route("/", methods=("GET",))
def index():
    data =  {"snippets" : Snippet.all.execute()}
    return render_template("index.html.jinja2", **data)


@app.route("/snippet/<int:snippet_id>", methods=("GET",))
def get_snippet_by_id(snippet_id):
    item = Snippet.all.filter(
        c.id == snippet_id).one().execute()
    data = {"snippet" : item}
    return render_template("snippet.html.jinja2", **data)


@app.route('/connect', methods=['POST',])
def connect():
    item = Person.all.filter(
        c.login == request.form['login']).one(None)
    item = item.execute()
    if '' == request.form.get('login', '') \
        or '' == request.form.get('password', ''):
            flash("Empty field !")
            return redirect(url_for("connect"))
    if item['password'] == request.form['password']:
        session['logged_in'] = True
        flash("You are connected !")
        return redirect("/") #FIXME
    else:
        flash("Invalid login or password !")
        return redirect(url_for("connect"))


@app.route('/connect', methods=('GET',))
def get_connect():
    return render_template('connect.html.jinja2')


@app.route('/disconnect')
def disconnect():
    session.pop('logged_in', None)
    flash('You are disconnected !')
    return redirect("/") #FIXME


@app.route("/modify/<int:id>", methods=("GET", "POST"))
def modify_snippet(id):
    if not session.get('logged_in'):
        return redirect(url_for("connect"))
    if request.method == "POST":
        item = Snippet.all.filter(c.id == id).one(None).execute()
        if item is not None:
            item['date'] = datetime.now()
            item['language'] = request.form['snip_language']
            item['title'] = request.form['snip_title']
            item['text'] = request.form['snip_text']
            item.save()
        return redirect(url_for("get_snippet_by_id", snippet_id=item['id']))
    else:
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
            return "Groaaah!",404

@app.route('/register', methods=('POST',))
def register():
    if '' == request.form.get('login', '') \
        or '' == request.form.get('password', '') \
        or '' == request.form.get('email', '') :
        return 'BAD'
    else:
        Person.create({
            'login': request.form['login'], 
            'password': request.form['password'], 
            'email': request.form['email'],
            }).save()
        return 'REGISTER'

@app.route('/register', methods=('GET',))
def get_register():
    return render_template('register.html.jinja2')

if __name__ == '__main__':
    app.run()
#    app.run(debug=True)

