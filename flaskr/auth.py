'''
Create a blueprint
a Blueprint is a way to organize a gr4oup of related views and other code. Rather than registering
views and other code directly with and application, they are registered with a blueprint. Then the 
blueprint is registered with the application when it is available in the factory function.

Flaskr will have two blueprints, one for authentication functions and one for the blog posts functions.
The code for each blueprint will go in a separate module. Since the blog needs to know about authentication,
you'll write the authentication one first.
'''

import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')
# creates a Blueprint named 'auth'
# __name__ is passed so the blueprint knows where it is defined

# placing app.register_blueprint() in __init__.py will register the blueprint

@bp.route('/register', methods=('GET', 'POST')) # associates the URL /register with register view function
# flask will call register when receiving a request for /auth/register and use the return value as a response
def register():
    if request.method == 'POST':
        username = request.form['username'] # request.form is special dictionary type for form key/value pairs
        password = request.form['password']
        db = get_db()
        error = None

        # verify that username and password are not empty
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (username, password) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                ) # executes the first parameter (SQL query), subbing in the second parameter (tuple) in place of (?, ?)
                # generate_password_hash from werkzeug encrypts the password for saving to the db
                db.commit()
            except db.IntegrityError:   # checks against the schema rules (username must be UNIQUE)
                error = f"User {username} is already registered."
            else:
                return redirect(url_for("auth.login")) # url_for generates the url for the parameter
                # it is best practice, can change URLs later without changing all code referencing that URL
            
        flash(error)    #flash stores messages that can b e retrieved when rendering the template
    
    return render_template('auth/register.html') # render_template will render a template containg HTML

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username'] 
        password = request.form['password']
        db = get_db()
        error = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()    # fetchone() returns a single row from the query

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password): # compares hashed password in storage 
            # to the hash of the password input by the user
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))
            # session is dict that stores data across requests.
            # after successful validation, user id is stores in a new session
            # data stored in a cookie and sent to browser, which is fetched with subsequent requests
        
        flash(error)

    return render_template('auth/login.html')

@bp.before_app_request  # registers a function that runs before the view function
        # no matter what URL is requested. 
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Require authentication in other views
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        
        return view(**kwargs)
    
    return wrapped_view
# this decorate returns a new view function that wraps the original view it's applied to.
# The new function checks if a user is loaded and redirects to the login page otherwise.
# If a user is loaded, the original view is called and continues normally.
# this decorator will be used when writing the blog views

# When using a blueprint, the name of the blueprint is prepended to the name of the function,
# so the enpoint for the login function written above is 'auth.login' because it was added
# to the 'auth' blueprint