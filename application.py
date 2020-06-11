from flask import Flask, render_template, redirect


app = Flask(__name__, static_url_path='/groupstudy')

@app.route('/')
def index():
    return render_template("front.html")

@app.route('/login')
def redirect():
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
