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
    """
    Creates a connection to the database.
    """

    try:
        connection = sqlite3.connect(db_file)
        connection.execute('pragma foreign_keys=ON')
        return connection
    except Error as e:
        print(e)

    return None


def find_categories():
    """
    Returns list of queried categories.
    """

    con = create_connection(DB_NAME)

    query = "SELECT id, name, description FROM category"

    cur = con.cursor()
    cur.execute(query)
    found_categories = cur.fetchall()
    con.close()

    # print(found_categories)

    return found_categories


def fetch_user_data(user):
    """
    Returns user data from a passed in user.
    """

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
    """
    Returns the user's id if they're logged in.
    """

    if session.get('userid') is None:
        return False
    else:
        return session.get('userid')


def is_logged_in():
    """
    Returns whether the current user is logged in.
    """

    if session.get('email') is None:
        print('Not logged in')
        return False
    else:
        print('Logged in')
        return True


def is_teacher():
    """
    Returns whether the logged in user has teacher permissions or not.
    """

    if not is_logged_in() or (session.get('teacher') is None or 0):
        print('Not teacher')
        return False
    else:
        print('Is teacher')
        return True


@app.route('/')
def render_homepage():
    # Show home page
    return render_template('home.html', category_list=find_categories(), logged_in=is_logged_in(),
                           user_account=my_account(), teacher=is_teacher())


@app.route('/about')
def render_about_page():
    # Show about page
    return render_template('about.html', category_list=find_categories(), logged_in=is_logged_in(),
                           user_account=my_account(), teacher=is_teacher())


@app.route('/contributions')
def render_contributions_page():
    # Connect to database
    con = create_connection(DB_NAME)

    # Get 10 of the most recently added / edited words
    query = "SELECT * FROM word ORDER BY timestamp DESC LIMIT 10"

    cur = con.cursor()
    cur.execute(query)

    queried_words = cur.fetchall()

    # Close connection
    con.close()

    print(queried_words)

    return render_template('contributions.html', category_list=find_categories(), logged_in=is_logged_in(),
                           user_account=my_account(), teacher=is_teacher(), contribution_list=queried_words)


@app.route('/login', methods=['GET', 'POST'])
def render_login_page():
    # Ensure user isn't already logged in
    if is_logged_in():
        return redirect('/?error=Already+logged+in')

    # User is attempting to log in
    if request.method == 'POST':
        # Get data from form
        email = request.form['email'].strip().lower()
        password = request.form['pass1'].strip()

        # Connect to database
        con = create_connection(DB_NAME)

        # Find user data using the entered email for reference
        query = """SELECT id, username, password, teacher FROM user WHERE email = ?"""
        cur = con.cursor()

        # Store user data
        cur.execute(query, (email,))
        user_data = cur.fetchall()

        # Close connection
        con.close()

        # Attempt to log in
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

        # Setup user's session data
        session['email'] = email
        session['userid'] = userid
        session['username'] = username
        session['teacher'] = teacher_status
        print(session)

        # Redirect to home page
        return redirect('/')

    return render_template('login.html', category_list=find_categories(), logged_in=is_logged_in(),
                           user_account=my_account(), teacher=is_teacher())


@app.route('/account/<user>')
def account(user):
    # Display account page of passed user
    current_user = fetch_user_data(user)

    # Account doesnt exist - catch error
    if current_user is False:
        return redirect('/?error=Account+unavailable')

    # Connect to database and grab the user's authored words
    con = create_connection(DB_NAME)
    query = "SELECT * FROM word WHERE author=? ORDER BY timestamp DESC LIMIT 10 "

    cur = con.cursor()
    cur.execute(query, (user,))

    # Store authored words in a new variable
    queried_words = cur.fetchall()

    print(queried_words)
    # Close database connection
    con.close()

    return render_template('account.html', category_list=find_categories(), logged_in=is_logged_in(),
                           user_account=my_account(), contribution_list=queried_words,
                           user_data=current_user, teacher=is_teacher())


