SELECT 'CREATE DATABASE status_database' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'status_database')\gexec

\c status_database

CREATE TABLE IF NOT EXISTS Machines (
  ID BIGSERIAL PRIMARY KEY,
  Name TEXT,
  Category TEXT,
  Addons TEXT ARRAY,
  Scripts TEXT ARRAY,
  ExtraConfig JSON,
  CollectStats BOOLEAN
);

CREATE TABLE IF NOT EXISTS LoggedData (
  Name TEXT, -- Machine name
  Time TIMESTAMP WITH TIME ZONE,
  Data JSON
);