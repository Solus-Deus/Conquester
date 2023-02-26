from flask import Flask, redirect, url_for, render_template, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
import threading
import time

app = Flask(__name__)
app.secret_key = "genius"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.permanent_session_lifetime = timedelta(hours=1)

db = SQLAlchemy(app)


class Users(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    password = db.Column(db.String(100))
    email = db.Column(db.String(100))

    def __init__(self, name, password, email):
        self.name = name
        self.email = email
        self.password = password

def perform_task():
    print("new minute")

def schedule_task():
    while abs(time.time())%60!=0:
        pass
    while True:
        perform_task()
        time.sleep(60)

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
            if request.form["password"] != request.form["password_again"]:
                print("test1")
                flash("Passwords do not match!", "info")
                return render_template('newacc.html')
            else:
                print("test2")
                # login = request.form["login"]
                password = request.form["password"]

                found_user = Users.query.filter_by(name=request.form["login"]).first()

                if found_user:
                    flash("This user already exists! Login or use another username!", "info")
                    return render_template('newacc.html')
                else:
                    usr = Users(login, password, "")
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
        return render_template('gamebase.html', logs=["test1", "test2", "test3"])
    else:
        return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session.pop("login", None)
    session.pop("email", None)
    return redirect(url_for("homepage"))


if __name__ == "__main__":
    thread = threading.Thread(target=schedule_task)
    thread.start()
    with app.app_context():
        db.create_all()
    app.run(debug=True)
