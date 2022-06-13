-- UTIL
CREATE OR REPLACE FUNCTION dist(x1 FLOAT, y1 FLOAT, x2 FLOAT, y2 FLOAT)
RETURNS FLOAT
RETURNS NULL ON NULL INPUT
LANGUAGE PLPGSQL
IMMUTABLE
AS $$
BEGIN
  RETURN SQRT(POWER(x2-x1, 2) + POWER(y2-y1, 2));
END;
$$;

-- TABLES -- Keep up to date with schemas in editor/db.py
CREATE TABLE IF NOT EXISTS model(
  model_id SERIAL PRIMARY KEY,
  label TEXT,
  type_id INTEGER NOT NULL,
  speed FLOAT NOT NULL
);

CREATE TABLE IF NOT EXISTS vehicle(
  vehicle_id SERIAL PRIMARY KEY,
  label TEXT,
  model_id INTEGER NOT NULL,
  owner_id INTEGER,
  CONSTRAINT fk_vehicle_model FOREIGN KEY(model_id) REFERENCES model(model_id)
);

CREATE TABLE IF NOT EXISTS hub(
  hub_id SERIAL PRIMARY KEY,
  label TEXT,
  posX FLOAT NOT NULL,
  posY FLOAT NOT NULL
);

CREATE TABLE IF NOT EXISTS path(
  path_id SERIAL PRIMARY KEY,
  start_hub_id INTEGER NOT NULL,
  end_hub_id INTEGER NOT NULL,
  CONSTRAINT fk_path_start_hub FOREIGN KEY(start_hub_id) REFERENCES hub(hub_id),
  CONSTRAINT fk_path_end_hub FOREIGN KEY(end_hub_id) REFERENCES hub(hub_id)
);

CREATE TABLE IF NOT EXISTS movement(
  movement_id SERIAL PRIMARY KEY,
  ts BIGINT NOT NULL,
  vehicle_id INTEGER NOT NULL,
  path_id INTEGER NOT NULL,
  CONSTRAINT fk_movement_vehicle FOREIGN KEY(vehicle_id) REFERENCES vehicle(vehicle_id),
  CONSTRAINT fk_movement_path FOREIGN KEY(path_id) REFERENCES path(path_id)
);


-- VIEWS
CREATE OR REPLACE VIEW discrepancies AS 
SELECT 
  0 AS movement_id, 
  'VEHICLE_NOT_IN_HUB' AS discrepancy_type
UNION ALL
SELECT 
  0 AS movement_id, 
  'MULTIPLE_VEHICLE_DEPARTURES' AS discrepancy_type;
/* TODO
  vehicle leaving from a hub it was not present in
  multiple departures of same vehicle at same timestamp
*/
  
/* 
  Movement table fields and include arrival_time of each movement based on the start time, vehicle's model speed, and path distance
*/
CREATE OR REPLACE VIEW movement_with_arrival AS
SELECT 
  m.movement_id, 
  m.ts, 
  m.vehicle_id, 
  m.path_id, 
  dist(shub.posX, shub.posY, ehub.posX, ehub.posY) / mdl.speed AS path_time
FROM movement m
JOIN path p ON m.path_id = p.path_id
JOIN hub shub ON p.start_hub_id = shub.hub_id
JOIN hub ehub ON p.end_hub_id = ehub.hub_id
JOIN vehicle v ON m.vehicle_id = v.vehicle_id
JOIN model mdl on v.model_id = mdl.model_id;


-- FUNCTIONS
CREATE OR REPLACE FUNCTION in_hub(ts BIGINT)
RETURNS TABLE (
  hub_id INTEGER,
  vehicle_id INTEGER
)
RETURNS NULL ON NULL INPUT
LANGUAGE PLPGSQL
STABLE
AS $$
BEGIN
  /* TODO
    vehicles in each hub at timestamp
      -> for each vehicle find the MOVEMENTS_WITH_ARRIVAL with the greatest start time <= timestamp
        - if arrival time <= timestamp, vehicle is in end_hub_id of path
  */
END;
$$;

CREATE OR REPLACE FUNCTION in_flight(ts BIGINT)
RETURNS TABLE (
  vehicle_id INTEGER,
  posX FLOAT,
  posY FLOAT
)
RETURNS NULL ON NULL INPUT
LANGUAGE PLPGSQL
STABLE
AS $$
BEGIN
  /* TODO
    in-flight vehicles position at timestamp
      -> Inflight position can be interpolated from MOVEMENTS_WITH_ARRIVAL start and arrival and timestamp
  */
END;
$$;


-- INDEXES
CREATE INDEX IF NOT EXISTS movement_timestamp_idx ON movement(ts);


-- PROCEDURES
CREATE OR REPLACE PROCEDURE clear_start_hubs()
LANGUAGE PLPGSQL
AS $$
BEGIN
  /* TODO
    delete all movements before timestamp 0
  */
END;
$$;

CREATE OR REPLACE PROCEDURE set_start_hubs()
LANGUAGE PLPGSQL
AS $$
BEGIN
  /* TODO
    reset with CLEAR_START_HUBS, then create a loopback movement for each vehicle at timestamp=-1 to and from the hub it has its first movement from
  */
END;
$$;


-- TRIGGER
/* TODO
  path distance
*/


-- USERS
/* TODO
  Create user with read-only priviledges for flask?
*/


-----------------------------------------------------------------------
INSERT INTO model (label, type_id, speed) 
VALUES 
  ('slow', 0, 10),     -- model_id=1
  ('medium', 0, 50),   -- model_id=2
  ('fast', 0, 100);    -- model_id=3

INSERT INTO vehicle(label, model_id, owner_id)
VALUES
  ('vehicle1', 1, 0),   -- vehicle_id=1
  ('vehicle2', 2, 0),   -- vehicle_id=2
  ('vehicle3', 2, 0),   -- vehicle_id=3
  ('vehicle4', 3, 0);   -- vehicle_id=4

INSERT INTO hub(label, posX, posY)
VALUES
  ('hub1', 0, 0),       -- hub_id=1
  ('hub2', 100, 100);   -- hub_id=2

INSERT INTO path(start_hub_id, end_hub_id)
VALUES
  (1, 2),   -- path_id=1
  (2, 1);   -- path_id=2

INSERT INTO movement(ts, vehicle_id, path_id)
VALUES
  (0, 1, 1),  -- movement_id=1
  (15, 1, 2), -- movement_id=2
  (2, 2, 1),  -- movement_id=3
  (4, 3, 1);  -- movement_id=4