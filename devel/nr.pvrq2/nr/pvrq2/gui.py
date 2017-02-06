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

import c4d


class JobDetailsDialog(c4d.gui.GeDialog):
  '''
  This dialog takes a dictionary as input and displays all key value
  pairs in a two-column table.
  '''

  def __init__(self, title, data):
    super(JobDetailsDialog, self).__init__()
    self.title = title
    self.data = data
    self.counter = 0

  def _AddLine(self, key, value):
    if value is None:
      return
    try:
      value = str(value)
    except Exception as exc:
      value = str(exc)
    self.AddStaticText(self.counter, c4d.BFH_LEFT, name=key)
    self.counter += 1
    if '\n' in value:
      style = c4d.DR_MULTILINE_READONLY
      self.AddMultiLineEditText(
        self.counter, c4d.BFH_SCALEFIT, 200, 30, style=style)
      self.SetString(self.counter, value)
      self.counter += 1
    else:
      self.AddStaticText(
        self.counter, c4d.BFH_SCALEFIT, name=value,
        borderstyle=c4d.BORDER_THIN_IN)
      self.counter += 1

  #< c4d.gui.GeDialog

  def CreateLayout(self):
    self.SetTitle(self.title)
    self.counter = 1000
    self.GroupBegin(0, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, cols=2, rows=0)
    for key, value in self.data.items():
      self._AddLine(key, value)
    self.GroupEnd()
    self.AddDlgGroup(c4d.DLG_OK)
    return True

  def Command(self, wid, bc):
    if wid == c4d.DLG_OK:
      self.Close()
    return True
