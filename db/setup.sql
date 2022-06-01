-- TABLES -- Keep up to date with schemas in editor/db.py
CREATE TABLE IF NOT EXISTS model(
  model_id SERIAL PRIMARY KEY,
  label TEXT,
  type_id INTEGER NOT NULL,
  speed FLOAT NOT NULL
)

CREATE TABLE IF NOT EXISTS vehicle(
  vehicle_id SERIAL PRIMARY KEY,
  label TEXT,
  model_id INTEGER NOT NULL,
  owner_id INTEGER,
  CONSTRAINT fk_vehicle_model FOREIGN KEY(model_id) REFERENCES model(model_id)
)

CREATE TABLE IF NOT EXISTS hub(
  hub_id SERIAL PRIMARY KEY,
  label TEXT,
  posX FLOAT NOT NULL,
  posY FLOAT NOT NULL
)

CREATE TABLE IF NOT EXISTS path(
  path_id SERIAL PRIMARY KEY,
  start_hub_id INTEGER NOT NULL,
  end_hub_id INTEGER NOT NULL,
  CONSTRAINT fk_path_start_hub FOREIGN KEY(start_hub_id) REFERENCES hub(hub_id),
  CONSTRAINT fk_path_end_hub FOREIGN KEY(end_hub_id) REFERENCES hub(hub_id)
)

CREATE TABLE IF NOT EXISTS movement(
  movement_id SERIAL PRIMARY KEY,
  timestamp BIGINT NOT NULL,
  vehicle_id INTEGER NOT NULL,
  path_id INTEGER NOT NULL,
  CONSTRAINT fk_movement_vehicle FOREIGN KEY(vehicle_id) REFERENCES vehicle(vehicle_id),
  CONSTRAINT fk_movement_path FOREIGN KEY(path_id) REFERENCES path(path_id),
)