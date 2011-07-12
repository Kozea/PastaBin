#!/usr/bin/env python
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


"""
PastaBin is a free web application allowing users to pasting text and source
code (called snippet). The syntax of the snippets are automatically colorized
in order to make them more readable.

No registration is required for posting snippets, but registered users can
list, modify and delete their own snippets.

Have fun with PastaBin!
"""

__app_name__ = 'PastaBin'
__version__ = '1.0'


CONFIG = {
        'secret_key': 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT',
        'email_smtp_server': 'localhost',
        'email_smtp_port': 25,
        'email_from_addr': 'no-reply@domaine.com',
        'email_subject': '[%s] New Password' % __app_name__,
        'color_keyword': '#b58900',
        'color_name': '#cb4b16',
        'color_comment': '#839496',
        'color_string': '#2aa198',
        'color_error': '#dc322f',
        'color_number': '#859900'}


import random
import smtplib
import json
from os.path import isfile, join as pathjoin
from os import environ
from datetime import datetime
from hashlib import sha256
from functools import wraps
from email.mime.text import MIMEText
from socket import error as socketerror

from flask import (Flask, url_for, render_template, redirect, abort,
        flash, session, request)
from pygments import highlight
from pygments.util import ClassNotFound as LexerNotFound
from pygments.formatters import HtmlFormatter
from pygments.lexers import (get_all_lexers, get_lexer_by_name,
        get_lexer_for_filename, guess_lexer)
from pygments.style import Style
from pygments.token import Keyword, Name, Comment, String, Error, Number
from multicorn.requests import CONTEXT as c

from access_points import Person, Snippet


def read_config():
    """Search the configuration file and read it."""
    #Search the configuration file
    search_paths = [
            pathjoin('/etc', 'pastabin.json'),
            pathjoin(environ.get('HOME', ''), '.pastabin.json'),
            pathjoin('./', 'pastabin.json')]
    for path in search_paths:
        if isfile(path):
            #Read the configuration file
            with open(path, 'r') as json_file:
                CONFIG.update(json.load(json_file))


app = Flask(__name__)
read_config()
app.jinja_env.autoescape = True
app.secret_key = str(CONFIG['secret_key'])


class PygmentsStyle(Style):
    """Pygments style."""
    styles = {
        Keyword: CONFIG['color_keyword'],
        Name: CONFIG['color_name'],
        Comment: CONFIG['color_comment'],
        String: CONFIG['color_string'],
        Error: CONFIG['color_error'],
        Number: CONFIG['color_number']}


def colorize(language, title, text):
    """Colorize the text syntax.

    Guess the language of the text and colorize it.

    Returns a tuple containing the colorized text and the language name.
    """
    formatter = HtmlFormatter(
        linenos=True, style=PygmentsStyle, noclasses=True, nobackground=True)
    #Try to get the lexer by name
    try:
        lexer = get_lexer_by_name(language.lower())
        return highlight(text, lexer, formatter), lexer.name
    except LexerNotFound:
        pass
    #Try to get the lexer by filename
    try:
        lexer = get_lexer_for_filename(title.lower())
        return highlight(text, lexer, formatter), lexer.name
    except LexerNotFound:
        pass
    #Try to guess the lexer from the text
    try:
        lexer = guess_lexer(text)
        if lexer.analyse_text(text) > .3:
            return highlight(text, lexer, formatter), lexer.name
    except LexerNotFound:
        pass
    #Fallback to the plain/text lexer
    lexer = get_lexer_by_name('text')
    return highlight(text, lexer, formatter), lexer.name


def get_lexers():
    """Get the supported language list.

    Yield tuples containing the language Displayable name and the language
    lexer name: ('Display Name', 'Lexer Name')
    """
    for lexer in get_all_lexers():
        yield lexer[0], lexer[1][0]


def get_random_password():
    """Get an random 8-character password."""
    return ''.join(random.sample('abcdefghijklmnopqrstuvwxyz0123456789', 8))


@app.template_filter('date_format')
def pretty_datetime(date):
    """Convert the date into a better human readable format."""
    return date.strftime('%A %d %B %Y @ %H:%M:%S').decode('utf-8')


