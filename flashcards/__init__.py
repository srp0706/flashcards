import os

from base64 import b64encode
from flask import Flask, flash, g, render_template, redirect, request, url_for
from random import randint
from flashcards.db import get_db

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.root_path, 'flashcards.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass


    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello. This is a test landing page'


    # the main index
    @app.route('/')
    def index_page():
        return render_template('index.html')


    # add a new flashcard to the database
    @app.route('/newcard', methods=('GET', 'POST'))
    def newcard():
        if request.method == 'POST':
            error=None
            db=get_db()

            lastitem = db.execute('SELECT item FROM flashcards ORDER BY item DESC;').fetchone()
            if lastitem==None:
                item=1
            else:
                item=int(lastitem['item'])+1
            imgdata = request.files['imgfile'].read()
            imgdata = b64encode(imgdata)
            desc = request.form['desc']
            note = request.form['note']

            if not imgdata:
                error = 'An image file is required.'
            if not desc:
                error = 'Description is required.'

            if error is not None:
                flash(error)
            else:
                db.execute(
                    'INSERT INTO flashcards (item, pic, desc, note)'
                    ' VALUES (?, ?, ?, ?)',
                    (item, imgdata, desc, note)
                )
                db.commit()
                return redirect(url_for('index'))

        return render_template('newcard.html')


    # show a random flashcard from the database, hiding the description until user clicks 'show'
    @app.route('/random')
    def randomcard():
        db = get_db()
        n=db.execute('SELECT COUNT(item) FROM flashcards;').fetchone()
        n=n[0]
        r = randint(1,n)
        card=db.execute('SELECT * FROM flashcards WHERE item={:d};'.format(r)).fetchone()
        return render_template('randomcard.html', card=card)


    # show a map view of all cards in the database
    @app.route('/allcards')
    def allcards():
        db=get_db()
        cards=db.execute('SELECT * FROM flashcards').fetchall()
        return render_template('allcards.html', cards=cards)


    from . import db
    db.init_app(app)

    app.add_url_rule('/', endpoint='index')

    return app