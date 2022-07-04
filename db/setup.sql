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

CREATE OR REPLACE FUNCTION lerp(a FLOAT, b FLOAT, ratio FLOAT)
RETURNS FLOAT
RETURNS NULL ON NULL INPUT
LANGUAGE PLPGSQL
IMMUTABLE
AS $$
BEGIN
  RETURN a + ((b-a) * ratio);
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
  -- distance FLOAT NOT NULL,
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
/* 
  Movement table fields and include arrival_time of each movement based on the start time, vehicle's model speed, and path distance
*/
CREATE OR REPLACE VIEW movement_with_arrival AS
WITH cte AS (
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
  JOIN model mdl on v.model_id = mdl.model_id
)
SELECT movement_id, ts, vehicle_id, path_id, path_time, ts + path_time AS arrival_time
FROM cte;


/*
  Lists inconsistencies in movement data:
   - Vehicles leaving from a hub it was not present in
   - Multiple departures of same vehicle at same timestamp
*/
CREATE OR REPLACE VIEW movement_inconsistencies AS  
WITH cte AS (
	SELECT 
		MWA.movement_id, 
		MWA.vehicle_id,
		MWA.ts, 
		LAG(MWA.arrival_time) 
			OVER(PARTITION BY MWA.vehicle_id ORDER BY MWA.arrival_time ASC) AS prev_arrival_ts,
		P.start_hub_id,
		LAG(P.end_hub_id) 
			OVER(PARTITION BY MWA.vehicle_id ORDER BY MWA.arrival_time ASC) AS prev_arrival_hub
	FROM movement_with_arrival MWA
	JOIN path P ON MWA.path_id = P.path_id
)
SELECT movement_id, vehicle_id, ts, 'VEHICLE_NOT_IN_HUB' AS inconsistency_type
FROM cte
WHERE prev_arrival_hub IS NOT NULL AND prev_arrival_ts IS NOT NULL
	AND (start_hub_id != prev_arrival_hub OR ts < prev_arrival_ts)
UNION ALL
SELECT m1.movement_id, m1.vehicle_id, m1.ts, 'MULTIPLE_VEHICLE_DEPARTURES' AS inconsistency_type
FROM movement m1
JOIN movement m2 ON m1.ts = m2.ts AND m1.vehicle_id = m2.vehicle_id AND m1.movement_id != m2.movement_id;


/*
  Starting hub for each vehicle based on its first movement.
*/
CREATE OR REPLACE VIEW start_hub AS 
WITH cte AS (
	SELECT 
		M.vehicle_id, 
		M.ts AS first_movement_ts, 
		p.start_hub_id, 
		ROW_NUMBER() OVER(PARTITION BY vehicle_id ORDER BY ts ASC) AS rn
	FROM movement M
	JOIN path P ON M.path_id = P.path_id
) 
SELECT vehicle_id, start_hub_id, first_movement_ts
FROM cte WHERE rn = 1;

-- FUNCTIONS
/*
  Returns a table of which vehicle is in each hub. 
  Only accurate if there are no movement_inconsistencies.
*/
CREATE OR REPLACE FUNCTION in_hub(ts BIGINT)
RETURNS TABLE (
  vehicle_id INTEGER,
  hub_id INTEGER
)
RETURNS NULL ON NULL INPUT
LANGUAGE SQL
STABLE
AS $$
  WITH cte AS (
    SELECT 
      MWA.vehicle_id, 
      MWA.ts,
      MWA.arrival_time,
      P.end_hub_id,
      ROW_NUMBER() OVER (PARTITION BY vehicle_id ORDER BY MWA.ts DESC) AS rn
    FROM movement_with_arrival MWA
    JOIN path P ON MWA.path_id = P.path_id
    WHERE MWA.ts <= $1
  )
  SELECT vehicle_id, end_hub_id AS hub_id
  FROM cte 
  WHERE rn = 1 AND arrival_time <= $1
  UNION
  SELECT vehicle_id, start_hub_id AS hub_id
  FROM start_hub
  WHERE first_movement_ts > $1;
$$;

