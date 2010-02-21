#! /usr/bin/python

import dbus
import dbus.mainloop.glib
import gobject
import sys

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

query.insert_message((sys.argv[:-1], [{"content": sys.argv[-1]}]))
