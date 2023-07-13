import random
import randomname
from math import floor

from flask import Flask, redirect, url_for, render_template, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from datetime import timedelta
import threading
import time

minute_length = 10

app = Flask(__name__)
app.secret_key = "genius"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
print(app.config['SQLALCHEMY_DATABASE_URI'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.permanent_session_lifetime = timedelta(hours=1)

db = SQLAlchemy(app)

bridges = db.Table('bridges',
                   db.Column('primary', db.Integer, db.ForeignKey('spall.id')),
                   db.Column('secondary', db.Integer, db.ForeignKey('spall.id')))

guestings = db.Table('guestings',
                     db.Column('spall', db.Integer, db.ForeignKey('spall.id')),
                     db.Column('user', db.Integer, db.ForeignKey('user.id')))


def conrandom():
    m = random.randint(1, 6)
    if m < 4:
        k = 2
    elif m == 4:
        k = 1
    else:
        k = 2
        while True:
            m = random.randint(1, 3)
            if m == 3:
                k += 2
            else:
                k += m
                break
    return k


class Spall(db.Model):
    id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column(db.String(40))
    nameorig = db.Column(db.Boolean)
    size = db.Column(db.Integer)
    awake = db.Column(db.Boolean)
    ingredients = db.relationship("Ingredient", backref="spall")
    bridges = db.relationship("Spall", secondary=bridges, primaryjoin=(bridges.c.primary == id),
                              secondaryjoin=(bridges.c.secondary == id), backref='spallings')
    guests = db.relationship("User", secondary=guestings, backref="position")

    def __init__(self, name="", con=None):
        if con is None:
            k = conrandom()
        else:
            k = con
        # if Spall.query.filter_by(id=1).first() in self.bridges and k < 3:
        #    k += 2
        self.size = k
        if name == "":
            self.name = f'Spall {randomname.generate("n/").capitalize()}'
            self.nameorig = False
        else:
            self.name = name
            self.nameorig = True
        self.awake = False

    def __repr__(self):
        return f'<Spall "{self.name}" #{self.id}>'

    def connect(self, target):
        self.bridges.append(target)
        target.bridges.append(self)
        db.session.commit()

    def create_neighbor(self):
        nb = Spall()
        db.session.add(nb)
        nb = Spall.query.filter_by().all()[-1]
        self.connect(nb)

    def wake(self):
        while self.size > len(self.bridges):
            sspall = Spall.query.filter_by(awake=False).all()
            if random.randint(1, 20) == 20 and len(sspall) > 1:
                rs1 = random.choice(sspall)
                while rs1 is self:
                    rs1 = random.choice(sspall)
                self.connect(rs1)
            else:
                self.create_neighbor()
        self.awake = True
        if self.size == 1:
            for i in range(5):
                self.roll_for_stuff()
        else:
            for i in range(self.size):
                self.roll_for_stuff()
        db.session.commit()

    def roll_for_stuff(self):
        pro = random.randint(1, 100)
        apple_bar = None
        dungeon = None
        if pro == 100:
            dungeon = Ingredient("big chest")
            apple_bar = IngBar("Apples", random.randint(250, 500) + random.randint(250, 500))
        elif pro == 99:
            dungeon = Ingredient("big tree")
            apple_bar = IngBar("Apples", 250, False, 250)
        elif pro >= 96:
            dungeon = Ingredient("average chest")
            apple_bar = IngBar("Apples", random.randint(50, 100) + random.randint(50, 100))
        elif pro >= 93:
            dungeon = Ingredient("average tree")
            apple_bar = IngBar("Apples", 50, False, 50)
        elif pro >= 85:
            dungeon = Ingredient("small chest")
            apple_bar = IngBar("Apples", random.randint(10, 20) + random.randint(10, 20))
        elif pro >= 77:
            dungeon = Ingredient("small tree")
            apple_bar = IngBar("Apples", 10, False, 10)
        if dungeon is not None:
            dungeon.bars.append(apple_bar)
            db.session.add_all([dungeon, apple_bar])
            dungeon = Ingredient.query.filter_by().all()[-1]
            self.ingredients.append(dungeon)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    move = db.Column(db.String(100))
    bars = db.relationship("PlayerBar", backref="user")
    inventory = db.relationship("Item", backref="user")
    logs = db.Column(db.String(10000))

    def __init__(self, name, password):
        self.name = name
        self.password = password
        self.email = ""
        self.move = ""
        self.logs = '[]'
        lvl = PlayerBar("Level", 1)
        xp = PlayerBar("Experience", 0, False, 20)
        hp = PlayerBar("Health", 20, False, 20)
        self.bars.append(lvl)
        self.bars.append(xp)
        self.bars.append(hp)
        db.session.add_all([lvl, xp, hp])

    def __repr__(self):
        return f'<User {self.name}>'

    def evalxp(self):
        lvl = next(i for i in self.bars if i.name == "Level")
        xp = next(i for i in self.bars if i.name == "Experience")
        hp = next(i for i in self.bars if i.name == "Health")
        while xp.value >= xp.maxx:
            xp.value -= xp.maxx
            lvl.value += 1
            xp.maxx = 10 * 2 ** lvl.value
        while xp.value < 0:
            lvl.value -= 1
            xp.maxx = 10 * 2 ** lvl.value
            xp.value += xp.maxx
        hp.maxx = 15 + lvl.value * 5
        db.session.commit()


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    bars = db.relationship("ItemBar", backref="item")
    person_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __init__(self, name, amount=0):
        self.name = name
        self.amount = amount

    def __repr__(self):
        return f'<Item {self.name} ({self.amount})>'


class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    bars = db.relationship("IngBar", backref="ingredient")
    spall_id = db.Column(db.Integer, db.ForeignKey('spall.id'))

    def __init__(self, tyype, name=""):
        self.type = tyype
        if name == "":
            self.name = randomname.generate("a/") + " " + tyype
            self.name = self.name.capitalize()
        else:
            self.name = name

    def __repr__(self):
        return f'<Ingredient {self.type} "{self.name}">'


class PlayerBar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    value = db.Column(db.Float, nullable=False)
    infinite = db.Column(db.Boolean)
    maxx = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __init__(self, name, value=0, infin=True, maxx=None):
        self.name = name
        self.value = value
        self.infinite = infin
        if not infin:
            self.maxx = maxx

    def __repr__(self):
        if self.infinite:
            return f'<PlayerBar {self.name} ({self.value})>'
        else:
            return f'<PlayerBar {self.name} ({self.value}/{self.maxx})>'


class ItemBar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    value = db.Column(db.Float, nullable=False)
    infinite = db.Column(db.Boolean)
    maxx = db.Column(db.Integer)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)

    def __init__(self, name, value=0, infin=True, maxx=None):
        self.name = name
        self.value = value
        self.infinite = infin
        if not infin:
            self.maxx = maxx

    def __repr__(self):
        return f'<ItemBar {self.name}>'


class IngBar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    value = db.Column(db.Float, nullable=False)
    infinite = db.Column(db.Boolean)
    maxx = db.Column(db.Integer)
    ing_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), nullable=False)

    def __init__(self, name, value=0, infin=True, maxx=None):
        self.name = name
        self.value = value
        self.infinite = infin
        if not infin:
            self.maxx = maxx

    def __repr__(self):
        return f'<IngBar {self.name}>'


