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


@app.route("/modify/<int:id>", methods=("GET", "POST"))
def modify_snippet(id):
    if request.method == "POST":
        item = Snippet.all.filter(c.id == id).one(None).execute()
        if item is not None:
            item['date'] = datetime.now()
            item['language'] = request.form['snip_language']
            item['title'] = request.form['snip_title']
            item['text'] = request.form['snip_text']
            item.save()
        return redirect("/") #FIXME
    else:
        try:
            item = Snippet.all.filter(c.id == id).one(None).execute()
        except:
            return "Ouch"
        if item is not None:
            return render_template(
                    "modify.html.jinja2",
                    snip_id=item['id'],
                    snip_title=item['title'],
                    snip_language=item['language'],
                    snip_text=item['text'],
                    )
        else:
            return "None" #FIXME


if __name__ == '__main__':
    app.run()
#    app.run(debug=True)


