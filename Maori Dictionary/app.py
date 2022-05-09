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


def fetch_user_data(user):
    con = create_connection(DB_NAME)

    # Grab category data at the passed category
    query = """SELECT id, username, teacher FROM user WHERE id = ?"""
    cur = con.cursor()
    cur.execute(query, (user,))
    fetched_user = cur.fetchall()

    if len(fetched_user) > 0:
        return fetched_user[0]
    else:
        return False


def my_account():
    if session.get('userid') is None:
        return False
    else:
        return session.get('userid')


def is_logged_in():
    if session.get('email') is None:
        print('Not logged in')
        return False
    else:
        print('Logged in')
        return True


def is_teacher():
    if not is_logged_in() or (session.get('teacher') is None or 0):
        print('Not teacher')
        return False
    else:
        print('Is teacher')
        return True


@app.route('/')
def render_homepage():
    return render_template('home.html', category_list=find_categories(), logged_in=is_logged_in(),
                           user_account=my_account(), teacher=is_teacher())


@app.route('/about')
def render_about_page():
    return render_template('about.html', category_list=find_categories(), logged_in=is_logged_in(),
                           user_account=my_account(), teacher=is_teacher())


@app.route('/contributions')
def render_contributions_page():
    return render_template('contributions.html', category_list=find_categories(), logged_in=is_logged_in(),
                           user_account=my_account(), teacher=is_teacher())


@app.route('/login', methods=['GET', 'POST'])
def render_login_page():
    if is_logged_in():
        return redirect('/?error=Already+logged+in')

    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['pass1'].strip()

        query = """SELECT id, username, password, teacher FROM user WHERE email = ?"""
        con = create_connection(DB_NAME)
        cur = con.cursor()
        cur.execute(query, (email,))
        user_data = cur.fetchall()
        con.close()

        try:
            userid = user_data[0][0]
            username = user_data[0][1]
            db_password = user_data[0][2]
            teacher_status = user_data[0][3]
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
        session['teacher'] = teacher_status
        print(session)
        return redirect('/')

    return render_template('login.html', category_list=find_categories(), logged_in=is_logged_in(),
                           user_account=my_account(), teacher=is_teacher())


@app.route('/account/<user>')
def account(user):
    current_user = fetch_user_data(user)
    if current_user is False:
        return redirect('/?error=Account+unavailable')

    return render_template('account.html', category_list=find_categories(), logged_in=is_logged_in(),
                           user_account=my_account(), user_data=current_user, teacher=is_teacher())


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
        teacher = request.form.get('teacher')

        # Check passwords
        if pass1 != pass2:
            return redirect('/signup?error=Passwords+dont+match')

        if len(pass1) < 8:
            return redirect('/signup?error=Passwords+must+be+8+characters+or+more')

        # Hash Password
        hashed_pass = bcrypt.generate_password_hash(pass1)

        # Connect to DB
        con = create_connection(DB_NAME)

        query = "INSERT INTO user(id, username, email, password, teacher) VALUES(NULL,?,?,?,?)"

        # Execute query
        cur = con.cursor()
        try:
            cur.execute(query, (username, email, hashed_pass, teacher))
        except sqlite3.IntegrityError:
            return redirect('/signup?error=Email+is+already+used')
        con.commit()
        con.close()

        return redirect('login')

    return render_template('signup.html', category_list=find_categories(), logged_in=is_logged_in(),
                           user_account=my_account(), teacher=is_teacher())


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
                           category_list=find_categories(), from_category=cat, logged_in=is_logged_in(),
                           user_account=my_account(), teacher=is_teacher())


@app.route('/word/<word>')
def render_word_page(word):
    con = create_connection(DB_NAME)

    # Grab category data at the passed category
    query = """SELECT * FROM word WHERE id = ?"""
    cur = con.cursor()
    cur.execute(query, (word,))
    word_data = cur.fetchall()

    con.close()

    return render_template('word.html', passed_word=word_data, category_list=find_categories(),
                           logged_in=is_logged_in(), user_account=my_account(), teacher=is_teacher())