def send_email(message, recipient):
    """Send a email.

    Arguments:
        message -- the email message
        recipient -- the email address where the message will be sent
    """
    msg = MIMEText(message)
    msg['Subject'] = CONFIG['email_subject']
    msg['To'] = recipient
    msg['From'] = CONFIG['email_from_addr']
    try:
        smtp = smtplib.SMTP(
            CONFIG['email_smtp_server'], CONFIG['email_smtp_port'])
        smtp.sendmail(CONFIG['email_from_addr'], recipient, msg.as_string())
    except socketerror:
        return False
    else:
        smtp.quit()
    return True


def get_page_informations(title='Unknown', menu_active=None):
    """Return various informations like the menu, the page title,...

    Arguments:
        title -- The page title
        menu_active -- The name of the current page
    """
    #Menu items for everybody
    menu_items = [
        {'name': 'index',
         'title': 'Home',
         'url': url_for('index'),
         'active': False},
        {'name': 'add',
         'title': 'New snippet',
         'url': url_for('add_snippet_get'),
         'active': False}]
    #Menu items for logged users
    if session.get('login', False):
        menu_items.append({
            'name': 'my_snippets',
            'title': 'My snippets',
            'url': url_for('my_snippets'),
            'active': False})
    #Active item of the menu
    for item in menu_items:
        if menu_active == item['name']:
            item['active'] = True
            break
    return {'menu': menu_items,
            'title': title or 'Unnamed snippet',
            'doc': '<p>%s</p>' % __doc__.replace('\n\n', '</p>\n<p>'),
            'appname': __app_name__}


def login_required(func):
    """Check the user rights.

    If a user goes to a protected page and is not logged in or have not
    rights to do some actions like modify or delete, then he should be
    redirected to the abort page.
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        """The decorated function."""
        item = Snippet.all.filter(c.id == kwargs['snippet_id'])
        item = item.one(None).execute()
        if item and item['person'] and session.get('id') and \
                item['person']['id'] == session.get('id', 0):
            return func(*args, **kwargs)
        return abort(403)
    return decorated_function


@app.route('/', methods=['GET'])
def index():
    """The home page of the site."""
    return render_template(
        'index.html.jinja2',
        snippets=list(Snippet.all.sort(-c.date)[:10].execute()),
        page=get_page_informations(title='Home'))


@app.route('/snippet/<int:snippet_id>', methods=['GET'])
@app.route('/s/<int:snippet_id>', methods=['GET'])
def view_snippet(snippet_id):
    """The snippet view page.

    Argument:
        snippet_id -- the id of the snippet to display
    """
    item = Snippet.all.filter(c.id == snippet_id).one(None).execute()
    if item:
        item['text'], lexername = colorize(
            item['language'], item['title'], item['text'])
        return render_template(
            'snippet.html.jinja2', snippet=item, lexername=lexername,
            page=get_page_informations(title=item['title']))
    else:
        return abort(404)


@app.route('/my_snippets', methods=['GET'])
def my_snippets():
    """The user's snippet list page."""
    #Check if the user is logged
    if not session.get('id'):
        return abort(403)
    item = Snippet.all.filter(c.person.id == session.get('id')).sort(-c.date)
    item = item.execute()
    if item:
        return render_template(
            'my_snippets.html.jinja2', snippets=list(item),
            page=get_page_informations(
                title='My snippets',
                menu_active='my_snippets'))
    else:
        return abort(404)


@app.route('/add', methods=['GET'])
def add_snippet_get(def_title='', def_lng='', def_txt=''):
    """The page for adding snippets.

    Keyword arguments:
        def_title -- The prefilled text of the title field
        def_lng -- The prefilled text of the language field
        def_txt -- The prefilled text of the title text
    """
    return render_template(
        'edit_snippet.html.jinja2',
        snip_title=def_title,
        snip_language=def_lng,
        snip_text=def_txt,
        action=url_for('add_snippet_post'),
        cancel=url_for('index'),
        lexerslist=get_lexers(),
        page=get_page_informations(
            title='Add a new Snippet',
            menu_active='add'))


