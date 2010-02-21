import dbus
import dbus.mainloop.glib
import gobject

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

bus = dbus.SessionBus()

storage = dbus.Interface(
    bus.get_object('org.redhog.epicenter',
                   '/org/redhog/epicenter/storage'),
    dbus_interface='org.redhog.epicenter.storage')

query = dbus.Interface(
    bus.get_object('org.redhog.epicenter',
                   storage.query(["foo", "bar"], ["fie"])),
    dbus_interface='org.redhog.epicenter.query')

def message_arrived(message):
    print "Received:", message

query.connect_to_signal("message_arrived", message_arrived)

print "Looping"
loop = gobject.MainLoop()
loop.run()
