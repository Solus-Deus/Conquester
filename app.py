from math import floor

from flask import Flask, redirect, url_for, render_template, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from datetime import timedelta
import threading
import time
import os

minute_length = 10

app = Flask(__name__)
app.secret_key = "genius"
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'
print(app.config['SQLALCHEMY_DATABASE_URI'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.permanent_session_lifetime = timedelta(hours=1)


db = SQLAlchemy(app)


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    move = db.Column(db.String(100))
    inventory = db.relationship("Inventory", backref="users")
    logs = db.Column(db.String(10000))

    def __init__(self, name, password):
        self.name = name
        self.password = password
        self.email = ""
        self.move = ""
        self.logs = '[]'

    def __repr__(self):
        return f'<User {self.name}>'


class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f'<Item {self.item}>'

#class Spalls(db.Model):
#    _id = db.Column("id", db.Integer, primary_key=True)
#    name = db.Column(db.String(20))
#    ingredients = db.Column(db.String(100))
#
#    def __init__(self, name, password, email):
#        self.name = name
#        self.email = email
#        self.password = password
#        self.move = ""
#        self.inventory = '{}'
#        self.logs = '[]'


def perform_task():
    print(time.ctime())
    with app.app_context():
        movers = Users.query.filter_by().all()
        for mover in movers:
            move = mover.move
            if move != "":
                inventory = mover.inventory
                if move == "ping":
                    newlog = "Pong"
                elif move == "apple":
                    found_inv = None
                    for i in inventory:
                        if i.item == "Apple":
                            found_inv = i
                            break
                    if found_inv==None:
                        found_inv=Inventory(item="Apple",amount=0,users=mover)
                        db.session.add(found_inv)
                        db.session.commit()
                    found_inv.amount += 1

                    newlog = "You took an apple. You now have " + str(found_inv.amount) + " Apples."
                else:
                    newlog = "error: Unknown move. Your move is " + move
                newlog = "[" + time.ctime() + "] " + newlog

                loggs = eval(mover.logs)
                loggs.append(newlog)
                if len(loggs) > 50:
                    loggs = loggs[:50]
                mover.logs = str(loggs)
                mover.move = ""
                db.session.commit()


def schedule_task():
    while floor(time.time()) % minute_length != 0:
        pass
    while True:
        perform_task()
        time.sleep(minute_length)


@app.route("/", methods=['GET', 'POST'])
def homepage():
    if request.method == 'POST':
        if request.form.get("login") == "Log in":
            return redirect(url_for("login"))
        elif request.form.get("newacc") == "Create account":
            return redirect(url_for("newacc"))

    else:
        return render_template('home.html')


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get("submit") == "submit":
            session.permanent = True
            # login = request.form["login"]
            password = request.form["password"]

            found_user = Users.query.filter_by(name=request.form["login"]).first()
            if found_user and password == found_user.password:
                session["login"] = found_user.name
                session["email"] = found_user.email
                flash("Login successful!", "info")
                return redirect(url_for("user"))
            else:
                flash("Wrong password or user does not exist!", "info")
                return redirect(url_for("login"))
        else:
            return render_template('login.html')

    elif "login" in session:
        return redirect(url_for("user"))
    elif request.method == 'GET':
        return render_template('login.html')


@app.route("/createaccount", methods=['GET', 'POST'])
def newacc():
    if request.method == 'POST':
        if request.form.get("create account") == "Submit":
            login = request.form["login"]
            password = request.form["password"]
            if password == "" or login == "":
                flash("Password or name cannot be empty!", "info")
                return render_template('newacc.html')
            elif password != request.form["password_again"]:
                flash("Passwords do not match!", "info")
                return render_template('newacc.html')
            elif len(login) < 3 or len(login) > 20:
                flash("Name length should be between 3 and 20 characters!", "info")
                return render_template('newacc.html')
            elif len(password) > 100:
                flash("Password should be no longer than 100 characters!", "info")
                return render_template('newacc.html')
            else:
                found_user = Users.query.filter_by(name=login).first()

                if found_user:
                    flash("This user already exists! Login or use another username!", "info")
                    return render_template('newacc.html')
                else:
                    usr = Users(login, password)
                    db.session.add(usr)
                    db.session.commit()
                    flash("Account created! Proceed to login!", "info")
                    return redirect(url_for("homepage"))

        else:
            return render_template('newacc.html')
    else:
        return render_template('newacc.html')


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if "login" in session:
        if session["login"] == "admin":
            user_list = Users.query.filter_by().all()
            return render_template('admin.html', listt=user_list, lenn=len(user_list))
        else:
            return redirect(url_for("homepage"))
    else:
        return redirect(url_for("login"))


@app.route('/user', methods=['GET', 'POST'])
def user():
    email = None
    if "login" in session:
        userr = session["login"]
        if request.method == 'POST':
            if request.form.get("logout") == "logout":
                return redirect(url_for("logout"))
            elif request.form.get("save") == "Save":
                email = request.form["email"]
                session["email"] = email
                found_user = Users.query.filter_by(name=userr).first()
                found_user.email = email
                db.session.commit()
        else:
            if "email" in session:
                email = session["email"]
        return render_template('user.html', login=userr, email=email)
    else:
        return redirect(url_for("login"))


@app.route('/game', methods=['GET', 'POST'])
def gamepage():
    if "login" in session:

        if request.method == 'POST':
            if request.form.get("ping") == "Ping!":
                move = "ping"
            elif request.form.get("apple") == "Take an apple":
                move = "apple"
            else:
                move = "Error: No such move!"
            found_user = Users.query.filter_by(name=session["login"]).first()
            found_user.move = move
            db.session.commit()
            flash("Move successful! You choose: " + move, "info")
            return redirect(url_for("gamepage"))
        else:
            userr = session["login"]
            found_user = Users.query.filter_by(name=userr).first()
            print(found_user.logs)
            return render_template('gamebase.html', logs=eval(found_user.logs), inv=found_user.inventory,
                                   toime=minute_length - (floor(time.time() % minute_length)))
    else:
        return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session.pop("login", None)
    session.pop("email", None)
    return redirect(url_for("homepage"))


thread = threading.Thread(target=schedule_task)
thread.start()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, use_reloader=False, host="0.0.0.0")