def perform_task():
    print(time.ctime())
    with app.app_context():
        spalls = Spall.query.filter_by().all()
        movers = User.query.filter_by().all()
        for spall in spalls:
            for ing in spall.ingredients:
                apples = next(i for i in ing.bars if i.name == "Apples")
                if not apples.infinite:
                    if apples.value < apples.maxx:
                        apples.value += apples.maxx / 100
                        apples.value = round(apples.value, 2)
        for mover in movers:
            bars = mover.bars
            hp = next(i for i in bars if i.name == "Health")
            newlog = ""
            if hp.value < 0:
                newlog = "Owie! You died. That took away the experience you need to get to your curent level. Also you lost all your items."
                for i in mover.inventory:
                    i.amount = 0
                exp = next(i for i in bars if i.name == "Experience")
                exp.value -= exp.maxx / 2
                hp.value += hp.maxx
                move = "died"
            else:
                if hp.value < hp.maxx:
                    hp.value += 1
                move = mover.move
                if move != "":
                    inventory = mover.inventory
                    newlog = "EROWEOWOEOOW"
                    if move[:8] == "use item":
                        use, item, num = move.split(",")
                        num = int(num)
                        item = next(i for i in inventory if i.name == item)
                        if item.amount < num:
                            newlog = f"You don't have enough {item.name}s"
                        # elif num < 0:
                        #    newlog = f"bro poggers go back to math class and try eating {num} apples gl"
                        else:
                            item.amount -= num
                            if item.name == "Apple":
                                addxp = 0
                                if num >= 0:
                                    for i in range(num):
                                        addxp += random.randint(2, 4)
                                else:
                                    for i in range(-num):
                                        addxp -= 4
                                xp = next(i for i in mover.bars if i.name == "Experience")
                                xp.value += addxp
                                newlog = f'You consumed {num} Apple(s) and gained {addxp} xp.'
                            else:
                                newlog = f'You consumed {num} "{item.name}(s)". Why? Nobody knows...'
                    elif move[4:7] == "ing":
                        use_type, ing, ing_id = move.split(",")
                        pos = mover.position[0]
                        ing = next(i for i in pos.ingredients if i.id == int(ing_id))
                        apple_bar = next(i for i in ing.bars if i.name == "Apples")
                        player_apples = None
                        for i in inventory:
                            if i.name == "Apple":
                                player_apples = i
                                break
                        if player_apples is None:
                            player_apples = Item("Apple")
                            inventory.append(player_apples)
                            db.session.add(player_apples)
                        if use_type == "use":
                            if ing.type[-4:] == "tree":
                                lvl = next(i for i in mover.bars if i.name == "Level")
                                change = random.randint(lvl.value, lvl.value * 5)
                                if change > floor(apple_bar.value):
                                    change = floor(apple_bar.value)
                                newlog = f'You harvested apples from the {ing.name} and got {change} Apples'
                                if ing.type[0] == "s":
                                    dif = 1
                                elif ing.type[0] == "a":
                                    dif = 5
                                elif ing.type[0] == "b":
                                    dif = 25
                                else:
                                    dif = 0
                                ra = random.random()
                                if ra > lvl.value / dif:
                                    hp = next(i for i in mover.bars if i.name == "Health")
                                    dmg = random.randint(dif, dif * 5)
                                    hp.value -= dmg
                                    newlog += f', but after that you fell down and lost {dmg} hp'
                                else:
                                    newlog += ", and were lucky (or experienced) enough to climb down graciously"
                            elif ing.type[-5:] == "chest":
                                change = floor(apple_bar.value)
                                newlog = f'You took {change} apples from the {ing.name}'
                            else:
                                change = 0
                        elif use_type == "put":
                            change = -player_apples.amount
                            newlog = f'You put {-change} Apples into the {ing.name}'
                        else:
                            change = 0
                            newlog = f'You interacted with "{ing.name}" and somehow broke it. Good job. Notify me pls'
                        player_apples.amount += change
                        apple_bar.value -= change
                        apple_bar.value = round(apple_bar.value, 2)
                    elif move[:18] == "move to spall no. ":
                        place = move[18:]
                        newwhere = Spall.query.filter_by(id=place).first()
                        now = mover.position[0]
                        if newwhere in now.bridges:
                            now.guests.remove(mover)
                            newwhere.guests.append(mover)
                            if not newwhere.awake:
                                newwhere.wake()
                            newlog = f'You moved from "{now.name}" to "{newwhere.name}"'
                        else:
                            newlog = f"Hey! {now.name} is not connected to {newwhere.name}! Are you trying to cheat?"
                    elif move[:16] == "rename spall to ":
                        newname = move[16:]
                        now = mover.position[0]
                        if not now.nameorig:
                            if 20 > len(newname) > 3:
                                now.name = newname
                                now.nameorig = True
                                db.session.commit()
                                newlog = f'Spall no. {now.id} is now named "{now.name}"!'
                            else:
                                newlog = f'Spall no. {now.id} didnt get renamed"!'

                        else:
                            newlog = f"Hey! {now.name} is a original spall name! Are you trying to cheat?"
                    elif move[:6] == "shout ":
                        text = move[6:]
                        newlog = 'You shouted "%s" to everyone on this spall' % text
                        youhear = f'You hear {mover.name} shout: "%s"' % text
                        print(youhear)
                        youhear = "[" + time.ctime() + "] " + youhear
                        for fellow in mover.position[0].guests:
                            if fellow is not mover:
                                fellog = eval(fellow.logs)
                                fellog.append(youhear)
                                fellow.logs = str(fellog)
                    else:
                        newlog = "error: Unknown move. Your move is " + move
            if move != "":
                newlog = "[" + time.ctime() + "] " + newlog

                loggs = eval(mover.logs)
                loggs.append(newlog)
                if len(loggs) > 50:
                    loggs = loggs[-50:]
                mover.logs = str(loggs)
                mover.move = ""
                mover.evalxp()
            db.session.commit()


