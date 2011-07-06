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

from multicorn import Multicorn
from multicorn.corns.alchemy import Alchemy
from multicorn.declarative import declare, Property
from multicorn.requests import CONTEXT as c
from multicorn.corns.extensers.computed import ComputedExtenser


mc = Multicorn()


@mc.register #FIXME
@declare(Alchemy, identity_properties=("id",), url="sqlite:///")
class Person(object): #FIXME RawPerson
    id = Property(type=int)
    login = Property(type=unicode)
    password = Property(type=unicode)
    email = Property(type=unicode)


@mc.register #FIXME
@declare(Alchemy, identity_properties=("id",), url="sqlite:///")
class Snippet(object): #FIXME RawSnippet
    id = Property(type=int)
    person_id = Property(type=int)
    date = Property(type=datetime)
    language = Property(type=unicode)
    title = Property(type=unicode)
    text = Property(type=unicode)


#FIXME
#Person = ComputedExtenser("Person", RawPerson)
#Snippet = ComputedExtenser("Snippet", RawSnippet)
#Person.register("snippets", Snippet.all.filter(c(-1).id == c.person_id))
#Snippet.register("person", Person.all.filter(c(-1).person_id == c.id))


Person.create({ #FIXME
    'login': "Kikoo",
    'password': "azertyuiop",
    'email': "kikoo@lol.com",
    }).save()

Person.create({ #FIXME
    'login': "Foobar",
    'password': ":p",
    'email': "foo@bar.com",
    }).save()

Snippet.create({ #FIXME
    'person_id': 2,
    'date': datetime(1942, 7, 14),
    'language': "python",
    'title': "hello.py",
    'text': "#!/usr/bin/python\n\nprint('Hello World!')\n",
    }).save()


if __name__ == "__main__":
    print(" | %4s | %-15s | %-15s | %-25s | " % ("id", "login", "password", "email"))
    for item in Person.all.execute():
        print(" | %4i | %-15s | %-15s | %-25s | " % (item['id'], item['login'], item['password'], item['email']))

    print("\n\n")

    print(" | %4s | %-15s | %-15s | %-15s | %-15s | " % ("id", "person_id.login", "language", "title", "date"))
    for item in Snippet.all.execute():
        #print(" | %4i | %-15s | %-15s | %-15s | %-15s | " % (item['id'], item['person']['login'], item['language'], item['title'], str(item['date'])))
        print(" | %4i | %-15i | %-15s | %-15s | %-15s | " % (item['id'], item['person_id'], item['language'], item['title'], str(item['date'])))



