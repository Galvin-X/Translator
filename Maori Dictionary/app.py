from flask import Flask, render_template, request, session, redirect
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from datetime import datetime

DB_NAME = "dictionary.db"

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "@*#(!HbJ@#LKJyl,!@#*aSDd**)sHdgsC^ExA&^*@#L!@#uiyoy:EWzA)R(_IAO:SD<?xiVqH{}#@$)_#(@)_IqI!"


def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        connection.execute('pragma foreign_keys=ON')
        return connection
    except Error as e:
        print(e)

    return None


def find_categories():
    con = create_connection(DB_NAME)

    query = "SELECT id, name, description FROM category"

    cur = con.cursor()
    cur.execute(query)
    found_categories = cur.fetchall()
    con.close()

    # print(found_categories)

    return found_categories


def is_logged_in():
    if session.get("email") is None:
        print("Not logged in")
        return False
    else:
        print("Logged in")
        return True


@app.route('/')
def render_homepage():
    return render_template('home.html', category_list=find_categories(), logged_in=is_logged_in())


@app.route('/about')
def render_about_page():
    return render_template('about.html', category_list=find_categories(), logged_in=is_logged_in())


@app.route('/contributions')
def render_contributions_page():
    return render_template('contributions.html', category_list=find_categories(), logged_in=is_logged_in())


@app.route('/login', methods=['GET', 'POST'])
def render_login_page():
    if is_logged_in():
        return redirect('/?error=Already+logged+in')

    if request.method == "POST":
        email = request.form['email'].strip().lower()
        password = request.form['pass1'].strip()

        query = """SELECT id, username, password FROM user WHERE email = ?"""
        con = create_connection(DB_NAME)
        cur = con.cursor()
        cur.execute(query, (email,))
        user_data = cur.fetchall()
        con.close()

        try:
            userid = user_data[0][0]
            username = user_data[0][1]
            db_password = user_data[0][2]
        except IndexError:
            return redirect('/login?error=Email+or+password+incorrect')

        # Check hashed password against entered password

        if not bcrypt.check_password_hash(db_password, password):
            return redirect(request.referrer + '?error=Email+or+password+incorrect')

        #   if db_password != pass1:
        #    return redirect('/login?error=Email+or+password+incorrect')

        session['email'] = email
        session['userid'] = userid
        session['username'] = username
        print(session)
        return redirect('/')

    return render_template('login.html', category_list=find_categories(), logged_in=is_logged_in())


@app.route('/account')
def account():
    if not is_logged_in():
        return redirect('/?error=Not+logged+in')

    return render_template('home.html', category_list=find_categories(), logged_in=is_logged_in())


@app.route('/logout')
def logout():
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect('/?message=See+you+next+time!')


@app.route('/signup', methods=['GET', 'POST'])
def render_signup_page():
    if is_logged_in():
        return redirect('/?error=Already+logged+in')

    if request.method == "POST":
        # Show form in console
        print(request.form)

        # Get data
        username = request.form.get('username').strip().title()
        email = request.form.get('email').strip().lower()
        pass1 = request.form.get('pass1')
        pass2 = request.form.get('pass2')

        # Check passwords
        if pass1 != pass2:
            return redirect('/signup?error=Passwords+dont+match')

        if len(pass1) < 8:
            return redirect('/signup?error=Passwords+must+be+8+characters+or+more')

        # Hash Password
        hashed_pass = bcrypt.generate_password_hash(pass1)

        # Connect to DB
        con = create_connection(DB_NAME)

        query = "INSERT INTO user(id, username, email, password) VALUES(NULL,?,?,?)"

        # Execute query
        cur = con.cursor()
        try:
            cur.execute(query, (username, email, hashed_pass))
        except sqlite3.IntegrityError:
            return redirect('/signup?error=Email+is+already+used')
        con.commit()
        con.close()

        return redirect('login')

    return render_template('signup.html', category_list=find_categories(), logged_in=is_logged_in())


@app.route('/category/<cat>')
def render_category_page(cat):
    con = create_connection(DB_NAME)

    # Grab category data at the passed category
    query = """SELECT id, name, description FROM category WHERE id = ?"""
    cur = con.cursor()
    cur.execute(query, (cat,))
    category_data = cur.fetchall()

    # print(category_data)

    # Find words that meet the requirements (word ids in the word_tag table with the category_id of <cat>
    query = """SELECT word_id FROM word_tag WHERE category_id = ?"""
    cur = con.cursor()
    cur.execute(query, (cat,))
    found_words = cur.fetchall()

    words_data = []

    # Access word table by referencing the found words from the word_tag table, append into new list
    for w in found_words:
        cur = con.cursor()
        cur.execute("""SELECT id, name, description, author, timestamp FROM word WHERE id = ?""", w)
        words_data.append(cur.fetchall())

    # Print words for debug + close connection to database
    print(words_data)
    con.close()

    return render_template('category.html', word_list=words_data, passed_cat=category_data,
                           category_list=find_categories(), from_category=cat, logged_in=is_logged_in())


@app.route('/word/<word>')
def render_word_page(word):
    con = create_connection(DB_NAME)

    # Grab category data at the passed category
    query = """SELECT id, name, description FROM word WHERE id = ?"""
    cur = con.cursor()
    cur.execute(query, (word,))
    word_data = cur.fetchall()

    con.close()

    return render_template('word.html', passed_word=word_data,
                           category_list=find_categories(), logged_in=is_logged_in())


app.run(host='0.0.0.0', debug=True)
