SELECT 'CREATE DATABASE status_database' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'status_database')\gexec

\c status_database

CREATE TABLE IF NOT EXISTS Machines (
  ID BIGSERIAL PRIMARY KEY,
  Name TEXT,
  Category TEXT,
  Addons TEXT ARRAY,
  ExtraConfig JSON,
  CollectStats BOOLEAN
);