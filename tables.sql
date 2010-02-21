
create table object_type (
	object_type_id integer primary key,
	name varchar
);

create table object (
	object_id integer primary key,
	object_type_id references object_type(object_type_id)
);

create table tag (
	object_id integer unique references object(object_id),
	name varchar
);

create table message (
	object_id integer unique references object(object_id),
	time integer
);

create table message_part (
	object_id integer references object(object_id),
	message_part_id integer primary_key
);

create table message_part_keyval (
	object_id integer references object(object_id),
	message_part_id integer references message_part(message_part_id),
	key text,
	value text
);

create table tagging (
	object_id integer references object(object_id),
	has_tag_id integer references tag(tag_id),
	original bool
);

insert into object_type (name) values ('tag');
insert into object_type (name) values ('message');
