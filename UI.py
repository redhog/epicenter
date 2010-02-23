import dbus
import dbus.mainloop.glib
import gobject
import DBus
import gnome
import gtk
import gtk.glade
 
class EpicenterWidget(object):
    def __init__(self, **kw):
        for key, value in kw.iteritems():
            setattr(self, key, value)
        self.glade = gtk.glade.XML("epicenter.glade", type(self).__name__)
        self.glade.signal_autoconnect(self)
        self.widget = self.glade.get_widget(type(self).__name__)
        self.widget.visible = True

class SearchHeader(EpicenterWidget):
    def on_ClosePage_clicked(self, button):
        searches = self.parent.glade.get_widget("Searches")
        self.content.close()
        searches.remove_page(searches.page_num(self.content.widget))

    def on_Query_key_release_event(self, input, event):
        if event.string == '\r':
            self.content.on_query_changed(input.get_text())

class SearchContent(EpicenterWidget):
    def __init__(self, **kw):
        self.query = None
        EpicenterWidget.__init__(self, **kw)

    def close(self):
        if self.query:
            # FIXME: How to disconnect on_message_arrived?
            pass
    
    def on_query_changed(self, text):
        self.close()
        tags = [tag.strip() for tag in text.split(";")]
        anti_tags = [tag[1:] for tag in tags if tag.startswith("!")]
        tags = [tag for tag in tags if not tag.startswith("!")]
        self.query = dbus.Interface(
            self.parent.bus.get_object('org.redhog.epicenter',
                                       self.parent.storage.query(dbus.Array(tags, "s"), dbus.Array(anti_tags, "s"))),
            dbus_interface='org.redhog.epicenter.query')

        self.query.connect_to_signal("message_arrived", self.on_message_arrived)
        for m in self.query.get_messages():
            self.on_message_arrived(m)

    def on_message_arrived(self, message):
        buf = self.glade.get_widget("ReceiveText").get_buffer()

        info = dict(message[1][0])
        info['tags'] = '; '.join(message[0])
        buf.insert(buf.get_end_iter(), "%(tags)s\n%(content)s\n\n" % info)
    
class MainWindow(EpicenterWidget):
    def __init__(self, bus, **kw):
        self.bus = bus
        self.storage = dbus.Interface(
            bus.get_object('org.redhog.epicenter',
                           '/org/redhog/epicenter/storage'),
            dbus_interface='org.redhog.epicenter.storage')
        EpicenterWidget.__init__(self, **kw)

    def on_NewPage_clicked(self, button):
        searches = self.glade.get_widget("Searches")
        page_nr = searches.get_n_pages() - 1
        content = SearchContent(parent = self)
        header = SearchHeader(parent = self, content = content)
        searches.insert_page(content.widget, header.widget, page_nr)

    def on_MainWindow_delete_event(self, window, event):
        gtk.main_quit()

gnome.program_init("Epicenter", "0.01")
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
MainWindow(dbus.SessionBus())
gtk.main()
