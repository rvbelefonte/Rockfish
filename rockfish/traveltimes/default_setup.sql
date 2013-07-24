-- Builds the default traveltime database tables

--
-- Trace geomtery table
--
CREATE TABLE IF NOT EXISTS traces (
	   ensemble INTEGER NOT NULL PRIMARY KEY,
	   trace INTEGER NOT NULL PRIMARY KEY,
	   trace_in_file INTEGER,
	   source_x FLOAT NOT NULL,
	   source_y FLOAT NOT NULL,
	   source_z FLOAT NOT NULL,
	   receiver_x FLOAT NOT NULL,
	   receiver_y FLOAT NOT NULL,
	   receiver_z FLOAT NOT NULL,
	   line TEXT,
	   site TEXT)
