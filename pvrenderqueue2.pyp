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

from __future__ import print_function
from importlib import reload

DEBUG = True

#######################################################################

import os
import sys

exec ("""class res(object):
 # Automatically generated using the Craftr maxon.c4d module
 project_path = os.path.dirname(__file__)
 def string(self, name, *subst):
  result = __res__.LoadString(getattr(self, name))
  for item in subst: result = result.replace('#', item, 1)
  return result
 def tup(self, name, *subst):
  return (getattr(self, name), self.string(name, *subst))
 def file(self, *parts):
  return os.path.join(self.project_path, *parts)
 def bitmap(self, *parts):
  b = c4d.bitmaps.BaseBitmap()
  if b.InitWith(self.file(*parts))[0] != c4d.IMAGERESULT_OK: return None
  return b
 DLG_PVRQ2 = 10001
 BTN_START = 10002
 BTN_ADD_FILE = 10003
 BTN_ADD_FOLDER = 10004
 GUI_TREEVIEW = 10005
 IDS_ERROR_FILENOTLOADED = 10006
 IDS_ERROR_JOBRETURNEDNONE = 10007
 IDS_ERROR_NOTC4DFILE = 10008
 IDS_RMB_CANCEL = 10009
 IDS_RMB_JOBDETAILS = 10010
 IDS_RMB_RESET = 10011
 IDS_COL_ENABLED = 10012
 IDS_COL_RENDERTR = 10013
 IDS_COL_JOBNAME = 10014
 IDS_COL_STATUS = 10015
 IDS_STATUS_PENDING = 10016
 IDS_STATUS_RENDERING = 10017
 IDS_STATUS_COMPLETED = 10018
 IDS_STATUS_FAILED = 10019
 IDS_STATUS_CANCELLED = 10020
 IDS_MENU_SCRIPTS = 10021
 IDS_MENU_HELP = 10022
 IDS_MENU_HELP_VISITDEV = 10023
 IDS_MENU_HELP_DOCS = 10024
 IDS_MENU_HELP_APIDOCS = 10025
 IDS_MENU_HELP_PLUGINPAGE = 10026
 IDS_SAVEERRORS = 10027
 IDS_ASKCLOSE = 10028
 ID_SCRIPTS_BEGIN = 200000
 ID_SCRIPTS_END = 200500\n""" + "res = res()")

#######################################################################

def setup_pvrq2_namespace():
  module_path = res.file('devel/nr.pvrq2')
  if not os.path.exists(module_path):
    module_path = res.file('res', 'modules' + sys.version[:3], 'nr.pvrq2.egg')
  if module_path not in sys.path:
    sys.path.append(module_path)

  # We pre-emptively append the path to the nr.pvrq2 namespace package
  # to make sure it can be found.
  import nr
  _add_path = os.path.join(module_path, 'nr')
  if _add_path not in nr.__path__:
    nr.__path__.append(_add_path)

setup_pvrq2_namespace()

import errno
import c4d
import glob
import nr.pvrq2 as pvrq2
import traceback
import webbrowser

if DEBUG: reload(pvrq2)

pvrq2.res = res

# This event seems to be sent to CoreMessage() when external
# rendering started or stopped. Unfortunately, it seems to be
# documented nowhere.
EVMSG_EXTERNALRENDERING = 430000697

class settings:
  url_dev = 'http://niklasrosenstein.com'
  url_docs = 'http://docs.niklasrosenstein.com/pvrenderqueue'
  url_apidoc = 'http://docs.niklasrosenstein.com/pvrenderqueue/api.html'
  url_plugin = 'https://niklasrosenstein.com/2015/08/pv-render-queue-2/'

#######################################################################

def set_bitmap_button_image(dlg, wid, bmp):
  '''
  Sets the image for a BitmapButton Custom GUI in *dlg* under the
  specified *wid* to *bmp*. *bmp* can be a string in which case an
  icon is loaded from the resources icon folder.
  '''

  if isinstance(bmp, str):
    path = res.file('res', 'icons', bmp)
    bmp = c4d.bitmaps.BaseBitmap()
    if bmp.InitWith(path)[0] != c4d.IMAGERESULT_OK:
      return False
  gui = dlg.FindCustomGui(wid, c4d.CUSTOMGUI_BITMAPBUTTON)
  if not gui:
    return False
  gui.SetImage(bmp)
  return True


