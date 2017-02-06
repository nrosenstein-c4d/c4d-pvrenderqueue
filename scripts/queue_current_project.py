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
This script adds a new FileRenderJob for the current project to the
render queue.
"""

import c4d
import os
import nr.pvrq2


def main():
  if not doc.GetDocumentPath():
    c4d.gui.MessageDialog("Please save your project before queueing.")
    return

  filename = os.path.join(doc.GetDocumentPath(), doc.GetDocumentName())
  job = nr.pvrq2.FileRenderJob(filename)
  nr.pvrq2.root.append(job)
  c4d.EventAdd()


if __name__ == '__main__':
  main()
