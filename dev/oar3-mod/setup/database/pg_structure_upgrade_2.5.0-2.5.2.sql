
ALTER TABLE jobs ADD array_index INTEGER NOT NULL default '1';

-- Update the database schema version
DELETE FROM schema;
INSERT INTO schema(version, name) VALUES ('2.5.2', '');
