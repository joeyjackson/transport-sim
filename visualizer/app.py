from flask import Flask, render_template
import os
from typing import Optional, List, Tuple
import psycopg2
from psycopg2.extensions import connection as pg_connection
from textwrap import dedent

connection: Optional[pg_connection] = None
app = Flask(__name__)


def connect_to_db() -> pg_connection:
  global connection
  if (connection is None):
    connection = psycopg2.connect(host=os.getenv('DB_HOST', 'localhost'),
                          database=os.getenv('DB_DATABASE', 'postgres'),
                          user=os.getenv('APP_DB_USER', 'app'),
                          password=os.getenv('APP_DB_PASSWORD'))
  return connection
  

def close_db_connection() -> None:
  global connection
  if (connection is not None):
    connection.close()
    connection = None


def query(query_str) -> List[Tuple]:
  try:
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute(query_str)
    results = cur.fetchall()
    cur.close()
    return results
  except Exception as e:
    close_db_connection()
    raise e


def get_models():
  return query('SELECT model_id, label, type_id, speed FROM model;')


def get_vehicles():
  return query('SELECT vehicle_id, label, model_id, owner_id FROM vehicle;')


def get_hubs():
  return query('SELECT hub_id, label, posX, posY FROM hub;')


def get_paths():
  return query('SELECT path_id, start_hub_id, end_hub_id FROM path;')


def get_movements():
  return query('SELECT movement_id, ts, vehicle_id, path_id FROM movement;')


def get_inconsistencies():
  return query('SELECT movement_id, vehicle_id, ts, inconsistency_type FROM movement_inconsistencies;')


def get_movements_with_arrival_info():
  return query(dedent('''
    SELECT 
      m.ts, 
      v.label, 
      mdl.speed,
      shub.posX AS startX, 
      shub.posY AS startX, 
      ehub.posX AS endX, 
      ehub.posY AS endY, 
      m.path_time,
      v.vehicle_id
    FROM movement_with_arrival m
    JOIN vehicle v ON m.vehicle_id = v.vehicle_id
    JOIN path p ON m.path_id = p.path_id
    JOIN hub shub ON p.start_hub_id = shub.hub_id
    JOIN hub ehub ON p.end_hub_id = ehub.hub_id
    JOIN model mdl on v.model_id = mdl.model_id;
  '''))


@app.route('/')
def index():
  return render_template('index.html')


@app.route('/api/movements')
def movements():
  return {
    "data": [
      {
        "timestamp": result[0], 
        "vehicle": result[1], 
        "vehicle_id": result[8], 
        "speed": result[2], 
        "startPos": {
          "x": result[3], 
          "y": result[4], 
        },
        "endPos": {
          "x": result[5], 
          "y": result[6], 
        },
        "path_time": result[7],
      } 
      for result in get_movements_with_arrival_info()
    ]
  }

@app.route('/api/hubs')
def hubs():
  return {
    "data": [
      {
        "hub_id": result[0],
        "label": result[1], 
        "pos": {
          "x": result[2], 
          "y": result[3]
        }
      }
      for result in get_hubs()
    ]
  }

@app.route('/api/inconsistencies')
def inconsistencies():
  return {
    "data": [
      {
        "movement_id": result[0],
        "vehicle_id": result[1], 
        "timestamp": result[2],
        "inconsistency_type": result[3]
      }
      for result in get_inconsistencies()
    ]
  }


if __name__ == "__main__":
  try:
    app.run(debug=True)
  finally:
    close_db_connection()