@app.route('/logout')
def logout():
    # Pop session data - log out
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))

    # Show logout message
    return redirect('/?message=See+you+next+time!')


@app.route('/signup', methods=['GET', 'POST'])
def render_signup_page():
    # Ensure user isn't logged in
    if is_logged_in():
        return redirect('/?error=Already+logged+in')

    # Post form
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

        # Make sure it has appropriate length
        if len(pass1) < 8:
            return redirect('/signup?error=Passwords+must+be+8+characters+or+more')

        # Hash Password
        hashed_pass = bcrypt.generate_password_hash(pass1)

        # Connect to database
        con = create_connection(DB_NAME)

        query = "INSERT INTO user(id, username, email, password, teacher) VALUES(NULL,?,?,?,?)"
        cur = con.cursor()

        # Execute query
        try:
            cur.execute(query, (username, email, hashed_pass, teacher))
        except sqlite3.IntegrityError:
            # Email has been used already
            return redirect('/signup?error=Email+is+already+used')

        # Commit and close database connection
        con.commit()
        con.close()

        # Redirect to login page
        return redirect('login')

    return render_template('signup.html', category_list=find_categories(), logged_in=is_logged_in(),
                           user_account=my_account(), teacher=is_teacher())


@app.route('/category/<cat>')
def render_category_page(cat):
    # Connect to database
    con = create_connection(DB_NAME)

    # Grab category data at the passed category
    query = """SELECT id, name, description, timestamp, user_created FROM category WHERE id = ?"""
    cur = con.cursor()
    cur.execute(query, (cat,))

    category_data = cur.fetchall()

    print(category_data)

    # Category doesn't exist - prevent error
    if not category_data:
        return redirect('/?error=No+such+category')

    # print(category_data)

    # Find words that meet the requirements (word ids in the word_tag table with the category_id of <cat>
    query = """SELECT word_id FROM word_tag WHERE category_id = ?"""
    cur = con.cursor()
    cur.execute(query, (cat,))
    found_words = cur.fetchall()

    # Dump table
    words_data = []

    # Access word table by referencing the found words from the word_tag table, append into dump table
    for w in found_words:
        cur = con.cursor()
        cur.execute("""SELECT id, name, maori, description, author, timestamp FROM word WHERE id = ?""", w)
        words_data.append(cur.fetchall())

    # Print words for debug + close connection to database
    print(words_data)
    con.close()

    return render_template('category.html', word_list=words_data, passed_cat=category_data,
                           category_list=find_categories(), from_category=cat, logged_in=is_logged_in(),
                           user_account=my_account(), teacher=is_teacher())


@app.route('/word/<word>', methods=["POST", "GET"])
def render_word_page(word):
    # Connect to database
    con = create_connection(DB_NAME)

    # Grab word data at the passed word id
    query = "SELECT * FROM word WHERE id=?"
    cur = con.cursor()
    cur.execute(query, (word,))
    word_data = cur.fetchall()

    # Run this code if form is being submitted
    if request.method == "POST":
        # Ensure user has appropriate permission
        if not is_logged_in():
            return redirect('/?error=Not+logged+in')

        if not is_teacher():
            return redirect('/?error=No+permission')

        # Post form
        if request.method == "POST":
            # Get data from form
            word_name = request.form['word_name'].strip()
            word_maori = request.form['word_maori'].strip()
            word_desc = request.form['word_desc'].strip()

            word_level = max(0, min(10, int(request.form['word_level'])))

            userid = session['userid']
            timestamp = datetime.now()

            # Only update if value has been changed
            if (word_name != word_data[0][1]) or (word_maori != word_data[0][5]) \
                    or (word_desc != word_data[0][2]) or (word_level != word_data[0][7]):
                # Update word
                query = "UPDATE word SET name=?,description=?,author=?,timestamp=?,maori=?,level=? WHERE id=?"
                cur = con.cursor()

                # Catch insertion errors
                cur.execute(query, (word_name, word_desc, userid, timestamp, word_maori, word_level, word))

                # Commit to database
                con.commit()

            # Close database connection
            con.close()

            # Redirect
            return redirect('/word/' + str(word))
    else:
        # Ensure word exists
        if not word_data:
            return redirect('/?error=No+such+word')

        # Get the id of the user who edited / created this word
        user_id = word_data[0][3]

        # Get all of the data
        query = "SELECT * FROM user WHERE id=?"
        cur = con.cursor()
        cur.execute(query, (user_id,))
        users = cur.fetchall()

        # Close connection
        con.close()

    return render_template('word.html', passed_word=word_data, category_list=find_categories(),
                           logged_in=is_logged_in(), user_account=my_account(), teacher=is_teacher(), user_data=users)


