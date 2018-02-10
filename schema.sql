CREATE TABLE IF NOT EXISTS changelog (
  id        integer primary key autoincrement,
  entry_id  integer not null,
  mod_type  text not null,
  date_norm text not null,
  time_norm text not null,
  pub       int default 0
);
CREATE TABLE IF NOT EXISTS "categories" (
	`id`	integer PRIMARY KEY AUTOINCREMENT,
	`ref`	TEXT NOT NULL,
	`title`	text NOT NULL,
	`desc`	TEXT,
	`tags`	text
);
CREATE TABLE IF NOT EXISTS "entries" (
	`id`	integer PRIMARY KEY AUTOINCREMENT,
	`ref`	text NOT NULL,
	`type`	text NOT NULL,
	`title`	text NOT NULL,
	`author`	text NOT NULL,
	`date_norm`	text NOT NULL,
	`time_norm`	text NOT NULL,
	`body_html`	text NOT NULL,
	`body_md`	text NOT NULL,
	`tags`	text,
	`pub`	int NOT NULL DEFAULT 0,
	`note_cat_id`	INTEGER,
	`note_show_home`	INTEGER DEFAULT 0
);
