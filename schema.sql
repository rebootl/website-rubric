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
  data1 text
);
