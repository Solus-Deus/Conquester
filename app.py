from flask import Flask, redirect, url_for, render_template, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
from time import sleep

app = Flask(__name__)
app.secret_key = "genius"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3' 
app.permanent_session_lifetime = timedelta(hours=1)

db = SQLAlchemy(app)

class users(db.Model):
	_id = db.Column("id", db.Integer, primary_key=True)
	name = db.Column(db.String(20))
	password = db.Column(db.String(100))
	email = db.Column(db.String(100))
	
	def __init__(self, name, password, email):
		self.name=name
		self.email=email
		self.password=password

@app.route("/", methods=['GET', 'POST'])
def homepage():
	if request.method == 'POST':
		if request.form.get("login")=="Log in":
			return redirect(url_for("login"))
		elif request.form.get("newacc")=="Create account":
			return redirect(url_for("newacc"))
			
	elif "login" in session:
		return redirect(url_for("user"))
	else:
		return render_template('home.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		if request.form.get("submit")=="submit":
			session.permanent = True
			login = request.form["login"]
			password = request.form["password"]
			
			found_user = users.query.filter_by(name=login).first()
			if found_user and password==found_user.password:
				session["login"] = found_user.name
				session["email"] = found_user.email
				flash("Login succesfull!","info")
				return redirect(url_for("user"))
			else:
				flash("Wrong password or user does not exist!","info")
				return redirect(url_for("login"))
		else:
			flash(request.form,"info")
			return render_template('login.html')
				
	elif "login" in session:
		return redirect(url_for("user"))
	elif request.method == 'GET':
		return render_template('login.html')

	
@app.route("/createaccount", methods=['GET', 'POST'])
def newacc():
	if request.method == 'POST':
		if request.form.get("create account")=="Submit":
			if request.form["password"]!=request.form["password_again"]:
				print("test1")
				flash("Passwords do not match!", "info")
				return render_template('newacc.html')
			else:
				print("test2")
				login = request.form["login"]
				password=request.form["password"]
				
				found_user = users.query.filter_by(name=login).first()
				
				if found_user:
					flash("This user already exists! Login or use another username!", "info")
					return render_template('newacc.html')
				else:
					usr = users(login, password, "")
					db.session.add(usr)
					db.session.commit()
					flash("Account created! Proceed to login!","info")
					return redirect(url_for("homepage"))
				
		else:
			return render_template('newacc.html')
	else:
		return render_template('newacc.html')
	

@app.route('/admin', methods=['GET', 'POST'])
def admin():
	if "login" in session:
		user=session["login"]
		if user == "admin":
			user_list = users.query.filter_by().all()
			return render_template('admin.html',listt=user_list, lenn=len(user_list))
		else:
			return redirect(url_for("homepage"))
	else:
		return redirect(url_for("homepage"))

@app.route('/user', methods=['GET', 'POST'])
def user():
	email=None
	if "login" in session:
		user=session["login"]
		if request.method == 'POST':
			if request.form.get("logout")=="logout":
				return redirect(url_for("logout"))
			elif request.form.get("save")=="Save":
				email = request.form["email"]
				session["email"] = email
				found_user = users.query.filter_by(name=user).first()
				found_user.email = email
				db.session.commit()
		else:
			if "email" in session:
				email = session["email"]
		return render_template('user.html', login=user, email=email)
	else:
		return redirect(url_for("homepage"))
@app.route("/logout")
def logout():
	session.pop("login",None)
	session.pop("email",None)
	return redirect(url_for("homepage"))
	

if __name__=="__main__":
	with app.app_context():
		db.create_all()
	app.run(debug=True)
	
