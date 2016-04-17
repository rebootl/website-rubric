drop table if exists entries;
create table entries (
  id integer primary key autoincrement,
  ref text not null,
  type text not null,
  title text not null,
  author text not null,
  date_str text not null,
  datetime_norm text not null,
  date_norm text not null,
  time_norm text not null,
  body_html text not null,
  body_md5sum text not null,
  meta_json text not null,
  body_md text not null,
  data1 text,
  pub int default 1,
  exifs_json text
);

drop table if exists galleries;
create table galleries (
  id integer primary key autoincrement,
  ref text not null,
  title text not null,
  desc text not null,
  datetime_norm text not null,
  pub int default 1
);

drop table if exists images;
create table images (
  id integer primary key autoincrement,
  ref text not null,
  caption text,
  datetime_norm text,
  exif_json text,
  gallery_id int,
  pub int default 1
);
