-- Table: items

-- DROP TABLE items;

CREATE TABLE items
(
  id_sql serial PRIMARY KEY,
  id text NOT NULL,
  tab_id text NOT NULL,
  owner text NOT NULL,
  buyout character varying(80),
  league text,
  name text,
)
WITH (
  OIDS=FALSE
);

CREATE INDEX items_tab_id_idx
  ON items
  USING hash
  (tab_id COLLATE pg_catalog."default");

CREATE TABLE items_mods
(
    id_sql serial PRIMARY KEY, 
    id text NOT NULL, 
    mods text, 
)
WITH (
  OIDS=FALSE
);

CREATE INDEX items_mods_id_idx
  ON items_mods
  USING hash
  (id COLLATE pg_catalog."default");


CREATE TABLE tabs
(
  id_sql serial PRIMARY KEY,
  id text NOT NULL,
  owner text,
  name text,
  buyout character varying(80),
  league text,
  item_count integer,
  last_update timestamp without time zone,
)
WITH (
  OIDS=FALSE
);
CREATE INDEX tabs_id_idx
  ON tabs
  USING hash
  (id COLLATE pg_catalog."default");

CREATE TABLE players
(
    id_sql serial PRIMARY KEY,
    name text,
)
WITH (
    OIDS=FALSE
);
CREATE INDEX players_id_idx
ON tabs
USING hash
(id_sql COLLATE pg_catalog."default");

CREATE TABLE players_league
(
    id_sql serial PRIMARY KEY,
    player text REFERENCES players (name),
    league text,
    last_update timestamp without time zone,
    nb_items int,

)
WITH (
    OIDS=FALSE
);

