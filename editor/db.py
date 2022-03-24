import sqlite3
import os
from typing import Iterable, Optional, List
import logging
import argparse
import textwrap

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

connection: Optional[sqlite3.Connection] = None


# The special path name :memory: can be provided to create a temporary database 
# in RAM.
def connect_to_db() -> sqlite3.Connection:
  global connection
  if (connection is None):
    connection = sqlite3.connect(
      os.path.join(os.path.dirname(__file__), 'transportation.db')
      # ':memory:'
    )
  return connection


def close_db_connection() -> None:
  global connection
  if (connection is not None):
    connection.close()
    connection = None


def query(q: str, params: Iterable = []) -> sqlite3.Cursor:
  try:
    connection = connect_to_db()
    _query = textwrap.dedent(q).strip()
    logger.debug('Executing query: %s %s', _query, params)
    return connection.execute(_query, params)
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
    connection.execute(query)

  def __init__(self) -> None:
    self._create_table()

  def truncate(self) -> None:
    connection = connect_to_db()
    query = f"""DELETE FROM {self.table_name()};"""
    logger.debug('Executing query: %s', query)
    connection.execute(query)


class ModelTable(BaseTable):
  def table_name(self) -> str:
    return 'model' 

  def _columns(self) -> List[ColumnDefinition]:
    return [
      ColumnDefinition('model_id', 'INTEGER', ['PRIMARY KEY']),
      ColumnDefinition('label', 'TEXT', []),
      ColumnDefinition('type_id', 'INTEGER', ['NOT NULL']),
      ColumnDefinition('speed', 'FLOAT', ['NOT NULL']),
    ]

class VehicleTable(BaseTable):
  def table_name(self) -> str:
    return 'vehicle' 
  
  def _columns(self) -> List[ColumnDefinition]:
    return [
      ColumnDefinition('vehicle_id', 'INTEGER', ['PRIMARY KEY']),
      ColumnDefinition('label', 'TEXT', []),
      ColumnDefinition('model_id', 'INTEGER', ['NOT NULL']),
      ColumnDefinition('owner_id', 'INTEGER', []),
    ]

  def _ddl_clauses(self) -> List[str]:
    return [
      'FOREIGN KEY(model_id) REFERENCES model(model_id)'
    ]


def main():
  try:
    connect_to_db()
    model = ModelTable()
    vehicle = VehicleTable()

    for row in query("""
      SELECT v.vehicle_id, v.label, m.label AS model, m.speed 
      FROM vehicle v 
      JOIN model m ON m.model_id = v.model_id;
    """):
      print(row)
    
  finally:
    close_db_connection()


if __name__ == '__main__':
  main()