def schedule_task():
    while True:
        while floor(time.time()) % minute_length != 0:
            pass
        perform_task()
        time.sleep(minute_length - 1)


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

            found_user = User.query.filter_by(name=request.form["login"]).first()
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
            loggin = request.form["login"]
            password = request.form["password"]
            if password == "" or loggin == "":
                flash("Password or name cannot be empty!", "info")
                return render_template('newacc.html')
            elif password != request.form["password_again"]:
                flash("Passwords do not match!", "info")
                return render_template('newacc.html')
            elif len(loggin) < 3 or len(loggin) > 20:
                flash("Name length should be between 3 and 20 characters!", "info")
                return render_template('newacc.html')
            elif len(password) > 100:
                flash("Password should be no longer than 100 characters!", "info")
                return render_template('newacc.html')
            else:
                found_user = User.query.filter_by(name=loggin).first()

                if found_user:
                    flash("This user already exists! Login or use another username!", "info")
                    return render_template('newacc.html')
                else:
                    usr = User(loggin, password)
                    db.session.add(usr)
                    db.session.commit()
                    spall = Spall.query.filter_by().all()
                    randomspall = random.choice(spall)
                    randomspall.guests.append(usr)
                    randomspall.wake()
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
            user_list = User.query.filter_by().all()
            return render_template('admin.html', listt=user_list, lenn=len(user_list),
                                   spalls=Spall.query.filter_by().all(), spalen=len(Spall.query.filter_by().all()))
        else:
            return redirect(url_for("homepage"))
    else:
        return redirect(url_for("login"))


