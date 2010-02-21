import dbus
import dbus.mainloop.glib
import dbus.service
import gobject
import weakref
import DBus
import Storage

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

bus = DBus.SessionBus()
 	
name = dbus.service.BusName("org.redhog.epicenter", bus)
storage = Storage.Storage(bus, "/org/redhog/epicenter/storage")

print "At your service"
loop = gobject.MainLoop()
loop.run()