@app.route('/remove_word/<word>')
def render_word_remove_page(word):
    if not is_logged_in():
        return redirect('/?error=Not+logged+in')

    if not is_teacher():
        return redirect('/?error=No+permission')

    con = create_connection(DB_NAME)

    query = "DELETE FROM word WHERE id=?"
    cur = con.cursor()

    cur.execute(query, (word,))

    con.commit()

    query = "DELETE FROM word_tag WHERE word_id=?"
    cur = con.cursor()

    cur.execute(query, (word,))

    con.commit()
    con.close()

    return redirect('/')


@app.route('/remove_category/<cat>')
def render_category_remove_page(cat):
    if not is_logged_in():
        return redirect('/?error=Not+logged+in')

    if not is_teacher():
        return redirect('/?error=No+permission')

    con = create_connection(DB_NAME)

    query = "SELECT user_created FROM category WHERE id=?"
    cur = con.cursor()

    cur.execute(query, (cat, ))
    created_by_user = cur.fetchall()

    if created_by_user[0][0]:
        query = "DELETE FROM category WHERE id=?"
        cur = con.cursor()

        cur.execute(query, (cat,))

        con.commit()
        con.close()
    else:
        return redirect('/?error=No+permission')

    return redirect('/')


@app.route('/add_word', methods=['GET', 'POST'])
def render_add_word_page():
    if not is_logged_in():
        return redirect('/?error=Not+logged+in')

    if not is_teacher():
        return redirect('/?error=No+permission')

    if request.method == "POST":
        word_name = request.form['word_name'].strip()
        word_maori = request.form['word_maori'].strip()
        word_desc = request.form['word_desc'].strip()
        cat_id = request.form['category'].strip()

        word_level = max(0, min(10, int(request.form['word_level'])))

        userid = session['userid']
        timestamp = datetime.now()

        print(f"User {userid} would like to add {word_name} to {cat_id} at {timestamp}")

        con = create_connection(DB_NAME)

        # FIND IF WORD ALREADY EXISTS
        query = """SELECT name FROM word"""
        cur = con.cursor()
        cur.execute(query)

        con.commit()

        word_data = cur.fetchall()

        for find_word in word_data:
            if find_word[0].strip().lower() == word_name.strip().lower():
                return redirect('/?error=Word+already+exists+in+database')

        query = "INSERT INTO word(id,name,description,author,timestamp,maori,level) VALUES (NULL,?,?,?,?,?,?)"
        cur = con.cursor()

        # Catch insertion errors
        cur.execute(query, (word_name, word_desc, userid, timestamp, word_maori, word_level))

        con.commit()

        query = "SELECT id FROM word ORDER BY id DESC"
        cur = con.cursor()
        cur.execute(query)

        list_of_ids = cur.fetchall()
        print(list_of_ids)

        latest_id = list_of_ids[0][0]

        # Add word to word tag
        query = """INSERT INTO word_tag(word_id, category_id) VALUES (?,?)"""
        cur = con.cursor()

        cur.execute(query, (latest_id, cat_id))

        con.commit()
        con.close()

        return redirect('/')

    return render_template('add_word.html', category_list=find_categories(), logged_in=is_logged_in(),
                           user_account=my_account(), teacher=is_teacher())


@app.route('/add_category', methods=['GET', 'POST'])
def render_add_category_page():
    if not is_logged_in():
        return redirect('/?error=Not+logged+in')

    if not is_teacher():
        return redirect('/?error=No+permission')

    if request.method == "POST":
        cat_name = request.form['word_name'].strip()
        cat_desc = request.form['word_desc'].strip()

        userid = session['userid']
        timestamp = datetime.now()

        con = create_connection(DB_NAME)

        # FIND IF WORD ALREADY EXISTS
        query = """SELECT name FROM category"""
        cur = con.cursor()
        cur.execute(query)

        con.commit()

        cat_data = cur.fetchall()
        c_id = len(cat_data) + 1

        for find_cat in cat_data:
            if find_cat[0].strip().lower() == cat_name.strip().lower():
                return redirect('/?error=Category+already+exists+in+database')

        query = "INSERT INTO category(id,name,description,timestamp,user_created) VALUES (NULL,?,?,?,?)"
        cur = con.cursor()

        # Catch insertion errors
        cur.execute(query, (cat_name, cat_desc, timestamp, 1))

        con.commit()
        con.close()

        return redirect('/')

    return render_template('add_category.html', category_list=find_categories(), logged_in=is_logged_in(),
                           user_account=my_account(), teacher=is_teacher())


app.run(host='0.0.0.0', debug=True)
