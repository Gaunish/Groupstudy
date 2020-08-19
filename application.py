#importing all dependencies
import os
from flask import Flask, render_template, redirect, g, session, request, flash
from flask_session import Session
from tempfile import mkdtemp
import sqlite3
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash


#configuring app
app = Flask(__name__)

#Ensure template are auto reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


#configure session to filesystem
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#Ensure responses arent cached
@app.after_request
def after_response(response):
    response.headers['Cache-Control'] = "no-cache, no-store, must-revalidate"
    response.headers['Expires'] = 0
    response.headers['Pragma'] = "no-cache"
    return response

#connecting database
DATABASE = '~/GroupStudy/Groupstudy/database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


#Redirects to the front page
@app.route('/')
def index():
    return render_template("front.html")

@app.route('/login')
def redirect():
    #checking if user has entered via webpage
    if request.method == "POST":
        return render_template("login.html")
    else:
        return render_template("login.html")

@app.route('/register')
def redirect1():
    return render_template("register.html")


@app.route('/create')
def redirect2():
    return render_template("create.html")

@app.route('/createTopic')
def redirect3():
    return render_template("createTopic.html")

if __name__ == '__main__':
    app.run()
