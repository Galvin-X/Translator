from flask import Flask, render_template, request, session, redirect
import sqlite3
from sqlite3 import Error
from datetime import datetime

DB_NAME = "dictionary.db"

app = Flask(__name__)
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


@app.route('/')
def render_homepage():
    return render_template('home.html', category_list=find_categories())


@app.route('/about')
def render_about_page():
    return render_template('about.html', category_list=find_categories())


@app.route('/contributions')
def render_contributions_page():
    return render_template('contributions.html', category_list=find_categories())


@app.route('/login')
def render_login_page():
    return render_template('login.html', category_list=find_categories())


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
                           category_list=find_categories(), from_category=cat)


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
                           category_list=find_categories())


app.run(host='0.0.0.0', debug=True)
