import weakref
import DBus
import Database
import Query

class Storage(DBus.ServiceObject):
    def __init__(self, *arg, **kw):
        self._queries = weakref.WeakKeyDictionary()
        self._dbconn = Database.Database("Epicenter.db")
        DBus.ServiceObject.__init__(self, *arg, **kw)

    @DBus.ServiceObject.service_method(
        dbus_interface='org.redhog.epicenter.storage',
        in_signature='asasb', out_signature='o')
    def query(self, tags, anti_tags, original = 0):
        query = self.make_object_temporary(Query.Query(self, tags, anti_tags, original))
        self._queries[query] = 1
        return query

    def _insert_message(self, message):
        self._dbconn.insert_message(message)
        for query in self._queries.iterkeys():
            query._message_arrived(message)
