
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
import base64
import json
import dbus
from zipfile import ZipFile


def package_ds_object(dsobj, destination_path):
    """
    Creates a zipped file with the file associated to a journal object,
    the preview and the metadata
    """
    object_id = dsobj.object_id
    preview_path = None

    if 'preview' in dsobj.metadata:
        # TODO: copied from expandedentry.py
        # is needed because record is saving the preview encoded
        if dsobj.metadata['preview'][1:4] == 'PNG':
            preview = dsobj.metadata['preview']
        else:
            # TODO: We are close to be able to drop this.
            preview = base64.b64decode(dsobj.metadata['preview'])

        preview_path = os.path.join(destination_path,
                                    'preview_id_' + object_id)
        preview_file = open(preview_path, 'w')
        preview_file.write(preview)
        preview_file.close()

    # create file with the metadata
    metadata_path = os.path.join(destination_path,
                                 'metadata_id_' + object_id)
    metadata_file = open(metadata_path, 'w')
    metadata = {}
    for key in dsobj.metadata.keys():
        if key not in ('object_id', 'preview', 'progress'):
            metadata[key] = dsobj.metadata[key]
    metadata_file.write(json.dumps(metadata))
    metadata_file.close()

    # create a zip fileincluding metadata and preview
    # to be read from the web server
    file_path = os.path.join(destination_path, 'id_' + object_id + '.journal')

    with ZipFile(file_path, 'w') as myzip:
        if preview_path is not None:
            myzip.write(preview_path, 'preview')
        myzip.write(metadata_path, 'metadata')
        myzip.write(dsobj.file_path, 'data')
    return file_path


def unpackage_ds_object(origin_path, dsobj=None):
    """
    Receive a path of a zipped file, unzip it, and save the data,
    preview and metadata on a journal object
    """
    tmp_path = os.path.dirname(origin_path)
    with ZipFile(origin_path) as zipped:
        metadata = json.loads(zipped.read('metadata'))
        preview_data = zipped.read('preview')
        zipped.extract('data', tmp_path)

    if dsobj is not None:
        for key in metadata.keys():
            dsobj.metadata[key] = metadata[key]

        dsobj.metadata['preview'] = dbus.ByteArray(preview_data)

        dsobj.file_path = os.path.join(tmp_path, 'data')
    else:
        return metadata, preview_data, os.path.join(tmp_path, 'data')
