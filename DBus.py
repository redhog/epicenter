import dbus
import dbus.mainloop.glib
import dbus.service
import gobject
import threading
import inspect

class TempObjectRegistry(object):
    def __init__(self, bus):
        self.registry = {}
        self.bus = bus
        self.bus.add_signal_receiver(self.nameOwnerChanged, signal_name="NameOwnerChanged")

    def register(self, sender, obj):
        if sender not in self.registry:
            self.registry[sender] = {}
        self.registry[sender][obj.__dbus_object_path__] = obj

    def unregister(self, sender, obj):
        if sender in self.registry:
            self.registry[sender].pop(obj.__dbus_object_path__).remove_from_connection()
        
    def nameOwnerChanged(self, name, old_owner, new_owner):
        if not old_owner: return
        for obj in self.registry[old_owner].values():
            obj.remove_from_connection()
        del self.registry[old_owner]

class ServiceWrapper(object):
    def __init__(self, **kw):
        self.kw = kw

    def __call__(self, method):
        a = inspect.getargspec(method)

        argspecs = a.args
        if a.defaults:
            argspecs = argspecs[:-len(a.defaults)] + [
                "%s = %s" % (name, repr(value))
                for name, value
                in zip(argspecs[-len(a.defaults):],
                       a.defaults)]

        wrapper_code = """
def wrapped_method(%(params)s):
    self._sender_name.sender_name = __sender_name__
    return method(%(outparams)s)
""" % {'params': ', '.join(argspecs + ['__sender_name__ = None'] + (a.varargs and ['*' + a.varargs] or []) + (a.keywords and ['**' + a.keywords] or [])),
               'outparams': ', '.join(argspecs + (a.varargs and ['*' + a.varargs] or []) + (a.keywords and ['**' + a.keywords] or []))}
        localvars = {'method': method}
        exec(wrapper_code, localvars)
        return dbus.service.method(sender_keyword='__sender_name__', **self.kw)(localvars['wrapped_method'])

class ServiceObject(dbus.service.Object):
    ServiceWrapper = ServiceWrapper
    
    def __init__(self, *arg, **kw):
        self._sender_name = threading.local()
        dbus.service.Object.__init__(self, *arg, **kw)

    def get_sender_name(self):
        return self._sender_name.sender_name

    @classmethod
    def service_method(cls, **kw):
        return cls.ServiceWrapper(**kw)

    def make_object_temporary(self, obj):
        obj.add_to_connection(self.connection, "/org/redhog/dbus/temporary/%s" % id(obj))
        self.connection.tempObjectRegistry.register(self.get_sender_name(), obj)
        return obj

class SessionBus(dbus.SessionBus):
    TempObjectRegistry = TempObjectRegistry
    def __new__(cls, *arg, **kw):
        self = dbus.SessionBus(*arg, **kw)
        self.tempObjectRegistry = cls.TempObjectRegistry(self)
        return self