def attach_tree_model(dlg, wid, model, root=None, userdata=None):
  '''
  Attaches the :class:`c4d.gui.TreeViewFunctions` *model* to the
  tree view of the dialog *dlg* under the id *wid*. If the *model*
  supports a ``SetupLayout()`` method, it will be called by this
  function.
  '''

  gui = dlg.FindCustomGui(wid, c4d.CUSTOMGUI_TREEVIEW)
  if not gui:
    return False
  gui.SetRoot(root, model, userdata)
  if hasattr(model, 'SetupLayout'):
    model.SetupLayout(gui)
  return True


def refresh_tree_view(dlg, wid):
  '''
  Refreshes the tree view of the dialog *dlg* in the specified *wid*.
  '''

  gui = dlg.FindCustomGui(wid, c4d.CUSTOMGUI_TREEVIEW)
  if gui:
    gui.Refresh()
    return True
  return False


def remove_document(doc, new_active_doc=None):
  r"""
  Removes the document *doc* from the list of documents in Cinema 4D
  and activates the next or a new document. This is similar to the
  :func:`c4d.documents.KillDocument` function, but on the contrary,
  *doc* will not be deallocated and still be valid.
  If *new_active_doc* is specified, it will be set as the new active
  document instead of the determined successor.
  """

  if type(doc) is not c4d.documents.BaseDocument:
      raise TypeError("doc must be a BaseDocument object")
  if new_active_doc is not None and \
          type(new_active_doc) is not c4d.documents.BaseDocument:
      raise TypeError("new_active_doc must be a BaseDocument object")

  successor = new_active_doc or doc.GetPred() or doc.GetNext()
  doc.Remove()

  # Note: The document will be removed before eventually inserting
  # a new document because if *doc* is the active document and is
  # empty, InsertBaseDocument will actually kill it before inserting
  # the new document.

  if not successor:
      successor = c4d.documents.BaseDocument()
      c4d.documents.InsertBaseDocument(successor)

  c4d.documents.SetActiveDocument(successor)


def run_script(filename):
  try:
    with open(filename, 'r') as fp:
      code = fp.read()
  except (IOError, OSError):
    traceback.print_exc()
    return
  doc = c4d.documents.GetActiveDocument()
  scope = {
    'doc': doc,
    'op': doc.GetActiveObject(),
    'mat': doc.GetActiveMaterial(),
    'tag': doc.GetActiveTag(),
    '__name__': '__main__',
    '__file__': filename}
  try:
    exec(compile(code, filename, 'exec'), scope)
  except BaseException:
    traceback.print_exc()


def silent_remove(filename):
  try:
    os.remove(filename)
  except OSError as exc:
    if exc.errno != errno.ENOENT:
      raise

#######################################################################

