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


__app_name__ = 'PastaBin'
__version__ = '0.1'


from datetime import datetime
from hashlib import sha256
from functools import wraps
import random

from flask import (Flask, url_for, render_template, redirect, abort,
        flash, escape, g, session, request)
from pygments import highlight
from pygments.util import ClassNotFound as LexerNotFound
from pygments.formatters import HtmlFormatter
from pygments.lexers import (get_all_lexers, get_lexer_by_name,
        get_lexer_for_filename, guess_lexer)
from pygments.style import Style
from pygments.token import Keyword, Name, Comment, String, Error, Number
from multicorn.requests import CONTEXT as c

from access_points import Person, Snippet
from utils.mail import SmtpAgent


app = Flask(__name__)
app.jinja_env.autoescape = True
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'


class PygmentsStyle(Style):
    """Pygments style based on Solarized."""
    styles = {
        Keyword: '#b58900',
        Name: '#cb4b16',
        Comment: '#839496',
        String: '#2aa198',
        Error: '#dc322f',
        Number: '#859900'}


def colorize(language, title, text):
    """Colorize the text syntax.

    Guess the language of the text and colorize it.

    Returns a tuple containing the colorized text and the language name.
    """
    formatter = HtmlFormatter(
            linenos=True,
            style=PygmentsStyle,
            noclasses=True,
            nobackground=True)
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


def get_lexers_list():
    """Get the supported language list.

    Returns a list of tuple containing the language Displayable name
    and the language lexer name:
        [('Display Name', 'Lexer Name'),]
    """
    lexers_list = []
    for lexer in get_all_lexers():
        lexers_list.append((lexer[0], lexer[1][0]))
    return lexers_list


def get_random_password():
    """Get an random 8-character password."""
    return ''.join(random.sample("abcdefghijklmnopqrstuvwxyz0123456789", 8))


@app.before_request
def constants():
    """ Global context constant injector."""
    g.smtp_agent = SmtpAgent()


@app.template_filter('date_format')
def pretty_datetime(date):
    """Convert the date into a better human readable format."""
    return date.strftime('%A %d %B %Y @ %H:%M:%S').decode('utf-8')


@app.template_filter('snip_user')
def snip_user(user):
    """Check the user's name"""
    if type(user) != unicode:
        return 'Guest'
    else:
        return user


@app.template_filter('check_title')
def check_title(title):
    """Check the snippet's title"""
    if title == '':
        return 'Unamed snippet'
    else:
        return title


def get_page_informations(title='Unknown', menu_active=None):
    """Retun various informations like the menu, the page title,...

    Arguments:
        title -- The page title
        menu_active -- The name of the current page
    """
    menu_items = [
            {
                'name': 'index',
                'title': 'Home',
                'url': url_for('index'),
                'active': False},
            {
                'name': 'add',
                'title': 'New snippet',
                'url': url_for('add_snippet_get'),
                'active': False}]
    if session.get('login', False):
        menu_items.append({
            'name': 'my_snippets',
            'title': 'My snippets',
            'url': url_for('my_snippets'),
            'active': False})
    for item in menu_items:
        if menu_active == item['name']:
            item['active'] = True
            break
    return {
            'menu': menu_items,
            'title': check_title(title),
            'appname': __app_name__}


def get_user_id():
    """Return the user id if logged, 0 else"""
    return session.get('id', 0)


def login_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        item = Snippet.all.filter(c.id == kwargs['id']).one(None).execute()
        if item is not None and item['person'] is not None:
            if item["person"]["id"] == get_user_id() and get_user_id() != 0:
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
def get_snippet_by_id(snippet_id):
    """The snippet view page.

    Argument:
        snippet_id -- the id of the snippet to display
    """
    item = Snippet.all.filter(c.id == snippet_id).one(None).execute()
    if item is not None:
        item['text'], lexername = colorize(
                item['language'],
                item['title'],
                item['text'])
        return render_template(
                'snippet.html.jinja2',
                snippet=item,
                lexername=lexername,
                page=get_page_informations(title=item['title']))
    else:
        return abort(404)


