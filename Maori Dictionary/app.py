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


@app.route('/')
def render_homepage():
    con = create_connection(DB_NAME)

    query = "SELECT id, name, description FROM category"

    cur = con.cursor()
    cur.execute(query)
    found_categories = cur.fetchall()
    con.close()

    return render_template('home.html', category_list=found_categories)


app.run(host='0.0.0.0', debug=True)