class JobTreeModel(c4d.gui.TreeViewFunctions):
  '''
  Handles the display and interaction to manage render jobs and folders.
  An element returned by any of the Get functions is a tuple of
  `(parent folder, child_index)`.
  '''

  HPAD = 2
  VPAD = 2

  def SetupLayout(self, tree_view):
    layout = c4d.BaseContainer()
    layout.SetInt32(res.IDS_COL_ENABLED, c4d.LV_CHECKBOX)
    layout.SetInt32(res.IDS_COL_RENDERTR, c4d.LV_CHECKBOX)
    layout.SetInt32(res.IDS_COL_JOBNAME, c4d.LV_TREE)
    layout.SetInt32(res.IDS_COL_STATUS, c4d.LV_USER)
    tree_view.SetLayout(4, layout)
    tree_view.SetHeaderText(*res.tup('IDS_COL_ENABLED'))
    tree_view.SetHeaderText(*res.tup('IDS_COL_RENDERTR'))
    tree_view.SetHeaderText(*res.tup('IDS_COL_JOBNAME'))
    tree_view.SetHeaderText(*res.tup('IDS_COL_STATUS'))

  #< c4d.gui.TreeViewFunctions

  def GetFirst(self, root, ud):
    return root.down

  def GetNext(self, root, ud, node):
    return node.next

  def GetPred(self, root, ud, node):
    return node.pred

  def GetDown(self, root, ud, node):
    return node.down

  def GetUp(self, root, ud, node):
    return node.parent

  def GetName(self, root, ud, node):
    try:
      return node.name
    except BaseException:
      traceback.print_exc()
      return '???'

  def IsChecked(self, root, ud, node, col):
    if col == res.IDS_COL_ENABLED:
      if isinstance(node, pvrq2.RenderJob):
        if node.status != pvrq2.STATUS_PENDING:
          return 0
      result = c4d.LV_CHECKBOX_ENABLED
      state = node.enabled_state
      if state == 'enabled':
        result |= c4d.LV_CHECKBOX_CHECKED
      elif state == 'tristate':
        result |= c4d.LV_CHECKBOX_TRISTATE
      return result
    elif col == res.IDS_COL_RENDERTR:
      if isinstance(node, pvrq2.RenderJob):
        if node.status != pvrq2.STATUS_PENDING:
          return 0
        result = c4d.LV_CHECKBOX_ENABLED
        if node.render_tr:
          result |= c4d.LV_CHECKBOX_CHECKED
      else:
        result = 0
      return result
    return 0

  def SetCheck(self, root, ud, node, col, checked, msg):
    if col == res.IDS_COL_ENABLED:
      node.enabled = checked
    elif col == res.IDS_COL_RENDERTR:
      if isinstance(node, pvrq2.RenderJob):
        node.render_tr = checked

  def IsSelected(self, root, ud, node):
    return node.selected

  def Select(self, root, ud, node, mode):
    if mode == c4d.SELECTION_NEW:
      root.set_selected(False, recursive=True)
      if node:
        node.selected = True
    elif mode == c4d.SELECTION_ADD:
      node.selected = True
    elif mode == c4d.SELECTION_SUB:
      node.selected = False

  def GetColumnWidth(self, root, ud, node, col, area):
    width = 0
    if col == res.IDS_COL_STATUS and isinstance(node, pvrq2.RenderJob):
      text = pvrq2.status_str(node.status)
      width = area.DrawGetTextWidth(text) + self.HPAD * 2
    return width

  def DrawCell(self, root, ud, node, col, drawinfo, bg_color):
    area = drawinfo['frame']
    w, h = drawinfo['width'], drawinfo['height']
    x, y = drawinfo['xpos'] + self.HPAD, drawinfo['ypos'] + self.VPAD
    ymid = y - self.VPAD + h / 2

    text = None
    if col == res.IDS_COL_STATUS and isinstance(node, pvrq2.RenderJob):
      text = pvrq2.status_str(node.status)

    if text is not None:
      area.DrawText(text, x, ymid, c4d.DRAWTEXT_VALIGN_CENTER)
      x += area.DrawGetTextWidth(text) + self.HPAD

  def DeletePressed(self, root, ud):
    selected = root.get_selected_nodes(children=False)
    if any(pvrq2.is_rendering(node) for node in selected):
      if not pvrq2.cancel_rendering():
        return
    [node.remove() for node in selected]

  def DoubleClick(self, root, ud, node, col, mouseinfo):
    return self.ContextMenuCall(root, ud, node, col, res.IDS_RMB_JOBDETAILS)

  def CreateContextMenu(self, root, ud, node, col, bc):
    bc.RemoveData(c4d.ID_TREEVIEW_CONTEXT_RESET)
    if isinstance(node, pvrq2.RenderJob):
      if node.status == pvrq2.STATUS_RENDERING:
        bc.SetString(*res.tup('IDS_RMB_CANCEL'))
      bc.SetString(*res.tup('IDS_RMB_JOBDETAILS'))
      if node.status not in (pvrq2.STATUS_PENDING, pvrq2.STATUS_RENDERING):
        if node.resettable:
          bc.SetString(*res.tup('IDS_RMB_RESET'))

  def ContextMenuCall(self, root, ud, node, col, command):
    if command == res.IDS_RMB_CANCEL:
      if isinstance(node, pvrq2.RenderJob):
        if node.status == pvrq2.STATUS_RENDERING and pvrq2.cancel_rendering():
          node.status = pvrq2.STATUS_CANCELLED
          c4d.EventAdd()
      return True
    elif command == res.IDS_RMB_JOBDETAILS:
      if isinstance(node, pvrq2.RenderJob):
        try:
          node.show_job_details()
        except BaseException:
          traceback.print_exc()
      return True
    elif command == res.IDS_RMB_RESET:
      if isinstance(node, pvrq2.RenderJob) and node.resettable:
        node.reset()
        c4d.EventAdd()
      return True
    return False


