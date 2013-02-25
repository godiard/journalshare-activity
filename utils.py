
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

import os

from sugar import profile
from sugar.datastore import datastore

tfile = open('templates', 'r')
templates = tfile.read()
tfile.close()

webdir = os.path.join(os.path.dirname(__file__), 'web')

INDEX = open(os.path.join(webdir, 'index.html'), 'w')
ICONS_DIR = os.path.join(webdir, 'images')
FILES_DIR = os.path.join(webdir, 'files')


def fill_out_template(template, content):
    template = templates.split('#!%s\n' % template)[1].split('\n!#')[0]
    for x in list(content.keys()):
        template = template.replace('{%s}' % x, content[x])

    return template


def find_icon(mime_type):
    generic_name = mime_type.split('/')[0]
    if generic_name + '.svg' in os.listdir(ICONS_DIR):
        return '%s.svg' % generic_name

    else:
        return 'unknown.svg'


def link_file(file_path):
    link_path = os.path.join(FILES_DIR, os.path.split(file_path)[-1])
    os.link(file_path, link_path)
    return os.path.split(link_path)[-1]


def build_journal_page():
    for f in os.listdir(FILES_DIR):
        os.remove(os.path.join(FILES_DIR, f))

    objects_starred, no = datastore.find({'keep': '1'})
    objects = []

    for dsobj in objects_starred:
        title = dsobj.metadata['title']
        icon = find_icon(dsobj.metadata['mime_type'])
        file_link = link_file(dsobj.file_path)
        objects.append({'file': file_link, 'name': title, 'icon': icon})

    objects_html = ''
    for o in objects:
        objects_html += '%s' % fill_out_template('object', o)

    index_html = fill_out_template('index', {'nick': profile.get_nick_name(),
                                             'objects': objects_html})

    INDEX.write(index_html)
    INDEX.flush()


if __name__ == "__main__":
    build_journal_page()
