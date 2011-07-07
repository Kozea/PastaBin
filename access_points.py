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
from multicorn.declarative import declare, Property, Relation
from multicorn.requests import CONTEXT as c
from multicorn.corns.extensers.computed import ComputedExtenser


mc = Multicorn()


@mc.register
@declare(Alchemy, identity_properties=("id",), url="sqlite:///pastabin.db")
class Person(object):
    id = Property(type=int)
    login = Property(type=unicode)
    password = Property(type=unicode)
    email = Property(type=unicode)


@mc.register
@declare(Alchemy, identity_properties=("id",), url="sqlite:///pastabin.db")
class Snippet(object):
    id = Property(type=int)
    person = Relation(Person)
    date = Property(type=datetime)
    language = Property(type=unicode)
    title = Property(type=unicode)
    text = Property(type=unicode)


if __name__ == "__main__":
    Person.create({
        'login': "Totoro",
        'password': "azerty",
        'email': "totoro@gibli.com",
        }).save()

    Snippet.create({
        'person': 1,
        'date': datetime(1988, 1, 1),
        'language': "assembly",
        'title': "hello.asm",
        'text': "org 100h\n\nmov ah, 09h\nmov dx, offset msg\nint 21h\n\nmov ah, 4Ch\nint 21h\n\nmsg db \"Groaaah!\"",
        }).save()


