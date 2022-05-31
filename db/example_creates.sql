-- TABLE
CREATE TABLE IF NOT EXISTS test(
    id SERIAL PRIMARY KEY,
    label TEXT,
    cc BIGINT
);

-- FUNCTION
CREATE OR REPLACE FUNCTION dist(x1 FLOAT, y1 FLOAT, x2 FLOAT, y2 FLOAT)
RETURNS FLOAT
RETURNS NULL ON NULL INPUT
LANGUAGE PLPGSQL
AS $$
BEGIN
    RETURN SQRT(POWER(x2-x2, 2) + POWER(y2-y1, 2));
END;
$$;

SELECT dist(2, 2, 2, 7); -- 5

-- PROCEDURE
CREATE OR REPLACE PROCEDURE gen_test(label TEXT, INOUT cc INTEGER DEFAULT NULL)
LANGUAGE PLPGSQL
AS $$
BEGIN
    SELECT FLOOR(random() * 10 + 1)::int INTO cc;
    INSERT INTO test ("label", "cc") VALUES (label, cc);
END;
$$;

CALL gen_test('bleb');

SELECT * FROM test ORDER BY cc;

-- INDEX
CREATE INDEX cc_idx ON test (cc);


-- VIEW
CREATE OR REPLACE VIEW hello_world AS 
SELECT 'hello world' AS hello;

SELECT * FROM hello_world;

-- MATERIALIZED VIEW
DROP MATERIALIZED VIEW IF EXISTS label_counts;

CREATE MATERIALIZED VIEW label_counts AS
SELECT label, COUNT(1) AS cnt FROM test GROUP BY label
WITH DATA;

SELECT * FROM label_counts;
REFRESH MATERIALIZED VIEW label_counts;

-- TRIGGER
CREATE TABLE IF NOT EXISTS math_facts(
    value1 FLOAT NOT NULL,
    value2 FLOAT NOT NULL,
    add FLOAT NOT NULL,
    sub FLOAT NOT NULL,
    mult FLOAT NOT NULL,
    div FLOAT NOT NULL,
    PRIMARY KEY(value1, value2)
);

CREATE OR REPLACE FUNCTION calculate_math_facts()
RETURNS TRIGGER
LANGUAGE PLPGSQL
AS $$
BEGIN
    IF NEW.value1 IS NULL THEN
        RAISE EXCEPTION 'value1 cannot be null';
    ELSIF NEW.value2 IS NULL THEN
        RAISE EXCEPTION 'value2 cannot be null';
    ELSIF NEW.value2 = 0 THEN
        RAISE EXCEPTION 'value2 cannot be 0';
    END IF;
    NEW.add = NEW.value1 + NEW.value2;
    NEW.sub = NEW.value1 - NEW.value2;
    NEW.mult = NEW.value1 * NEW.value2;
    NEW.div = NEW.value1 / NEW.value2;
    RETURN NEW;
END;
$$;

CREATE TRIGGER math_facts_trigger 
BEFORE INSERT OR UPDATE ON math_facts
FOR EACH ROW
EXECUTE FUNCTION calculate_math_facts();

INSERT INTO math_facts ("value1", "value2") 
VALUES 
    (1, 1),
    (1, 2),
    (1, 3),
    (2, 1),
    (2, 2),
    (2, 3);
    
UPDATE math_facts
SET mult = 10
WHERE value1=1 AND value2=1;
    
SELECT * FROM math_facts;
    
--------------------------------------------------------------------------
--------------------------------------------------------------------------

ALTER TABLE math_facts ADD COLUMN pow FLOAT;
ALTER TABLE math_facts ALTER COLUMN div DROP NOT NULL;

CREATE OR REPLACE FUNCTION calculate_math_facts()
RETURNS TRIGGER
LANGUAGE PLPGSQL
AS $$
BEGIN
	IF NEW.value1 IS NULL THEN
		RAISE EXCEPTION 'value1 cannot be NULL';
	ELSIF NEW.value2 IS NULL THEN
		RAISE EXCEPTION 'value2 cannot be NULL';
	END IF;	
	
	IF NEW.value2 = 0 THEN
		NEW.div = NULL;
	ELSE
		NEW.div = NEW.value1 / NEW.value2;
	END IF;
	
	NEW.add = NEW.value1 + NEW.value2;
	NEW.sub = NEW.value1 - NEW.value2;
	NEW.mult = NEW.value1 * NEW.value2;
	NEW.pow = POWER(NEW.value1, NEW.value2);
	
	RETURN NEW;
END;
$$;

CREATE OR REPLACE TRIGGER math_facts_trigger 
BEFORE UPDATE OR INSERT
ON math_facts
FOR EACH ROW
EXECUTE FUNCTION calculate_math_facts();

SELECT * FROM math_facts;

INSERT INTO math_facts ("value1", "value2")
VALUES (1, 0);

UPDATE math_facts 
SET add = 0;

INSERT INTO math_facts ("value1", "value2") 
VALUES 
    (5, 1),
    (5, 2),
    (5, 3);