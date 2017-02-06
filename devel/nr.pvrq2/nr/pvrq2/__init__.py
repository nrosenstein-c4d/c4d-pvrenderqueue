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
This document describes the #nr.pvrq2 module. It exposes a rich API to develop
extensions that is used internally by the *PV Render Queue 2* plugin as well.

# Example

This is a stripped down version of the `queue_current_project.py` script
that is delivered with the plugin. It simply takes the full path to the
document and creates a new :class:`FileRenderJob` from it, appending as the
last job in the render queue.

```python
import c4d, os
import nr.pvrq2

def main():
  filename = os.path.join(doc.GetDocumentPath(), doc.GetDocumentName())
  job = nr.pvrq2.FileRenderJob(filename)
  nr.pvrq2.root.append(job)
  c4d.EventAdd()

main()
```
"""

from .gui import JobDetailsDialog
from .node import TreeNodeBase
from .ordereddict import OrderedDict
import abc
import c4d
import os
import uuid

__author__ = 'Niklas Rosenstein <rosensteinniklas@gmail.com>'
__version__ = '2.3.0'


STATUS_PENDING = 'pending'      #: Job is pending in the queue
STATUS_RENDERING = 'rendering'  #: Job is currently rendering
STATUS_COMPLETED = 'completed'  #: Job has been completed
STATUS_FAILED = 'failed'        #: Job could not be rendered successfully
STATUS_CANCELLED = 'cancelled'  #: Job was cancelled by the user
STATUS_ALL = [STATUS_PENDING, STATUS_RENDERING, STATUS_COMPLETED,
              STATUS_FAILED, STATUS_CANCELLED]

#: The resource of the PV Render Queue 2 plugin. Will be bound at
#: the time the plugin is loaded.
res = None

# Mapping of the plugins registered with :class:`register_node_plugin`.
job_plugins = {}

#: HyperFile identifier.
HYPERFILE_IDENT = 1037405


class BaseNode(TreeNodeBase):
  '''
  Base class for nodes in the render queue. Provides properties such as an
  elements enabled and selection state. Instances of this class can be
  serialized to and from #c4d.HyperFile objects but their constructor **must**
  be callable with no arguments for that to work.

  # Attributes

  enabled (bool): A #bool flag that is used to determine if the node is
    enabled. In the case of a #RenderJob, this member determines if the job
    should be rendered or skipped.

  selected (bool): A #bool flag that specifies whether the node is selected
    in the GUI or not. This member is not saved during serialization.

  uuid (uuid.UUID): The UUID of the node. This is used to keep track of
    parent-child relationships during the serialization process with #read()
    and #write().

  # Class Members

  disklevel (int): Override on class-level. The disklevel for serialization.

  ident (str): Override on class-level. The identifier for finding the right
    class to read back the node when loading a HyperFile.

  serializable (bool): Override on class-level. True if the implementation is
    serializable, #False if #read() and #write() raise #NotImplementedError.
  '''

  disklevel = 0
  ident = None
  serializable = False

  def __init__(self):
    super(BaseNode, self).__init__()
    self.enabled = True
    self.selected = False
    self.uuid = uuid.uuid4()

  def get_selected_nodes(self, children=True, result=None):
    '''
    Returns a list of the selected nodes including *self*.
    '''

    if result is None:
      result = []
    if self.selected:
      result.append(self)
      if not children:
        return result
    for child in self.iter_children():
      child.get_selected_nodes(children, result)
    return result

  def set_selected(self, selected, recursive=False):
    '''
    Set the selection state of the node, optionally recursively.
    '''

    self.selected = selected
    if recursive:
      for child in self.iter_children():
        child.set_selected(selected, True)

  def iter_tree(self, filter=None):
    '''
    Recursively iterate over the complete tree.
    '''

    for child in self.iter_children():
      if not filter or filter(child):
        yield child
      for sub in child.iter_tree(filter):
        yield sub

  @property
  def enabled_state(self):
    '''
    Returns the enabled state of the node, based on its own state and
    the state of its parent nodes.

    # Returns
    One of `'enabled'`, `'disabled'` or `'tristate'`.
    '''

    if not self.enabled:
      return 'disabled'
    parent = self.parent
    while parent:
      if not parent.enabled:
        return 'tristate'
      parent = parent.parent
    return 'enabled'

  @abc.abstractproperty
  def name(self):
    '''
    Return the name of the node.
    '''

    raise NotImplementedError

  def write(self, hf):
    '''
    Overridable. Write the node to a HyperFile.

    # Parameters
    hf (c4d.storage.HyperFile): The HyperFile to write to.

    # Returns
    #True if the job was written successfully, #False if not.
    '''

    if not hf.WriteBool(self.enabled): return False
    return True

  def read(self, hf, disklevel):
    '''
    Overridable. Read a node from a HyperFile.

    # Parameters
    hf (c4d.storage.HyperFile): The HyperFile to read from.
    disklevel (int): The disklevel of the data that was written to the
      HyperFile, as it was specified to #register_node_plugin().

    # Raises
    NotImplementedError: Default implementation. Should be raised if
      #serializable() is #False.

    # Returns
    The #BaseNode object or None if it could not be read.
    '''

    enabled = hf.ReadBool()
    if enabled is None: return False
    self.enabled = enabled
    return True


class RenderJob(BaseNode):
  '''
  Represents a job that is to be rendered in the Picture Viewer. It is,
  however, an abstract base class that can be subclassed to implement
  custom behaviour of the job (eg. pre-processing before rendering,
  notifications, whatever).

  A RenderJob is not expected to have child nodes.

  Known subclasses: #FileRenderJob

  # Attributes

  render_tr (bool): A #bool flag that specifies whether the job should be
    rendered with Team Render or using the standard Render to Picture Viewer
    command.

  status (str): The status of the job. Any of the following values:

      * #nr.pvrq2.STATUS_PENDING
      * #nr.pvrq2.STATUS_RENDERING
      * #nr.pvrq2.STATUS_COMPLETED
      * #nr.pvrq2.STATUS_FAILED
      * #nr.pvrq2.STATUS_CANCELLED

  error_message (str): #None or a #str if there was an error with the job.

  # Class Members

  resettable (bool): Class-level attribute that specifies if the job is
    resettable using #reset().
  '''

  resettable = False

  def __init__(self):
    super(RenderJob, self).__init__()
    self.render_tr = False
    self.status = STATUS_PENDING
    self.error_message = None

  def __repr__(self):
    return '<{0} name={1!r}>'.format(type(self).__name__, self.name)

  @abc.abstractproperty
  def name(self):  #< BaseNode
    '''
    Return the name of the render job (eg. the name of the scene file).
    '''

    raise NotImplementedError

  def get_job_details(self):
    '''
    Return a dictionary with meta information about the job.
    '''

    return {
      'status': status_str(self.status),
      'error_message': self.error_message}

  def show_job_details(self):
    '''
    Called to open a dialog with information on the job. The default
    implementation will use the dictionary returned by #get_job_details()
    and display it in a dialog.
    '''

    details = self.get_job_details()
    dialog = JobDetailsDialog(self.name, details)
    dialog.Open(c4d.DLG_TYPE_MODAL)

  @abc.abstractmethod
  def get_scene(self):
    '''
    Called to retrieve the Cinema 4d BaseDocument that should be
    rendered in the Picture Viewer. Returns None if the scene could not
    be loaded. The job's status will be set to #STATUS_FAILED.
    '''

    raise NotImplementedError

  def completed(self):
    '''
    Called when the render job completed. It can not be determined if it
    finished successfully or not.
    '''

    pass

  def write(self, hf):
    '''
    Implements writing the RenderJob information to a HyperFile.
    Subclasses must call the parent implementation if they override
    this method.
    '''

    if not super(RenderJob, self).write(hf): return False
    if not hf.WriteBool(self.render_tr): return False
    if self.status == STATUS_RENDERING:
      if not hf.WriteString(STATUS_CANCELLED): return False
    else:
      if not hf.WriteString(self.status): return False
    if not hf.WriteString(self.error_message or ''): return False
    return True

  def read(self, hf, disklevel):
    '''
    Implements reading the RenderJob from a HyperFile.
    Subclasses must call the parent implementation if they override
    this method.
    '''

    if not super(RenderJob, self).read(hf, disklevel): return False
    self.render_tr = hf.ReadBool()
    if self.render_tr is None: return False
    self.status = hf.ReadString()
    if self.status not in STATUS_ALL: return False
    self.error_message = hf.ReadString()
    return True

  def reset(self):
    '''
    Reset the status of the job, allowing it to be processed
    by the render queue once again. This method should only be
    called if #resettable is True.
    '''

    self.status = STATUS_PENDING
    self.error_message = None


class Folder(BaseNode):
  '''
  Represents a folder that can contain a number of render jobs. All
  children of a folder are supposed to be :class:`RenderJob` objects.

  ```python
  folder = nr.pvrq2.Folder('John Doe\'s stuff')
  folder.append(job1)
  folder.append(job2)
  nr.pvrq2.root.append(folder)
  ```
  '''

  def __init__(self, name='???'):
    super(Folder, self).__init__()
    self.name = name
    self.open = True

  def __repr__(self):
    return '<{0} name={1!r} enabled={2!r}>'.format(
      type(self).__name__, self.name, self.enabled)

  #< BaseNode

  name = None
  ident = 'nr.pvrq2.Folder'
  serializable = True

  def write(self, hf):
    if not super(Folder, self).write(hf): return False
    if not hf.WriteString(self.name): return False
    if not hf.WriteBool(self.open): return False
    return True

  def read(self, hf, disklevel):
    if not super(Folder, self).read(hf, disklevel): return False
    self.name = hf.ReadString()
    self.open = hf.ReadBool()
    if self.name is None or self.open is None: return False
    return self


class Root(BaseNode):
  '''
  Represents the root of the render queue. Contains folders and jobs.
  '''

  pass


class FileRenderJob(RenderJob):
  '''
  This class implements a render job from a scene file.
  '''

  def __init__(self, filename=''):
    super(FileRenderJob, self).__init__()
    self.filename = filename

  #< BaseNode

  @property
  def name(self):
    return os.path.basename(self.filename)

  ident = 'nr.pvrq2.FileRenderJob'
  serializable = True

  def write(self, hf):
    if not super(FileRenderJob, self).write(hf): return False
    if not hf.WriteFilename(self.filename): return False
    return True

  def read(self, hf, disklevel):
    if not super(FileRenderJob, self).read(hf, disklevel): return False
    self.filename = hf.ReadFilename()
    if self.filename is None: return False
    return True

  #< RenderJob

  resettable = True

  def get_job_details(self):
    details = super(FileRenderJob, self).get_job_details()
    details['filename'] = self.filename
    return details

  def get_scene(self):
    flags = c4d.SCENEFILTER_OBJECTS | c4d.SCENEFILTER_MATERIALS
    doc = c4d.documents.LoadDocument(self.filename, flags)
    if not doc:
      self.error_message = res.string('IDS_ERROR_FILENOTLOADED', self.filename)
      return None
    return doc


def write_nodes(root, hf):
  '''
  Writes all nodes of *root* into the HyperFile *hf*.

  Note that this function can raise any exception that any
  of the #BaseNode.write() implementations could raise.
  '''

  if root.serializable:
    if not hf.WriteChunkStart(0, 0): return False
    if not hf.WriteString(root.ident): return False
    if not hf.WriteInt32(root.disklevel): return False
    if not hf.WriteString(str(root.uuid)): return False

    # Write the parent UUID.
    if root.parent:
      if not hf.WriteString(str(root.parent.uuid)): return False
    else:
      if not hf.WriteString(''): return False

    if not root.write(hf): return False
    if not hf.WriteChunkEnd(): return False

  for node in root.iter_children():
    if not write_nodes(node, hf):
      return False

  return True


def read_nodes(hf, error_callback=None):
  '''
  Reads all nodes back from the HyperFile *hf* and returns all
  root nodes in a list.

  # Parameters

  hf (c4d.storage.HyperFile): The HyperFile to read from.
  error_callback (function): Called when an error occurs with an
    error type string and a data value. Possible type strings are:

    * `'unknown-plugin'` with the identifier as its data
    * `'read-exception'` with the Python exception as its data
    * `'read-wrong-result'` with the wrong object returned

  # Returns
  #list of #BaseNode.
  '''

  nodes = OrderedDict()
  if not error_callback:
    error_callback = lambda k, v: None

  while hf.ReadValueHeader() == c4d.HYPERFILEVALUE_START:
    chunk = hf.ReadChunkStart()
    if not chunk:
      return False

    # Read the node header information.
    ident = hf.ReadString()
    disklevel = hf.ReadInt32()
    node_uuid = hf.ReadString()
    parent_uuid = hf.ReadString()
    if any(x is None for x in [ident, disklevel, node_uuid, parent_uuid]):
      return False

    node_uuid = uuid.UUID(node_uuid)
    parent_uuid = uuid.UUID(parent_uuid)

    try:
      if ident not in job_plugins:
        error_callback('unknown-plugin', ident)
        continue

      try:
        node = job_plugins[ident]()
        node.uuid = node_uuid
        if not node.read(hf, disklevel):
          error_callback('read-error', node)
          continue
      except BaseException as exc:
        error_callback('read-exception', exc)
        continue

      if not isinstance(node, BaseNode):
        error_callback('read-wrong-result', node)
        continue
    finally:
      hf.SkipToEndChunk()

    nodes[node_uuid] = (node, parent_uuid)

  # Re-establish the child/parent relationships.
  parentless = []
  for node, parent_uuid in nodes.itervalues():
    try:
      parent = nodes[parent_uuid][0]
    except KeyError:
      parentless.append(node)
      continue
    else:
      parent.append(node)

  return parentless


def register_node_plugin(cls):
  '''
  Registers a BaseNode subclass to PV Render Queue, allowing instances
  of that implementation to be serialized when they're in the render
  queue.

  :param cls: A :class:`BaseNode` subclass.
  :raise ValueError: If *cls.ident* is already used.
  :raise TypeError: If *cls* is not a :class:`BaseNode` subclass.
  '''

  if not isinstance(cls.ident, str):
    raise ValueError('invalid identifier, expected str')
  if cls.ident in job_plugins:
    raise ValueError('identifer already used: {0!r}'.format(ident))
  if not issubclass(cls, BaseNode):
    raise TypeError('expected a BaseNode subclass')

  job_plugins[cls.ident] = cls


def get_cache_filename():
  '''
  Returns the filename at which the cache of the queue is saved.
  '''

  return os.path.join(c4d.storage.GeGetC4DPath(c4d.C4D_PATH_PREFS), 'pvrq2.hf')


def is_rendering(node=None):
  '''
  :returns: True if any of the nodes in the tree starting at *node*
    is currently rendering, False if not.
  '''

  if node is None:
    node = root

  if isinstance(node, RenderJob) and node.status == STATUS_RENDERING:
    return True
  for child in node.iter_children():
    if is_rendering(child):
      return True
  return False


def delete_node(node):
  '''
  Deletes a node from the render queue. If a render job is encountered
  that is currently rendering, and the user says not to stop the current
  rendering, nothing will happen.

  :returns: True if the node has been deleted, False if not.
  '''

  if is_rendering(node):
    if not cancel_rendering():
      return False
  node.remove()


def move_selected(direction):
  '''
  Move the selected nodes up or down.

  :param direction: ``'up'`` or ``'down'``
  '''

  if direction not in ('up', 'down'):
    raise ValueError('invalid direction', direction)

  nodes = root.get_selected_nodes(children=False)
  if direction == 'down':
    nodes.reverse()
  for node in nodes:
    if not move_node(node, direction):
      return


def move_node(node, direction):
  '''
  Move the specified *node* up or down.

  :param node: The node to move.
  :param direction: The direction to move the node to.
  :returns: True if the node was moved, False if not.
  '''

  ref = None
  from_folder = isinstance(node.parent, Folder)

  if direction == 'up':
    if node.parent.down is not node:
      ref = node.pred
    elif from_folder:
      ref = node.parent
  elif direction == 'down':
    if node.parent.down_last is not node:
      ref = node.next
    elif from_folder:
      ref = node.parent
  else:
    raise ValueError('invalid direction', direction)

  if not ref:
    return False

  node.remove()
  if direction == 'up':
    if not from_folder and isinstance(ref, Folder):
      ref.append(node)
    else:
      node.insert_before(ref)
  else:
    if not from_folder and isinstance(ref, Folder):
      ref.append(node, 0)
    else:
      node.insert_after(ref)

  return True


def cancel_rendering():
  '''
  Cancels the external rendering. The user will have to reply wether
  the rendering should really be cancelled or not. Returns True if
  the active external rendering was cancelled, False if not.
  '''

  c4d.CallCommand(430000731)  # Stop Rendering...
  return not c4d.CheckIsRunning(c4d.CHECKISRUNNING_EXTERNALRENDERING)


def status_str(status):
  '''
  Converts a render job status to a localized string.
  '''

  if status == STATUS_PENDING:
    return res.string('IDS_STATUS_PENDING')
  elif status == STATUS_RENDERING:
    return res.string('IDS_STATUS_RENDERING')
  elif status == STATUS_COMPLETED:
    return res.string('IDS_STATUS_COMPLETED')
  elif status == STATUS_FAILED:
    return res.string('IDS_STATUS_FAILED')
  elif status == STATUS_CANCELLED:
    return res.string('IDS_STATUS_CANCELLED')
  return '-- invalid status --'


#: :class:`Root` object that contains all :class:`RenderJob` and
#: :class:`Folder` objects.
root = Root()

register_node_plugin(Folder)
register_node_plugin(FileRenderJob)
