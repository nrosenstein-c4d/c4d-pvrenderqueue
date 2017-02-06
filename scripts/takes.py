# PV Render Queue Cinema 4D Plugin
# Copyright (C) 2015  Niklas Rosenstein
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
This script generates a render job for each selected take separately
and adds it to the render queue. Requires Cinema 4D R17.
"""

__author__ = 'Niklas Rosenstein <rosensteinniklas@gmail.com>'
__version__ = '1.0.0'

import c4d
import nr.pvrq2

try:
    import c4d.modules.takesystem as takesystem
except ImportError:
    takesystem = None


class TakeJob(nr.pvrq2.RenderJob):

    def __init__(self, doc, take):
        super(TakeJob, self).__init__()
        self.doc = doc
        self.take = take
        self.scene_name = doc.GetDocumentName()
        self.take_name = take.GetName()

    def get_job_details(self):
        details = super(TakeJob, self).get_job_details()
        details.update({'scene_name': self.scene_name, 'take': self.take_name})
        return details

    @property
    def name(self):
        return self.take.GetName()

    def get_scene(self):
        take_data = self.doc.GetTakeData()
        take_data.SetCurrentTake(self.take)
        return self.doc


def main():
    if not takesystem:
        c4d.gui.MessageDialog('takes available in Cinema 4D R17+')
        return

    global doc
    doc = doc.GetClone(c4d.COPYFLAGS_0)

    take_data = doc.GetTakeData()
    takes = take_data.GetTakeSelection(True)
    if not takes:
        c4d.gui.MessageDialog('no takes selected')
        return

    name = '{0} Takes'.format(doc.GetDocumentName())
    folder = nr.pvrq2.Folder(name)
    for take in takes:
        folder.append(TakeJob(doc, take))
    nr.pvrq2.root.append(folder)
    c4d.EventAdd()


if __name__ == "__main__":
    main()
