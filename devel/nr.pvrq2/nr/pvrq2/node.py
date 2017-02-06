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

class TreeNodeBase(object):
  '''
  A base class to construct tree structures.

  .. attribute:: root

    :getter: Returns the root of the tree.
    :type: :class:`TreeNodeBase`

  .. attribute:: parent

    :getter: Returns the parent node of this node.
    :type: :class:`TreeNodeBase`

  .. attribute:: next

    :getter: Returns the next node of this node.
    :type: :class:`TreeNodeBase`

  .. attribute:: pred

    :getter: Returns the preceding node of this node.
    :type: :class:`TreeNodeBase`

  .. attribute:: down

    :getter: Returns the first child node of this node.
    :type: :class:`TreeNodeBase`

  .. attribute:: down_last

    :getter: Returns the last child node of this node.
    :type: :class:`TreeNodeBase`

  .. attribute:: children

    :getter: Returns a list of the node's children.
    :type: :class:`list` of :class:`TreeNodeBase`
  '''

  def __init__(self):
    super(TreeNodeBase, self).__init__()
    self.__parent = None
    self.__next = None
    self.__pred = None
    self.__down = None
    self.__down_last = None

  def __assert_dangling(self, param):
    if not self.is_dangling():
      message = '<{0}> is already in a hierarchy'.format(param)
      raise RuntimeError(message, self)

  def is_dangling(self):
    '''
    Returns True if the node is a dangling node, meaning it is not
    inserted in a hierarchy. A dangling node has no parent or
    neighbouring nodes.
    '''

    return not (self.__parent or self.__next or self.__pred)

  def get_root(self):
    root = self
    while root.__parent:
      root = root.__parent
    return root

  def get_parent(self):
    return self.__parent

  def get_next(self):
    return self.__next

  def get_pred(self):
    return self.__pred

  def get_down(self):
    return self.__down

  def get_down_last(self):
    return self.__down_last

  def get_children(self):
    children = []
    child = self.__down
    while child:
      children.append(child)
      child = child.__next
    return children

  def remove(self):
    '''
    Removes the node from the parent and neighbouring nodes. Does
    not detach child nodes.
    '''

    if self.__parent:
      if self is self.__parent.__down:
        self.__parent.__down = self.__next
      if self is self.__parent.__down_last:
        self.__parent.__down_last = self.__pred
    if self.__next:
      self.__next.__pred = self.__pred
    if self.__pred:
      self.__pred.__next = self.__next
    self.__parent = None
    self.__next = None
    self.__pred = None

  def insert_after(self, node):
    '''
    Inserts *self* after *node*. *self* must be free (not in a
    hierarchy) and *node* must have a parent node, otherwise a
    :class:`RuntimeError` is raised.
    '''

    if not isinstance(node, TreeNodeBase):
      raise TypeError('<node> must be TreeNodeBase instance', type(node))
    self.__assert_dangling('self')
    if not node.__parent:
      raise RuntimeError('<node> must have a parent node', node)

    self.__parent = node.__parent
    if node.__next:
      node.__next.__pred = self
    else:
      assert self.__parent.__down_last is node
      self.__parent.__down_last = self
    self.__next = node.__next
    node.__next = self
    self.__pred = node

  def insert_before(self, node):
    '''
    Inserts *self* before *node*. *self* must be free (not in a
    hierarchy) and *node* must have a parent node, otherwise a
    :class:`RuntimeError` is raised.
    '''

    if not isinstance(node, TreeNodeBase):
      raise TypeError('<node> must be TreeNodeBase instance', type(node))
    self.__assert_dangling('self')
    if not node.__parent:
      raise RuntimeError('<node> must have a parent node', node)

    self.__parent = node.__parent
    if node.__pred:
      node.__pred.__next = self
    else:
      assert node is self.__parent.__down
      self.__parent.__down = self
    self.__pred = node.__pred
    node.__pred = self
    self.__next = node

  def append(self, node, index=None):
    '''
    Appends *node* at the specified *index*. If *index* is None,
    *node* will be inserted at the end of the children list. The
    *index* can not be a negative value as it would need to count
    the number of childrens first.
    '''

    if not isinstance(node, TreeNodeBase):
      raise TypeError('<node> must be TreeNodeBase instance', type(node))
    if index is not None and not isinstance(index, int):
      raise TypeError('<index> must be None or int', type(index))
    if index is not None and index < 0:
      raise ValueError('<index> must be None or positive int', index)

    # Make sure the node is not already in a hierarchy.
    node.__assert_dangling('node')

    # Even if the node that is to be inserted is free, it could
    # still be the root of the hierarchy which would be free.
    if node is self.root:
      raise RuntimeError('can not insert <root> node into its hierarchy', node)

    assert bool(self.__down) == bool(self.__down_last), \
      "TreeNodeBase.down and TreeNodeBase.down_last out of balance (" + self.name + ")"

    if not self.__down:
      self.__down = node
      self.__down_last = node
      node.__parent = self
    else:
      if index is not None:
        dest = self.__down
        child_index = 0
        while dest and child_index < index:
          dest = dest.__next
          child_index += 1
      else:
        dest = None

      if dest:
        node.insert_before(dest)
      else:
        node.insert_after(self.__down_last)

  def iter_children(self, recursive=False):
    '''
    Iterator for the children of this node. If *recursive* is True,
    the function will iterate recursively over all children as well.
    '''

    child = self.down
    while child:
      next = child.next
      if recursive:
        for x in child.iter_children(True):
          yield x
      yield child
      child = next

  def flush_children(self):
    '''
    Remove all child nodes from this node.
    '''

    while self.down:
      self.down.remove()

  root = property(get_root)
  parent = property(get_parent)
  next = property(get_next)
  pred = property(get_pred)
  down = property(get_down)
  down_last = property(get_down_last)
  children = property(get_children)
