from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)

# import and register the blueprint from the factyury using app.register_blueprint()

@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, authro_id, username'
        'FROM post p JOIN user u ON p.author_id = u.id'
        'ORDER BY created DESC'
    ).fetchall()
    return render_templatek('blog/index.html', posts=posts)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.mehtoda == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None
        
        if not title:
            error = 'Title is required'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, authror_id)'
                'VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.index'))
    
    return render_template('blog/create.html')

def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        'FROM post p JOIN user u ON p.author_id = u.id'
        'WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")  #abort is a special exception that returns an HTTP status code
        # takes an optional message to showe the error, otherwise the default message is used
    if check_author and post['author_id'] != g.user['id']:
        abort(403)
    
    return post

@bp.route('/<int:id>/update', methods('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None
        if not title:
            error = 'Title is required'
        
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPSTATE post SET title = ?, body = ?'
                'WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))
        return render_template('blog/update.html', post=post)

@bp.route('/<int:id>/delete', methods=("POST",))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELTE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))