@app.route('/my_snippets', methods=['GET'])
def my_snippets():
    """The user's snippet list page."""
    if get_user_id() <= 0:
        return abort(403)
    item = Snippet.all.filter(c.person.id == get_user_id()).sort(-c.date)
    item = item.execute()
    if item is not None:
        return render_template(
                'my_snippets.html.jinja2',
                snippets=list(item),
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
            lexerslist=get_lexers_list(),
            page=get_page_informations(
                title='Add a new Snippet',
                menu_active='add'))


@app.route('/add', methods=['POST'])
def add_snippet_post():
    """The page for adding snippets (POST)."""
    if len(request.form['snip_text']) > 0:
        item = Snippet.create({
            'person': get_user_id(),
            'date': datetime.now(),
            'language': request.form['snip_language'],
            'title': request.form['snip_title'],
            'text': request.form['snip_text']})
        item.save()
        return redirect(url_for('get_snippet_by_id', snippet_id=item['id']))
    else:
        flash('The text field is empty...', 'error')
        return add_snippet_get(
                request.form['snip_title'],
                request.form['snip_language'],
                request.form['snip_text'])


@login_required
@app.route('/modify/<int:id>', methods=['GET'])
def modify_snippet_get(id):
    """The page for modifying snippets.

    Argument:
        id -- The id of the snippet to modify
    """
    item = Snippet.all.filter(c.id == id).one(None).execute()
    if item is not None:
        return render_template(
                'edit_snippet.html.jinja2',
                snip_title=item['title'],
                snip_language=item['language'],
                snip_text=item['text'],
                action=url_for('modify_snippet_post', id=id),
                cancel=url_for('get_snippet_by_id', snippet_id=id),
                lexerslist=get_lexers_list(),
                page=get_page_informations(
                    title='Modify a snippet (%s)' % item['title']))
    else:
        return abort(404)


@login_required
@app.route('/modify/<int:id>', methods=['POST'])
def modify_snippet_post(id):
    """The page for modifying snippets (POST).

    Argument:
        id -- The id of the snippet to modify
    """
    item = Snippet.all.filter(c.id == id).one(None).execute()
    if item is not None and len(request.form['snip_text']) > 0:
        item['date'] = datetime.now()
        item['language'] = request.form['snip_language']
        item['title'] = request.form['snip_title']
        item['text'] = request.form['snip_text']
        item.save()
    else:
        flash('Error when modifying the snippet', 'error')
    return redirect(url_for('get_snippet_by_id', snippet_id=item['id']))


@login_required
@app.route('/delete/<int:id>', methods=['GET'])
def delete_snippet_get(id):
    """The page for deleting snippets.

    Argument:
        id -- The id of the snippet to delete
    """
    item = Snippet.all.filter(c.id == id).one(None).execute()
    if item is not None:
        return render_template(
                'delete.html.jinja2',
                snip_id=id,
                snip_title=item['title'],
                page=get_page_informations(title='Delete a snippet'))
    else:
        return abort(404)


@login_required
@app.route('/delete/<int:id>', methods=['POST'])
def delete_snippet_post(id):
    """The page for deleting snippets (POST).

    Argument:
        id -- The id of the snippet to delete
    """
    item = Snippet.all.filter(c.id == id).one(None).execute()
    if item is not None:
        item.delete()
        return redirect(url_for('index'))
    else:
        return abort(404)


@app.route('/connect', methods=['GET'])
def get_connect():
    """The page containing the login form."""
    if get_user_id():
        return redirect(url_for('index'))
    return render_template(
            'connect.html.jinja2',
            page=get_page_informations(title='Connexion'))


