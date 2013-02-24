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

from sugar.datastore import datastore

tfile = open('templates', 'r')
templates = tfile.read()
tfile.close()


def fill_out_template(template, content):
    template = templates.split('#!%s\n' % template)[1].split('\n!#')[0]
    for x in content.keys():
        template = template.replace('{%s}' % x, content[x])

    return template


def build_journal():
    objects_starred, no = datastore.find({'keep': '1'})

    objects = [{'file': 'a', 'name': 'No Te Va Gustar - A las nueve',
                'icon': 'audio-x-generic.svg'},
               {'file': 'b', 'name': 'Perla jugando con el gato BOB',
                'icon': 'image.svg'}]

    objects_html = ''
    for o in objects:
        objects_html += '%s' % fill_out_template('object', o)

    print fill_out_template('index', {'nick': 'Agus', 'objects': objects_html})


if __name__ == "__main__":
    build_journal()
