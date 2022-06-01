from flask import Flask, render_template
import os
from typing import Optional
import psycopg2
from psycopg2.extensions import connection as pg_connection

connection: Optional[pg_connection] = None
app = Flask(__name__)


def connect_to_db() -> pg_connection:
  global connection
  if (connection is None):
    connection = psycopg2.connect(host=os.getenv('DB_HOST', 'localhost'),
                          database=os.getenv('DB_DATABASE', 'postgres'),
                          user=os.getenv('DB_USERNAME', 'postgres'),
                          password=os.getenv('DB_PASSWORD'))
  return connection
  

def close_db_connection() -> None:
  global connection
  if (connection is not None):
    connection.close()
    connection = None


def query(query_str):
  conn = connect_to_db()
  cur = conn.cursor()
  cur.execute(query_str)
  results = cur.fetchall()
  cur.close()
  return results


def get_models():
  return query('SELECT model_id, label, type_id, speed FROM model;')


def get_vehicles():
  return query('SELECT vehicle_id, label, model_id, owner_id FROM vehicle;')


def get_hubs():
  return query('SELECT hub_id, label, posX, posY FROM hub;')


def get_paths():
  return query('SELECT path_id, start_hub_id, end_hub_id FROM path;')


def get_movements():
  return query('SELECT movement_id, timestamp, vehicle_id, path_id FROM movement;')


@app.route('/')
def index():
  return render_template(
    'index.html', 
    models=get_models(), 
    vehicles=get_vehicles(), 
    hubs=get_hubs(), 
    paths=get_paths(), 
    movements=get_movements()
  )


if __name__ == "__main__":
  try:
    app.run(debug=True)
  finally:
    close_db_connection()