@app.route('/connect', methods=['POST'])
def connect():
    """The page containing the login form (POST)."""
    item = Person.all.filter(
        c.login.lower() == request.form['login'].lower()).one(None)
    item = item.execute()
    if item is not None:
        if '' == request.form.get('login', '') \
        or '' == request.form.get('password', ''):
            flash('Invalid login or password !', 'error')
            return redirect(url_for('connect'))
        if item['password'] == sha256(request.form['password']).hexdigest():
            session['login'] = item['login']
            session['id'] = item['id']
            flash('Welcome %s !' % escape(session['login']), 'ok')
            return redirect(url_for('index'))
        else:
            flash('Invalid login or password !', 'error')
            return redirect(url_for('connect'))
    else:
        flash('Invalid login or password !', 'error')
        return redirect(url_for('connect'))


@app.route('/disconnect', methods=['GET'])
def disconnect():
    """Disconnect the logged user."""
    session['login'] = None
    session['id'] = None
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
    if '' == request.form.get('login', '') \
        or '' == request.form.get('password1', '') \
        or '' == request.form.get('password2', '') \
        or '' == request.form.get('email', '') :
        flash('Some fields are empty !', 'error')
        return get_register(def_login=request.form.get('login'),
                def_email=request.form.get('email'))
    if request.form['password1'] != request.form['password2']:
        flash('Passwords are not same !', 'error')
        return get_register(def_login=request.form.get('login'),
                def_email=request.form.get('email'))
    item = Person.all.filter(c.login.lower() == \
        request.form['login'].lower()).one(None).execute()
    if item is not None:
        flash('Your login already exists !', 'error')
        return get_register(def_login='', def_email=request.form.get('email'))
    else:
        person = Person.create({
            'login': request.form['login'],
            'password': sha256(request.form['password2']).hexdigest(),
            'email': request.form['email']})
        person.save()
        session['login'] = person['login']
        session['id'] = person['id']
    flash('Welcome %s !' % escape(session['login']), 'ok')
    return redirect(url_for('index'))


@app.route('/account', methods=['GET'])
def get_account():
    """Page for modifying the logged user's account."""
    item = Person.all.filter(c.id == get_user_id()).one(None).execute()
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
    if not session.get('id'):
        return redirect(url_for('connect'))
    if '' == request.form.get('login', '') \
        or '' == request.form.get('email', ''):
        flash('Some fields are empty !', 'error')
        return get_account()
    person = Person.all.filter(c.login.lower() == \
        request.form['login'].lower()).one(None).execute()
    item = Person.all.filter(c.id == session['id']).one(None).execute()
    if person is not None and person['login'] != item['login']:
        flash('Your login already exists !', 'error')
        return get_account()
    if item is not None:
        item['login'] = request.form['login']
        item['email'] = request.form['email']
        if request.form['password1'] or request.form['password2'] :
            if request.form['password1'] != request.form['password2']:
                flash('Passwords are not same !', 'error')
                return get_account()
            else:
                item['password'] = sha256(request.form['password1']).hexdigest()
        item.save()
        session['login'] = request.form['login']
        flash('Your account is been modify !', 'ok')
    return redirect(url_for('index'))


@app.route('/password', methods=['GET'])
def forgotten_password_get():
    """Page for getting a new password."""
    return render_template(
            'forgotten_password.html.jinja2',
            page=get_page_informations(title='Forgot your password ?'))


@app.route('/password', methods=['POST'])
def forgotten_password_post():
    """Page for getting a new password (POST)."""
    password = get_random_password()
    item = Person.all.filter(c.login.lower() == request.form['login'].lower())
    item = item.one(None).execute()
    if item is not None:
        item['password'] = sha256(password).hexdigest()
        item.save()
        message = u'your new password is: %s' % password
        subject = u'Forgotten Password'
        g.smtp_agent.sendmail_alternative(message, subject, item['email'])
        flash('A mail was sent to : %s' % item['email'], 'ok')
        return redirect(url_for('connect'))
    else:
        flash('This login does not exist', 'error')
        return forgotten_password_get()


if __name__ == '__main__':
#    app.run()
    app.run(debug=True)

