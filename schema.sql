drop table if exists entries;
create table entries (
  id integer primary key autoincrement,
  ref text not null,
  type text not null,
  title text not null,
  author text not null,
  date_norm text not null,
  time_norm text not null,
  body_html text not null,
  body_md text not null,
  tags text,
  pub int default 0
);

drop table if exists changelog;
create table changelog (
  id integer primary key autoincrement,
  entry_id integer not null,
  mod_type text not null,
  date_norm text not null,
  time_norm text not null,
  pub int default 0
);

drop table if exists categories;
create table categories (
  id integer primary key autoincrement,
  title text not null,
  tags text
);

/* not used atm. */
/*drop table if exists galleries;
create table galleries (
  id integer primary key autoincrement,
  ref text not null,
  title text not null,
  desc text not null,
  tags text not null,
  date_norm text not null,
  pub int default 0
);

drop table if exists images;
create table images (
  id integer primary key autoincrement,
  ref text not null,
  thumb_ref text not null,
  caption text not null,
  datetime_norm text not null,
  exif_json text not null,
  gallery_id int,
  pub ind default 1
);*/
