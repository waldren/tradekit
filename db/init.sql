CREATE TABLE IF NOT EXISTS stock (
    id SERIAL PRIMARY KEY, 
    symbol TEXT NOT NULL UNIQUE, 
    name TEXT NOT NULL,
    exchange TEXT NOT NULL,
    industry text NULL,
    sector text NULL,
    shortable BOOLEAN NULL
);

CREATE TABLE IF NOT EXISTS ohlc_data 
(
  id SERIAL PRIMARY KEY,
  dt TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  stock_id INTEGER NOT NULL,
  open NUMERIC NOT NULL,
  high NUMERIC NOT NULL,
  low NUMERIC NOT NULL,
  close NUMERIC NOT NULL,
  volume NUMERIC NOT NULL,
  CONSTRAINT fk_stock FOREIGN KEY(stock_id) REFERENCES stock(id)
);

CREATE TABLE IF NOT EXISTS tick_data  
(
  id SERIAL PRIMARY KEY,
  dt TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  stock_id INTEGER NOT NULL,
  bid NUMERIC NOT NULL,
  ask NUMERIC NOT NULL,
  bid_vol NUMERIC,
  ask_vol NUMERIC,
  CONSTRAINT fk_stock FOREIGN KEY(stock_id) REFERENCES stock(id)
);

CREATE TABLE IF NOT EXISTS indicators (
  id SERIAL PRIMARY KEY,
  name text NOT NULL,
  symbol text NULL,
  src text NOT NULL DEFAULT 'unknown',
  cat text NOT NULL DEFAULT 'unknown',
  description text NULL
);

CREATE TABLE IF NOT EXISTS stock_indicators  
(
  id SERIAL PRIMARY KEY,
  dt TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  stock_id INTEGER NOT NULL,
  indicators_id INTEGER NOT NULL,
  val NUMERIC NOT NULL,
  CONSTRAINT fk_stock FOREIGN KEY(stock_id) REFERENCES stock(id),
  CONSTRAINT fk_indicators FOREIGN KEY(indicators_id) REFERENCES indicators(id),
  UNIQUE (stock_id, indicators_id, dt)
);

CREATE TABLE IF NOT EXISTS fundamental (
  id SERIAL PRIMARY KEY,
  symbol text not null,
  name text null,
  description text null,
  useage text null
);

CREATE TABLE IF NOT EXISTS stock_fundamental  
(
  id SERIAL PRIMARY KEY,
  dt TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  stock_id INTEGER NOT NULL,
  fundamental_id INTEGER NOT NULL,
  val NUMERIC NOT NULL,
  CONSTRAINT fk_stock FOREIGN KEY(stock_id) REFERENCES stock(id),
  CONSTRAINT fk_fundamental FOREIGN KEY(fundamental_id) REFERENCES fundamental(id),
  UNIQUE (stock_id, fundamental_id, dt)
);

CREATE TABLE IF NOT EXISTS watchlist(
  id SERIAL PRIMARY KEY,
  list text NOT NULL,
  stock_id integer NOT NULL,
  dt_add TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  dt_remove TIMESTAMP WITHOUT TIME ZONE NULL,
  active boolean NOT NULL DEFAULT TRUE,
  notes text null,
  CONSTRAINT fk_stock FOREIGN KEY(stock_id) REFERENCES stock(id)
);