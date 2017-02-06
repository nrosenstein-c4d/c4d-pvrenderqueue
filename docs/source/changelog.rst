Changelog
=========

v2.3

* Fix issue with pre-R17 versions of Cinema 4D embedding Python 2.6
  which does not have ``collections.OrderedDict`` by adding
  ``nr.pvrq2.ordereddict.OrderedDict``

v2.2

* Add the current project to the queue with the new `queue_current_project.py` script
* Automatically save the render queue persistently when the plugin is closed
  and load it when its opened
* API Changes

  * Add `BaseNode.uuid`, `.ident`, `.disklevel`, `.serializable`,
    `.read()` and `.write()`
  * Add `nr.pvrq2.register_node_plugin()`
  * Add `TreeNode.iter_children(recursive=False)` parameter

v2.1

* Added HTML documentation to the plugin and hosted online here
* Updated API documentation
* Updated Links in the plugin's "Help" menu and README

v2.0

* Initial 2.0 version with improved user interface, new functionality
  and scripting API