/*
  Returns a table of vehicles currently in progress of a movement and their interpolated position. 
  Only accurate if there are no movement_inconsistencies.
*/
CREATE OR REPLACE FUNCTION in_flight(ts BIGINT)
RETURNS TABLE (
  vehicle_id INTEGER,
  path_id INTEGER,
  progress_percentage FLOAT,
  posX FLOAT,
  posY FLOAT
)
RETURNS NULL ON NULL INPUT
LANGUAGE SQL
STABLE
AS $$
  WITH cte AS (
    SELECT 
      MWA.vehicle_id, 
      MWA.ts,
      MWA.arrival_time,
      MWA.path_time,
      P.path_id,
      HS.posX AS startX,
      HE.posX AS endX,
      HS.posY AS startY,
      HE.posY AS endY,
      ROW_NUMBER() OVER (PARTITION BY vehicle_id ORDER BY MWA.ts DESC) AS rn
    FROM movement_with_arrival MWA
    JOIN path P ON MWA.path_id = P.path_id
    JOIN hub HS ON P.start_hub_id = HS.hub_id
    JOIN hub HE ON P.end_hub_id = HE.hub_id
    WHERE MWA.ts <= $1
  )
  SELECT 
    vehicle_id, 
    path_id,
    ($1 - ts) / path_time::FLOAT AS progress_percentage,
    lerp(startX, endX, ($1 - ts) / path_time::FLOAT) AS posX,
    lerp(startY, endY, ($1 - ts) / path_time::FLOAT) AS poxY
  FROM cte 
  WHERE rn = 1 AND arrival_time > $1
$$;


-- INDEXES
CREATE INDEX IF NOT EXISTS movement_timestamp_idx ON movement(ts);


-- PROCEDURES
CREATE OR REPLACE PROCEDURE insert_sample_data()
LANGUAGE PLPGSQL
AS $$
BEGIN
  INSERT INTO model (label, type_id, speed) 
  VALUES 
    ('slow', 0, 10),     -- model_id=1
    ('medium', 0, 50),   -- model_id=2
    ('fast', 0, 100);    -- model_id=3

  INSERT INTO vehicle(model_id, owner_id)
  VALUES
    (1, 0),   -- vehicle_id=1
    (2, 0),   -- vehicle_id=2
    (2, 0);   -- vehicle_id=3

  INSERT INTO vehicle(label, model_id, owner_id)
  VALUES
    ('special_vehicle', 3, 0);   -- vehicle_id=4

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
END;
$$;


-- TRIGGERS
CREATE OR REPLACE FUNCTION set_vehicle_label()
RETURNS TRIGGER
LANGUAGE PLPGSQL
AS $$
BEGIN
	IF NEW.label IS NULL OR NEW.label = '' THEN
		NEW.label = CONCAT('vehicle', NEW.vehicle_id);
	END IF;	
	RETURN NEW;
END;
$$;

CREATE TRIGGER vehicle_label_trigger 
BEFORE INSERT OR UPDATE ON vehicle
FOR EACH ROW
EXECUTE FUNCTION set_vehicle_label();

-- -- DISABLED: DOES NOT ACCOUNT FOR CHANGES ON HUB POSITION
-- CREATE OR REPLACE FUNCTION set_path_distance()
-- RETURNS TRIGGER
-- LANGUAGE PLPGSQL
-- AS $$
-- DECLARE
--   startX FLOAT; 
--   startY FLOAT; 
--   endX FLOAT; 
--   endY FLOAT; 
-- BEGIN
-- 	IF NEW.start_hub_id IS NULL THEN
-- 		RAISE EXCEPTION 'start_hub_id cannot be NULL';
-- 	ELSIF NEW.end_hub_id IS NULL THEN
-- 		RAISE EXCEPTION 'end_hub_id cannot be NULL';
-- 	END IF;	

--   select posX into startX from hub WHERE NEW.start_hub_id = hub_id;
--   select posY into startY from hub WHERE NEW.start_hub_id = hub_id;
--   select posX into endX from hub WHERE NEW.end_hub_id = hub_id;
--   select posY into endY from hub WHERE NEW.end_hub_id = hub_id;
	
-- 	NEW.distance = dist(startX, startY, endX, endY);
	
-- 	RETURN NEW;
-- END;
-- $$;

-- CREATE TRIGGER path_distance_trigger 
-- BEFORE INSERT OR UPDATE ON path
-- FOR EACH ROW
-- EXECUTE FUNCTION set_path_distance();


-----------------------------------------------------------------------
CALL insert_sample_data();