import psycopg2
from psycopg2.extensions import connection as pg_connection, cursor as pg_cursor
import os
from typing import Iterable, Optional, List
import logging
import argparse
import textwrap
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

parser = argparse.ArgumentParser()
parser.add_argument("-log", "--log", 
  default="WARNING", 
  help=("Provide logging level: CRITICAL, ERROR, WARNING, INFO DEBUG. default=WARNING"),
)
options = parser.parse_args()
numeric_level = getattr(logging, options.log.upper(), None)
if not isinstance(numeric_level, int):
  raise ValueError('Invalid log level: %s' % options.log.upper())
logging.basicConfig(level=numeric_level)

logger = logging.getLogger(__name__)

connection: Optional[pg_connection] = None


def connect_to_db() -> pg_connection:
  global connection
  if (connection is None):
    connection = psycopg2.connect(host='localhost',
                                  database=os.getenv('DB_DATABASE'),
                                  user=os.getenv('DB_USERNAME'),
                                  password=os.getenv('DB_PASSWORD'))
  return connection


def close_db_connection() -> None:
  global connection
  if (connection is not None):
    connection.close()
    connection = None


def query(q: str, params: Iterable = []) -> pg_cursor:
  try:
    connection = connect_to_db()
    _query = textwrap.dedent(q).strip()
    logger.debug('Executing query: %s %s', _query, params)
    cur = connection.cursor()
    cur.execute(_query, params)
    return cur
  except Exception as e:
    raise Exception('Error executing query: {} {}\ncaused by: {}'.format(q, params, e)) from e


class ColumnDefinition():
  def __init__(self, name: str, data_type: str, constraints: List[str] = []):
    self.name = name
    self.data_type = data_type
    self.constraint = constraints

  def __str__(self):
    constraints = "".join([f" {c}" for c in self.constraint])
    return f"{self.name} {self.data_type}{constraints}"


class BaseTable():
  def table_name(self) -> str:
    raise Exception('not implemented')

  def _columns(self) -> List[ColumnDefinition]:
    raise Exception('not implemented')

  def _ddl_clauses(self) -> List[str]:
    return []
  
  def _schema(self) -> str:
    columns = [str(c) for c in self._columns()]
    clauses = self._ddl_clauses()
    lines = ",\n        ".join(columns + clauses)
    return textwrap.dedent(f"""
      CREATE TABLE IF NOT EXISTS {self.table_name()} (
        {lines}
      );
    """).strip()

  def _create_table(self) -> None:
    connection = connect_to_db()
    query = self._schema()
    logger.debug('Executing query: %s', query)
    cur = connection.cursor()
    cur.execute(query)
    cur.close()

  def __init__(self) -> None:
    self._create_table()

  def truncate(self) -> None:
    connection = connect_to_db()
    query = f"""DELETE FROM {self.table_name()};"""
    logger.debug('Executing query: %s', query)
    cur = connection.cursor()
    cur.execute(query)
    cur.close()

# NOTE: Keep up to date with schemas in db/setup.sql

class ModelTable(BaseTable):
  def table_name(self) -> str:
    return 'model' 

  def _columns(self) -> List[ColumnDefinition]:
    return [
      ColumnDefinition('model_id', 'SERIAL', ['PRIMARY KEY']),
      ColumnDefinition('label', 'TEXT', []),
      ColumnDefinition('type_id', 'INTEGER', ['NOT NULL']),
      ColumnDefinition('speed', 'FLOAT', ['NOT NULL']),
    ]

class VehicleTable(BaseTable):
  def table_name(self) -> str:
    return 'vehicle' 
  
  def _columns(self) -> List[ColumnDefinition]:
    return [
      ColumnDefinition('vehicle_id', 'SERIAL', ['PRIMARY KEY']),
      ColumnDefinition('label', 'TEXT', []),
      ColumnDefinition('model_id', 'INTEGER', ['NOT NULL']),
      ColumnDefinition('owner_id', 'INTEGER', []),
    ]

  def _ddl_clauses(self) -> List[str]:
    return [
      'CONSTRAINT fk_vehicle_model FOREIGN KEY(model_id) REFERENCES model(model_id)'
    ]

class HubTable(BaseTable):
  def table_name(self) -> str:
    return 'hub' 
  
  def _columns(self) -> List[ColumnDefinition]:
    return [
      ColumnDefinition('hub_id', 'SERIAL', ['PRIMARY KEY']),
      ColumnDefinition('label', 'TEXT', []),
      ColumnDefinition('posX', 'FLOAT', ['NOT NULL']),
      ColumnDefinition('posY', 'FLOAT', ['NOT NULL']),
    ]


class PathTable(BaseTable):
  def table_name(self) -> str:
    return 'path' 
  
  def _columns(self) -> List[ColumnDefinition]:
    return [
      ColumnDefinition('path_id', 'SERIAL', ['PRIMARY KEY']),
      ColumnDefinition('start_hub_id', 'INTEGER', ['NOT NULL']),
      ColumnDefinition('end_hub_id', 'INTEGER', ['NOT NULL']),
    ]

  def _ddl_clauses(self) -> List[str]:
    return [
      'CONSTRAINT fk_path_start_hub FOREIGN KEY(start_hub_id) REFERENCES hub(hub_id)',
      'CONSTRAINT fk_path_end_hub FOREIGN KEY(end_hub_id) REFERENCES hub(hub_id)'
    ]


class MovementTable(BaseTable):
  def table_name(self) -> str:
    return 'movement' 
  
  def _columns(self) -> List[ColumnDefinition]:
    return [
      ColumnDefinition('movement_id', 'SERIAL', ['PRIMARY KEY']),
      ColumnDefinition('ts', 'BIGINT', ['NOT NULL']),
      ColumnDefinition('vehicle_id', 'INTEGER', ['NOT NULL']),
      ColumnDefinition('path_id', 'INTEGER', ['NOT NULL']),
    ]

  def _ddl_clauses(self) -> List[str]:
    return [
      'CONSTRAINT fk_movement_vehicle FOREIGN KEY(vehicle_id) REFERENCES vehicle(vehicle_id)',
      'CONSTRAINT fk_movement_path FOREIGN KEY(path_id) REFERENCES path(path_id)',
    ]

