# Copyright 2013 Agustin Zubiaga <aguz@sugarlabs.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import subprocess

from gi.repository import GObject
GObject.threads_init()
from gi.repository import Gtk
from gi.repository import WebKit

from sugar3.activity import activity
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.activity.widgets import StopButton
from sugar3.graphics.toolbarbox import ToolbarBox

import downloadmanager

class JournalShare(activity.Activity):

    def __init__(self, handle):

        activity.Activity.__init__(self, handle)

        activity_path = activity.get_bundle_path()
        self.server_proc = subprocess.Popen(['/bin/python', 'server.py',
            activity_path])

        toolbar_box = ToolbarBox()

        activity_button = ActivityToolbarButton(self)
        toolbar_box.toolbar.insert(activity_button, 0)
        activity_button.show()

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        separator.show()
        toolbar_box.toolbar.insert(separator, -1)

        stopbutton = StopButton(self)
        toolbar_box.toolbar.insert(stopbutton, -1)
        stopbutton.show()

        self.set_toolbar_box(toolbar_box)
        toolbar_box.show()

        self.view = WebKit.WebView()
        self.view.connect('mime-type-policy-decision-requested',
                     self.__mime_type_policy_cb)
        self.view.connect('download-requested', self.__download_requested_cb)

        self.view.load_uri('http://localhost:2500/web/index.html')
        self.view.show()
        self.set_canvas(self.view)

    def __mime_type_policy_cb(self, webview, frame, request, mimetype,
                              policy_decision):
        if not self.view.can_show_mime_type(mimetype):
            policy_decision.download()
            return True

        return False

    def __download_requested_cb(self, browser, download):
        downloadmanager.add_download(download, browser)
        return True

    def read_file(self, file_path):
        pass

    def write_file(self, file_path):
        pass

    def can_close(self):
        self.server_proc.kill()
        return True