@app.route('/add', methods=['POST'])
def add_snippet_post():
    """The page for adding snippets (POST)."""
    if request.form['snip_text']:
        item = Snippet.create({
                'person': session.get('id', 0),
                'date': datetime.now(),
                'language': request.form['snip_language'],
                'title': request.form['snip_title'],
                'text': request.form['snip_text']})
        item.save()
        return redirect(url_for('view_snippet', snippet_id=item['id']))
    else:
        flash('You can\'t post empty snippets !', 'error')
        return add_snippet_get(
            request.form['snip_title'],
            request.form['snip_language'],
            request.form['snip_text'])


@app.route('/fork/<int:snippet_id>', methods=['GET'])
def fork_snippet_get(snippet_id):
    """The page for forking snippets.

    Argument:
        snippet_id -- The id of the snippet to fork
    """
    item = Snippet.all.filter(c.id == snippet_id).one(None).execute()
    return add_snippet_get(
        def_title=item['title'], def_lng=item['language'], def_txt=item['text'])


@app.route('/modify/<int:snippet_id>', methods=['GET'])
@login_required
def modify_snippet_get(snippet_id):
    """The page for modifying snippets.

    Argument:
        snippet_id -- The id of the snippet to modify
    """
    item = Snippet.all.filter(c.id == snippet_id).one(None).execute()
    if item:
        return render_template(
            'edit_snippet.html.jinja2',
            snip_title=item['title'],
            snip_language=item['language'],
            snip_text=item['text'],
            action=url_for('modify_snippet_post', snippet_id=snippet_id),
            cancel=url_for('view_snippet', snippet_id=snippet_id),
            lexerslist=get_lexers(),
            page=get_page_informations(
                title='Modify a snippet (%s)' % (
                    item['title'] or 'Unnamed snippet')))
    else:
        return abort(404)


@app.route('/modify/<int:snippet_id>', methods=['POST'])
@login_required
def modify_snippet_post(snippet_id):
    """The page for modifying snippets (POST).

    Argument:
        snippet_id -- The id of the snippet to modify
    """
    item = Snippet.all.filter(c.id == snippet_id).one(None).execute()
    if item and request.form['snip_text']:
        item['date'] = datetime.now()
        item['language'] = request.form['snip_language']
        item['title'] = request.form['snip_title']
        item['text'] = request.form['snip_text']
        item.save()
    else:
        flash('Error when modifying the snippet', 'error')
    return redirect(url_for('view_snippet', snippet_id=item['id']))


@app.route('/delete/<int:snippet_id>', methods=['GET'])
@login_required
def delete_snippet_get(snippet_id):
    """The page for deleting snippets.

    Argument:
        snippet_id -- The id of the snippet to delete
    """
    item = Snippet.all.filter(c.id == snippet_id).one(None).execute()
    if item:
        return render_template(
            'delete.html.jinja2',
            snip_id=snippet_id,
            snip_title=item['title'],
            page=get_page_informations(title='Delete a snippet'))
    else:
        return abort(404)


@app.route('/delete/<int:snippet_id>', methods=['POST'])
@login_required
def delete_snippet_post(snippet_id):
    """The page for deleting snippets (POST).

    Argument:
        snippet_id -- The id of the snippet to delete
    """
    item = Snippet.all.filter(c.id == snippet_id).one(None).execute()
    if item:
        item.delete()
        return redirect(url_for('index'))
    else:
        return abort(404)


@app.route('/connect', methods=['GET'])
def get_connect():
    """The page containing the login form."""
    #if the user is already connected, redirect him
    if session.get('id'):
        return redirect(url_for('index'))
    else:
        return render_template(
            'connect.html.jinja2',
            page=get_page_informations(title='Connexion'))


@app.route('/connect', methods=['POST'])
def connect():
    """The page containing the login form (POST)."""
    item = Person.all.filter(
            (c.login.lower() == request.form['login'].lower())
            & (c.password == sha256(request.form['password']).hexdigest()))
    item = item.one(None).execute()
    if item:
        session['login'] = item['login']
        session['id'] = item['id']
        flash('Welcome %s !' % session['login'], 'ok')
        return redirect(url_for('index'))
    else:
        flash('Invalid login or password !', 'error')
        return redirect(url_for('connect'))


