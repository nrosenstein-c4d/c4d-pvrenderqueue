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

class _Item(object):
  __slots__ = ('key', 'value')

  def __init__(self, key, value):
    self.key = key
    self.value = value

class OrderedDict(object):
  '''
  A very basic implementation of an ordered dictionary.
  '''

  def __init__(self, iterable=()):
    self._items = []
    for key, value in iterable:
      self[key] = value

  def __getitem__(self, needle):
    for item in self._items:
      if item.key == needle:
        return item.value
    raise KeyError(needle)

  def __setitem__(self, needle, value):
    for item in self._items:
      if item.key == needle:
        item.value = value
        return
    self._items.append(_Item(needle, value))

  def __delitem__(self, needle):
    for index, item in self._items:
      if item.key == needle:
        break
    else:
      raise KeyError(needle)
    del self._items[index]

  def __iter__(self):
    return self.iterkeys()

  def iterkeys(self):
    for item in self._items:
      yield item.key

  def itervalues(self):
    for item in self._items:
      yield item.value

  def iteritems(self):
    for item in self._items:
      yield (item.key, item.value)

  def keys(self):
    return list(self.iterkeys())

  def values(self):
    return list(self.itervalues())

  def items(self):
    return list(self.iteritems())