@app.route('/remove_word/<word>')
def render_word_remove_page(word):
    # Ensure user has appropriate permission
    if not is_logged_in():
        return redirect('/?error=Not+logged+in')

    if not is_teacher():
        return redirect('/?error=No+permission')

    # Create connection to database
    con = create_connection(DB_NAME)

    # Delete word from the word table at <word>
    query = "DELETE FROM word WHERE id=?"
    cur = con.cursor()

    cur.execute(query, (word,))

    # Commit word deletion
    con.commit()

    # Delete word tag
    query = "DELETE FROM word_tag WHERE word_id=?"
    cur = con.cursor()

    cur.execute(query, (word,))

    # Commit changes and close database
    con.commit()
    con.close()

    return redirect('/')


@app.route('/remove_category/<cat>')
def render_category_remove_page(cat):
    # Ensure user has appropriate permission
    if not is_logged_in():
        return redirect('/?error=Not+logged+in')

    if not is_teacher():
        return redirect('/?error=No+permission')

    # Connect to database
    con = create_connection(DB_NAME)

    # Ensures the selected category has been created by a user
    query = "SELECT user_created FROM category WHERE id=?"
    cur = con.cursor()

    cur.execute(query, (cat,))
    created_by_user = cur.fetchall()

    # If the query returns nothing, this category must not exist
    if not created_by_user:
        return redirect('/?error=No+such+category')

    # (if created_by_user[0][0] == True), Display the remove category page
    if created_by_user[0][0]:
        # Grab category data at the passed category
        query = """SELECT id, name, description, timestamp, user_created FROM category WHERE id = ?"""
        cur = con.cursor()
        cur.execute(query, (cat,))
        category_data = cur.fetchall()

        # Find words that meet the requirements (word ids in the word_tag table with the category_id of <cat>
        query = "SELECT word_id FROM word_tag WHERE category_id=?"
        cur = con.cursor()

        cur.execute(query, (cat,))
        found_words = cur.fetchall()

        # Create dump table to insert all of the word data into
        words_data = []

        # Access word table by referencing the found words from the word_tag table, append into new list
        for w in found_words:
            cur = con.cursor()
            cur.execute("SELECT id, name, maori, description, author, timestamp FROM word WHERE id=?", w)

            # Add data to dump table
            words_data.append(cur.fetchall())

        # Print words for debug + close connection to database
        print(words_data)
        con.close()

        return render_template('remove_category.html', category_list=find_categories(), logged_in=is_logged_in(),
                               user_account=my_account(), teacher=is_teacher(), word_list=words_data,
                               passed_cat=category_data)
    else:
        # User has no permission - close connection and redirect
        con.close()
        return redirect('/?error=No+permission')

    return redirect('/')


