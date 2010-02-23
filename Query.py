import dbus
import DBus
import Database

message_signature = '(asaa{ss})'
"""
 A message consists of
 
 Struct of
  Array of strings - tags
  Array of
   Dictionary of
    Headername and value - e.g content-type and 'text/plain' or content and 'Some text'

 The interpretation of the array of dictionaries should be the same as
 in
 http://people.collabora.co.uk/~danni/telepathy-book/sect.messaging.rich.html
 In addition, a keyword of 'remote_storage_object' in the header
 indicates a bus name and object path from which the actual message
 can be fetched. This should provide the interface
 org.redhog.epicenter.message_storage
"""
messages_signature = 'a' + message_signature

class MessageConflictsWithQuery(dbus.DBusException):
    _dbus_error_name = 'org.redhog.epicenter.query.MessageConflictsWithQuery'

class Query(DBus.ServiceObject):
    def __init__(self, storage, tags, anti_tags, original, *arg, **kw):
        self.storage = storage
        # Just ensure that they're sets...
        self.tags = set(tags)
        self.anti_tags = set(anti_tags)
        self.original = original
        DBus.ServiceObject.__init__(self, *arg, **kw)

    @DBus.ServiceObject.service_method(
        dbus_interface='org.redhog.epicenter.query',
        in_signature='sxx', out_signature='i')
    def get_tags(self, sort, start_pos, end_pos):
        "sort is matching, anti_matching or binary_search"
        pass

    @DBus.ServiceObject.service_method(
        dbus_interface='org.redhog.epicenter.query',
        in_signature='xx', out_signature='i')
    def get_nr_messages(self, start_date = -1, end_date = -1):
        pass

    @DBus.ServiceObject.service_method(
        dbus_interface='org.redhog.epicenter.query',
        in_signature='xxxx', out_signature=messages_signature)
    def get_messages(self, start_time = -1, end_time = -1, start_pos = -1, end_pos = -1):
        return self.storage._dbconn.get_messages(self.original, *self.storage._dbconn._limit_to_sql(start_pos, end_pos, *self._get_query_sql(start_time, end_time)))

    @DBus.ServiceObject.service_method(
        dbus_interface='org.redhog.epicenter.query',
        in_signature=message_signature, out_signature='')
    def insert_message(self, message):
        if self.anti_tags.intersection(set(message[0])): raise MessageConflictsWithQuery
        message = list(message)
        message[0] = list(self.tags.union(message[0]))
        return self.storage._insert_message(message)
    
    @dbus.service.signal(
        dbus_interface='org.redhog.epicenter.query',
        signature=message_signature)
    def message_arrived(self, message):
        pass

    def _message_arrived(self, message):
        tags = set(message[0])
        if self.tags - tags or self.anti_tags.intersection(tags):
            return
        self.message_arrived(message)

    def _get_query_sql(self, start_time = -1, end_time = -1):
        return self.storage._dbconn._query_to_sql(
            self.tags, self.anti_tags, self.original,
            *self.storage._dbconn._date_to_sql(start_time, end_time, query_object_table = 'message'))
