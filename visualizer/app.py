from flask import Flask, render_template
import os
import psycopg2

def get_db_connection():
  pwd = os.getenv('DB_PASSWORD')
  conn = psycopg2.connect(host=os.getenv('DB_HOST', 'localhost'),
                          database=os.getenv('DB_DATABASE', 'postgres'),
                          user=os.getenv('DB_USERNAME', 'postgres'),
                          password=pwd)
  return conn

app = Flask(__name__)

@app.route("/hello")
def hello_world():
  return "<p>Hello, World!</p>"

@app.route('/')
def index():
  conn = get_db_connection()
  cur = conn.cursor()
  cur.execute('SELECT value1, value2, add, sub, mult, div, pow FROM math_facts;')
  results = cur.fetchall()
  cur.close()
  conn.close()
  return render_template('index.html', results=results)

if __name__ == "__main__":
  app.run(debug=True)