@app.route('/confirm_remove_category/<cat>')
def render_confirm_category_remove_page(cat):
    # Ensure user has appropriate permission
    if not is_logged_in():
        return redirect('/?error=Not+logged+in')

    if not is_teacher():
        return redirect('/?error=No+permission')

    # Connect to database
    con = create_connection(DB_NAME)

    # Ensures the selected category has been created by a user
    query = "SELECT user_created FROM category WHERE id=?"
    cur = con.cursor()

    cur.execute(query, (cat,))
    created_by_user = cur.fetchall()

    # If the query returns nothing, this category must not exist
    if not created_by_user:
        return redirect('/?error=No+such+category')

    # (if created_by_user[0][0] == True), Remove the category
    if created_by_user[0][0]:
        query = "DELETE FROM category WHERE id=?"
        cur = con.cursor()

        cur.execute(query, (cat,))

        # Commit and close the database connection
        con.commit()
        con.close()
    else:
        # Category isn't a user-created one, so the user has no permission to remove it.
        con.close()
        return redirect('/?error=No+permission')

    return redirect('/')


@app.route('/add_word', methods=['GET', 'POST'])
def render_add_word_page():
    # Ensure user has appropriate permission
    if not is_logged_in():
        return redirect('/?error=Not+logged+in')

    if not is_teacher():
        return redirect('/?error=No+permission')

    # Only run this code if the form is being posted
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

        # Get list of word names
        query = "SELECT name FROM word"
        cur = con.cursor()
        cur.execute(query)

        word_data = cur.fetchall()

        # Check if word being inserted already exists in the word table
        for find_word in word_data:
            if find_word[0].strip().lower() == word_name.strip().lower():
                return redirect('/?error=Word+already+exists+in+database')

        # Build query for inserting the new word into the word table
        query = "INSERT INTO word(id,name,description,author,timestamp,maori,level,image) VALUES (NULL,?,?,?,?,?,?,?)"
        cur = con.cursor()

        # Insert
        cur.execute(query, (word_name, word_desc, userid, timestamp, word_maori, word_level, "noimage.png"))

        # Commit to database
        con.commit()

        # Get list of word ids from the word table
        query = "SELECT id FROM word ORDER BY id DESC"
        cur = con.cursor()
        cur.execute(query)

        list_of_ids = cur.fetchall()
        print(list_of_ids)

        # Latest word id
        latest_id = list_of_ids[0][0]

        # Add word to word tag
        query = """INSERT INTO word_tag(word_id, category_id) VALUES (?,?)"""
        cur = con.cursor()

        cur.execute(query, (latest_id, cat_id))

        # Commit and close the database connection
        con.commit()
        con.close()

        return redirect('/')

    return render_template('add_word.html', category_list=find_categories(), logged_in=is_logged_in(),
                           user_account=my_account(), teacher=is_teacher())


@app.route('/add_category', methods=['GET', 'POST'])
def render_add_category_page():
    # Ensure user has appropriate permission
    if not is_logged_in():
        return redirect('/?error=Not+logged+in')

    if not is_teacher():
        return redirect('/?error=No+permission')

    # Only run this code if the form is being posted
    if request.method == "POST":
        # Get data from the form
        cat_name = request.form['word_name'].strip()
        cat_desc = request.form['word_desc'].strip()

        userid = session['userid']
        timestamp = datetime.now()

        # Connect to database
        con = create_connection(DB_NAME)

        # Build query for inserting the new category into the categories table
        query = "INSERT INTO category(id,name,description,timestamp,user_created) VALUES (NULL,?,?,?,?)"
        cur = con.cursor()

        # Catch insertion errors
        try:
            # Try to insert into the category
            cur.execute(query, (cat_name, cat_desc, timestamp, 1))

            # Commit and close the database connection
            con.commit()
            con.close()

            # Redirect to the homepage
            return redirect('/')
        except sqlite3.IntegrityError:

            # Something has gone wrong, close database connection and try again
            con.commit()
            con.close()

    return render_template('add_category.html', category_list=find_categories(), logged_in=is_logged_in(),
                           user_account=my_account(), teacher=is_teacher())


app.run(host='0.0.0.0', debug=True)