@app.route('/user', methods=['GET', 'POST'])
def user():
    email = None
    if "login" in session:
        userr = session["login"]
        found_user = User.query.filter_by(name=userr).first()
        if request.method == 'POST':
            if request.form.get("logout") == "logout":
                return redirect(url_for("logout"))
            elif request.form.get("save") == "Save":
                email = request.form["email"]
                session["email"] = email
                found_user.email = email
                db.session.commit()
        else:
            if "email" in session:
                email = session["email"]
        db.session.commit()
        return render_template('user.html', login=userr, email=email)
    else:
        return redirect(url_for("login"))


@app.route('/game', methods=['GET', 'POST'])
def gamepage():
    if "login" in session:

        if request.method == 'POST':
            found_user = User.query.filter_by(name=session["login"]).first()
            if request.form.get("ping") == "Do nothing (default)":
                move = ""
            elif request.form.get("apple") == "Take an apple":
                move = "apple"
            elif request.form.get("cam") == "Chose and move":
                place = request.form["placelist"]
                move = "move to spall no. " + place
            elif request.form.get("sho") == "Shout":
                message = request.form.get("message")
                move = "shout " + message
            elif request.form.get("csn") == "Change spall name":
                newname = request.form.get("newname")
                move = "rename spall to " + newname
            else:
                for item in found_user.inventory:
                    if request.form.get(f"use item {item.name}") == "Use":
                        move = f"use item,{item.name},{request.form[f'numberof {item.name}']}"
                        break
                else:
                    for ing in found_user.position[0].ingredients:
                        if request.form.get(f"use ing {ing.id}") == "Take apples":
                            move = f"use,ing,{ing.id}"
                            break
                    else:
                        for ing in found_user.position[0].ingredients:
                            if request.form.get(f"put ing {ing.id}") == "Put all your apples":
                                move = f"put,ing,{ing.id}"
                                break
                        else:
                            move = "Error: No such move!"
            found_user.move = move
            db.session.commit()
            flash(f'You choose move: "{move}", it will happen soon.', "info")
            return redirect(url_for("gamepage"))
        else:
            userr = session["login"]
            found_user = User.query.filter_by(name=userr).first()
            return render_template('gamebase.html', logs=eval(found_user.logs), user=found_user,
                                   toime=minute_length - (floor(time.time() % minute_length)),
                                   pos=found_user.position[0])
    else:
        return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session.pop("login", None)
    session.pop("email", None)
    return redirect(url_for("homepage"))


thread = threading.Thread(target=schedule_task)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if len(Spall.query.filter_by().all()) == 0:
            zero = Spall(name="Point Alpha", con=8)
            db.session.add(zero)
            db.session.commit()
            zero = Spall.query.filter_by().first()
            zero.wake()
            db.session.commit()
            two_to_8 = Spall.query.filter_by().all()
            for one in two_to_8:
                one.wake()
            db.session.commit()
    thread.start()
    app.run(debug=True, use_reloader=False, host="0.0.0.0")
