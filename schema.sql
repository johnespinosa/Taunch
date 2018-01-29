drop table if exists userInfo;
create table userInfo (
 user text not null,
 password text not null,
 friends text not null,
 memories text not null
);
drop table if exists memories;
create table memories (
  id integer primary key autoincrement,
  title text not null,
  comment_ids text,
  owner text not null
);
drop table if exists comments;
create table comments (
  id integer primary key autoincrement,
  content text,
  type text,
  reply_ids text,
  owner text,
  isVisible text,
  date text
);
drop table if exists images;
create table images (
  id integer primary key,
  image_names text
);