@app.route('/disconnect', methods=['GET'])
def disconnect():
    """Disconnect the logged user."""
    session['login'] = session['id'] = None
    flash('You are disconnected !', 'ok')
    return redirect(url_for('index'))


@app.route('/register', methods=['GET'])
def get_register(def_login='', def_email=''):
    """Page for registering new users.

    Keyword arguments:
        def_login -- The prefilled value for the login field
        def_email -- The prefilled value for the login email
    """
    return render_template(
        'account.html.jinja2',
        action=url_for('register'),
        login=def_login,
        email=def_email,
        page=get_page_informations(title='Register'))


@app.route('/register', methods=['POST'])
def register():
    """Page for registering new users (POST)."""
    #Check if all fields are filled and if the passwords are equal
    if not all((request.form['login'], request.form['password1'],
                request.form['password2'], request.form['email'])) \
                or request.form['password1'] != request.form['password2']:
        flash('Some fields are empty or passwords are not the same!', 'error')
        return get_register(
            def_login=request.form['login'], def_email=request.form['email'])
    item = Person.all.filter(c.login.lower() == request.form['login'].lower())
    item = item.one(None).execute()
    #Check if the login already exists
    if item:
        flash('The login already exists!', 'error')
        return get_register(def_email=request.form['email'])
    #Register the user
    person = Person.create({
        'login': request.form['login'],
        'password': sha256(request.form['password2']).hexdigest(),
        'email': request.form['email']})
    person.save()
    #Login the user
    session['login'] = person['login']
    session['id'] = person['id']
    flash('Welcome %s !' % session['login'], 'ok')
    return redirect(url_for('index'))


@app.route('/account', methods=['GET'])
def get_account():
    """Page for modifying the logged user's account."""
    item = Person.all.filter(c.id == session.get('id')).one(None).execute()
    return render_template(
        'account.html.jinja2',
        action=url_for('account'),
        login=item['login'],
        email=item['email'],
        page=get_page_informations(title='Manage my account'),
        person=item)


@app.route('/account', methods=['POST'])
def account():
    """Page for modifying the logged user's account (POST)."""
    #Check if the user is logged
    if not session.get('id'):
        return abort(403)
    #Check if the login field or the email field is empty, and check
    #if the two password fields are the same
    if not all((request.form['login'], request.form['email'])) \
            or request.form['password1'] != request.form['password2']:
        flash('Some fields are empty or passwords are not the same!', 'error')
        return get_account()
    #Check if the login already exists in th DB and if the
    #wanted login is not Guest
    login = request.form['login'].lower()
    person = (
        Person.all.filter(c.login.lower() == login)
        .one(None).execute())
    if person and login != session.get('login', '').lower() or login == 'guest':
        flash('The login already exists!', 'error')
        return get_account()
    #Update the account
    item = Person.all.filter(c.id == session['id']).one(None).execute()
    if item:
        item['login'] = request.form['login']
        item['email'] = request.form['email']
        #If the user fill the passwords, check them and update the password
        if request.form['password1']:
            item['password'] = sha256(request.form['password1']).hexdigest()
        item.save()
        session['login'] = request.form['login']
        flash('Your account has been modified!', 'ok')
    return redirect(url_for('index'))


@app.route('/password', methods=['GET'])
def forgotten_password_get():
    """Page for getting a new password."""
    return render_template(
        'forgotten_password.html.jinja2',
        page=get_page_informations(title='Forgot your password?'))


@app.route('/password', methods=['POST'])
def forgotten_password_post():
    """Verify if the mail can be sent if so send_email"""
    item = (
        Person.all.filter(c.login.lower() == request.form['login'].lower())
        .one(None).execute())
    if item and item['email'] == request.form['email']:
        password = get_random_password()
        item['password'] = sha256(password).hexdigest()
        message = 'Your new password is: %s' % password
        if send_email(message, item['email']):
            item.save()
            flash('An email was sent to: %s' % item['email'], 'ok')
            return redirect(url_for('connect'))
        else:
            flash('An error occurred while sending the email', 'error')
            return forgotten_password_get()
    else:
        flash('Login and email mismatch.', 'error')
    return forgotten_password_get()


if __name__ == '__main__':
    app.run()