class RQDialog(c4d.gui.GeDialog):
  '''
  The main dialog that implements the user interaction and management
  of the render queue.
  '''

  def __init__(self, msg_data):
    super(RQDialog, self).__init__()
    self.msg_data = msg_data
    self.scripts = []
    self.last_save_notice = None

  @property
  def running(self):
    return self.msg_data.running

  @running.setter
  def running(self, value):
    self.msg_data.running = value

  def BuildMenu(self):
    self.scripts = glob.glob(os.path.join(res.file('scripts'), '*.py'))
    self.MenuFlushAll()
    if self.scripts:
      self.MenuSubBegin(res.string('IDS_MENU_SCRIPTS'))
      for index, script in enumerate(self.scripts):
        idx = res.ID_SCRIPTS_BEGIN + index
        self.MenuAddString(idx, os.path.basename(script))
      self.MenuSubEnd()
    self.MenuSubBegin(res.string('IDS_MENU_HELP'))
    self.MenuAddString(*res.tup('IDS_MENU_HELP_VISITDEV'))
    self.MenuAddString(*res.tup('IDS_MENU_HELP_PLUGINPAGE'))
    self.MenuAddString(*res.tup('IDS_MENU_HELP_DOCS'))
    self.MenuAddString(*res.tup('IDS_MENU_HELP_APIDOCS'))
    self.MenuSubEnd()
    self.MenuFinished()

  def InputEvent(self, bc):
    device = bc.GetInt32(c4d.BFM_INPUT_DEVICE)
    channel = bc.GetInt32(c4d.BFM_INPUT_CHANNEL)
    if device == c4d.BFM_INPUT_KEYBOARD:
      if channel == c4d.KEY_UP:
        pvrq2.move_selected('up')
        c4d.EventAdd()
        return True
      elif channel == c4d.KEY_DOWN:
        pvrq2.move_selected('down')
        c4d.EventAdd()
        return True
    return False

  def SaveCache(self):
    self.last_save_notice = None
    filename = pvrq2.get_cache_filename()
    hf = c4d.storage.HyperFile()
    if not hf.Open(pvrq2.HYPERFILE_IDENT, filename, c4d.FILEOPEN_WRITE, c4d.FILEDIALOG_NONE):
      self.last_save_notice = '{0!r} could not be opened'.format(filename)  # xxx: localization
      return False

    # Check if there are any nodes that can not be saved (except
    # for the root node).
    errors = []
    for node in pvrq2.root.iter_children(recursive=True):
      if not node.serializable:
        errors.append('{0!r} can not be saved persistently'.format(node.name))

    try:
      success = pvrq2.write_nodes(pvrq2.root, hf)
    except BaseException as exc:
      if DEBUG:
        traceback.print_exc()
      errors.append('could not be saved: ' + str(exc))
      success = False
    finally:
      hf.Close()
      self.last_save_notice = '\n'.join(errors)

    if not success:
      silent_remove(filename)

    return success

  @staticmethod
  def LoadCache(flush_old=True):
    if flush_old:
      pvrq2.root.flush_children()

    filename = pvrq2.get_cache_filename()
    hf = c4d.storage.HyperFile()
    if not hf.Open(pvrq2.HYPERFILE_IDENT, filename, c4d.FILEOPEN_READ, c4d.FILEDIALOG_NONE):
      return False

    def error_callback(kind, data):
      print('[PV Render Queue 2]: LoadCache:', kind, data)

    try:
      nodes = pvrq2.read_nodes(hf, error_callback)
    except BaseException as exc:
      if DEBUG:
        traceback.print_exc()
      c4d.gui.MessageDialog(str(exc))
      return False

    for node in nodes:
      pvrq2.root.append(node)
    return True

  #< c4d.gui.GeDialog

  def CreateLayout(self):
    if not self.LoadDialogResource(res.DLG_PVRQ2):
      return False
    self.BuildMenu()
    set_bitmap_button_image(self, res.BTN_START, 'btn_start_off.png')
    set_bitmap_button_image(self, res.BTN_ADD_FILE, 'btn_add_file.png')
    set_bitmap_button_image(self, res.BTN_ADD_FOLDER, 'btn_add_folder.png')
    attach_tree_model(self, res.GUI_TREEVIEW, JobTreeModel(), pvrq2.root)
    return True

  def InitValues(self):
    self.LoadCache()
    return True

  def Command(self, wid, bc):
    if wid == res.BTN_ADD_FILE:
      filename = c4d.storage.LoadDialog(c4d.FILESELECTTYPE_SCENES)
      if filename:
        if not filename.endswith('.c4d'):
          c4d.gui.MessageDialog(res.string('IDS_ERROR_NOTC4DFILE'))
        else:
          pvrq2.root.append(pvrq2.FileRenderJob(filename))
          self.SaveCache()
          c4d.EventAdd()
      return True
    elif wid == res.BTN_ADD_FOLDER:
      filename = c4d.storage.LoadDialog(flags=c4d.FILESELECT_DIRECTORY)
      if filename:
        scenes = glob.glob(os.path.join(filename, '*.c4d'))
        if scenes:
          folder = pvrq2.Folder(os.path.basename(filename))
          pvrq2.root.append(folder)
          c4d.EventAdd()
          [folder.append(pvrq2.FileRenderJob(x)) for x in scenes]
          self.SaveCache()
      return True
    elif wid == res.BTN_START:
      if self.running:
        # Only ask the user to cancel the rendering.
        pvrq2.cancel_rendering()
      self.running = not self.running
      c4d.EventAdd()
    elif wid == res.IDS_MENU_HELP_VISITDEV:
      webbrowser.open(settings.url_dev)
      return True
    elif wid == res.IDS_MENU_HELP_DOCS:
      webbrowser.open(settings.url_docs)
      return True
    elif wid == res.IDS_MENU_HELP_APIDOCS:
      webbrowser.open(settings.url_apidoc)
      return True
    elif wid == res.IDS_MENU_HELP_PLUGINPAGE:
      webbrowser.open(settings.url_plugin)
      return True
    elif wid >= res.ID_SCRIPTS_BEGIN and wid <= res.ID_SCRIPTS_END:
      index = wid - res.ID_SCRIPTS_BEGIN
      try:
        filename = self.scripts[index]
      except IndexError:
        print("[PV Render Queue 2]: Script index out of range.", index)
      else:
        run_script(filename)
        self.SaveCache()
      return True
    return False

  def CoreMessage(self, mid, bc):
    if mid == c4d.EVMSG_CHANGE:
      icon = ('btn_start_off.png', 'btn_start_on.png')[bool(self.running)]
      set_bitmap_button_image(self, res.BTN_START, icon)
      refresh_tree_view(self, res.GUI_TREEVIEW)
    return super(RQDialog, self).CoreMessage(mid, bc)

  def Message(self, msg, result):
    if msg.GetId() == c4d.BFM_INPUT:
      return self.InputEvent(msg)
    return super(RQDialog, self).Message(msg, result)

  def AskClose(self):
    self.SaveCache()
    if self.last_save_notice:
      msg = res.string('IDS_ASKCLOSE')
      msg = res.string('IDS_SAVEERRORS', msg, '\n\n' + self.last_save_notice)
      result = c4d.gui.MessageDialog(msg, c4d.GEMB_YESNO)
      if result != c4d.GEMB_R_YES:
        return True  # don't close!
    return False


