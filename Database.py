import sqlite3

class Database(object):
    def __init__(self, dbfile = "Epicenter.db"):
        self.dbconn = sqlite3.connect(dbfile)

    def insert_message(self, message):
        tags, parts = message
        cur = self.dbconn.cursor()

        cur.execute("insert into object (object_type_id) select object_type_id from object_type where name = 'message'")
        cur.execute("select last_insert_rowid()")
        object_id = cur.fetchone()[0]
        cur.execute("insert into message (object_id, time) values (?, ?)", (object_id, 0))

        for part in parts:
            cur.execute("insert into message_part (object_id) values (?)", (object_id,))
            cur.execute("select last_insert_rowid()")
            message_part_id = cur.fetchone()[0]

            for key, value in part.iteritems():
                cur.execute("insert into message_part_keyval (object_id, message_part_id, key, value) values (?, ?, ?, ?)",
                            (object_id, message_part_id, key, value))

        for tag in tags:
            cur.execute("select object_id from tag where name = ?", (tag,))
            row = cur.fetchone()
            if row:
                tag_id = row[0]
            else:
                cur.execute("insert into object (object_type_id) select object_type_id from object_type where name = 'tag'")
                cur.execute("select last_insert_rowid()")
                tag_id = cur.fetchone()[0]
                cur.execute("insert into tag (object_id, name) values (?, ?)", (tag_id, tag))
            cur.execute("insert into tagging (object_id, has_tag_id, original) values (?, ?, 0)", (object_id, tag_id))
            cur.execute("insert into tagging (object_id, has_tag_id, original) values (?, ?, 1)", (object_id, tag_id))

        cur.close()
        self.dbconn.commit()

    @classmethod
    def _date_to_sql(cls, start_time = 0, end_time = 0, query_object_table = 'object', query_object_params = []):
        if start_time == 0 and end_time == 0:
            return query_object_table, query_object_params

        info = {'query_object_table': query_object_table}

        info['cmps'] = []
        params = []
        if start_time != 0:
            info['cmps'].append("m.time >= %s")
            params.append(start_time)
        if end_time != 0:
            info['cmps'].append("m.time <= %s")
            params.append(end_time)
        info['cmps'] = ' and '.join(info['cmps'])
        
        return """
         (select
           p.%(post_table_id)s
          from
           %(query_object_table)s as q       
           join message as m on
            q.object_id = m.object_id
          where
           %(cmps)s
         )
        """ % info, query_object_params + params

    @classmethod
    def _query_to_sql(cls, tags, anti_tags, original = 1, query_object_table = 'object', query_object_params = []):
        except_array = []
        join_array = []
        except_param_array = []
        join_param_array = []

        info = {'query_object_table': query_object_table,
                'n': 0}

        for tag in anti_tags:
            except_array.append("""
             except
              select
               ot%(n)s.object_id
              from
               tagging as ot%(n)s,
               tag as t%(n)s
              where
               t%(n)s.object_id = ot%(n)s.has_tag_id
               and t%(n)s.name = ?
               and ot%(n)s.original = ?
               """ % info)
            except_param_array.append(tag[1:])
            except_param_array.append(original)
            info["n"] += 1
        for tag in tags:
            join_array.append("""
             join tagging as ot%(n)s on
              ot%(n)s.object_id = o.object_id
             join tag as t%(n)s on
              t%(n)s.object_id = ot%(n)s.has_tag_id
              and t%(n)s.name = ?
              and ot%(n)s.original = ?
            """ % info)
            join_param_array.append(tag)
            join_param_array.append(original)
            info["n"] += 1

        info["joins"] = "".join(join_array)
        info["excepts"] = "".join(except_array)

        return """
         (select
           o.object_id
          from
           %(query_object_table)s as o
           %(joins)s
          %(excepts)s
         )
        """ % info, query_object_params + join_param_array + except_param_array

    def get_messages(self, sql, params):
        cur = self.dbconn.cursor()
        sql = """
         select
          m.*,
          kv.*,
          (select
            group_concat(t.name)
           from
            tagging as mt
            join tag as t on
             m.object_id = mt.object_id
             and mt.has_tag_id = t.object_id) as tags
         from
          %s as q
          join message as m on
           q.object_id = m.object_id
          join message_part_keyval as kv on
           m.object_id = kv.object_id
         order by
          m.time,
          m.object_id,
          kv.message_part_id,
          kv.key
        """  % (sql,)
        
        cur.execute(sql, params)
        names = [dsc[0] for dsc in cur.description]

        res = []
        msg_tags = []
        msg_id = None
        msg = []
        part_id = None
        part = {}
        row = True
        while row:
            row = cur.fetchone()
            if row: row = dict(zip(names, row))

            new_msg = not row or not msg_id or msg_id != row['object_id']
            new_part = new_msg or part_id != row['message_part_id']

            if new_part:
                if part_id is not None:
                    msg.append(part)
                if row:
                    part_id = row['message_part_id']
                    part = {}
            if new_msg:
                if msg_id is not None:
                    res.append((msg_tags, msg))
                if row:
                    msg_id = row['object_id']
                    msg_tags = row['tags'].split(',')
                    msg = []
            if row:
                part[row['key']] = row['value']
        
        cur.close()
        return res

if __name__ == "__main__":


    db = Database()

    for m in db.get_messages(*db._query_to_sql(["foo"], [], 1, "message")):
        print m