class RQCommand(c4d.plugins.CommandData):
  '''
  The plugin command that opens the dialog.
  '''

  PLUGIN_ID = 1035722
  PLUGIN_NAME = 'PV Render Queue 2'
  PLUGIN_FLAG = 0
  PLUGIN_HELP = ''

  def __init__(self, msg_data):
    super(RQCommand, self).__init__()
    self.msg_data = msg_data

  @property
  def dialog(self):
    if not hasattr(self, '_dialog'):
      self._dialog = RQDialog(self.msg_data)
    return self._dialog

  def Register(self):
    icon = None
    return c4d.plugins.RegisterCommandPlugin(
      self.PLUGIN_ID, self.PLUGIN_NAME, self.PLUGIN_FLAG,
      icon, self.PLUGIN_HELP, self)

  #< c4d.plugins.CommandData

  def Execute(self, doc):
    return self.dialog.Open(c4d.DLG_TYPE_ASYNC, self.PLUGIN_ID,
      defaultw=400, defaulth=210)

  def RestoreLayout(self, secret):
    return self.dialog.Restore(self.PLUGIN_ID, secret)


class RQMessageData(c4d.plugins.MessageData):
  '''
  This plugin handles the actual processing of the render queue.
  '''

  PLUGIN_ID = 1035723
  PLUGIN_NAME ="PV Render Queue 2 - Message Data"
  PLUGIN_FLAG = 0

  def __init__(self):
    super(RQMessageData, self).__init__()
    self.running = False

  def Register(self):
    return c4d.plugins.RegisterMessagePlugin(
      self.PLUGIN_ID, self.PLUGIN_NAME, self.PLUGIN_FLAG, self)

  def ProcessQueue(self):
    # If the renderer is not running and we have a running job,
    # the job must have finished now!
    next_up = None
    render_tr = False
    for node in pvrq2.root.iter_tree(lambda x: isinstance(x, pvrq2.RenderJob)):
      if node.status == pvrq2.STATUS_RENDERING:
        node.status = pvrq2.STATUS_COMPLETED
        try:
          node.completed()
        except BaseException:
          traceback.print_exc()
        c4d.EventAdd()
      elif node.status == pvrq2.STATUS_PENDING and self.running:
        if next_up is None and node.enabled_state == 'enabled':
          try:
            next_up = node.get_scene()
          except BaseException:
            node.status = pvrq2.STATUS_FAILED
            node.error_message = traceback.format_exc()
            print(node.error_message, file=sys.stderr)
          else:
            if next_up is None:
              node.status = pvrq2.STATUS_FAILED
              if not node.error_message:
                node.error_message = res.string('IDS_ERROR_JOBRETURNEDNONE')
            else:
              node.status = pvrq2.STATUS_RENDERING
              render_tr = node.render_tr

    if next_up:
      remove = False
      if not next_up.GetListHead():
        remove = True
        c4d.documents.InsertBaseDocument(next_up)
      c4d.documents.SetActiveDocument(next_up)
      if render_tr:
        c4d.CallCommand(300002144)  # Team Render to Picture Viewer
      else:
        c4d.CallCommand(12099)  # Render to Picture Viewer
      if remove:
        remove_document(next_up)
      c4d.EventAdd()
    elif self.running:
      c4d.EventAdd()
      self.running = False

  #< c4d.plugins.MessageData

  def GetTimer(self):
    return 2000

  def CoreMessage(self, event_id, bc):
    if event_id in (EVMSG_EXTERNALRENDERING, c4d.EVMSG_CHANGE, c4d.MSG_TIMER):
      if not c4d.CheckIsRunning(c4d.CHECKISRUNNING_EXTERNALRENDERING):
        self.ProcessQueue()
    return True


def main():
  if c4d.GetC4DVersion() < 15000:
    return
  msg_data = RQMessageData()
  msg_data.Register()
  RQCommand(msg_data).Register()


if __name__ == '__main__':
  main()
