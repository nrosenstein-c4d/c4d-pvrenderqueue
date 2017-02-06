PV Render Queue API Documentation
=================================

.. automodule:: nr.pvrq2

Data
~~~~

.. autodata:: nr.pvrq2.STATUS_PENDING
.. autodata:: nr.pvrq2.STATUS_RENDERING
.. autodata:: nr.pvrq2.STATUS_COMPLETED
.. autodata:: nr.pvrq2.STATUS_FAILED
.. autodata:: nr.pvrq2.STATUS_CANCELLED
.. autodata:: nr.pvrq2.res
.. autodata:: nr.pvrq2.root

Functions
~~~~~~~~~

.. autofunction:: nr.pvrq2.register_node_plugin
.. autofunction:: nr.pvrq2.get_cache_filename
.. autofunction:: nr.pvrq2.is_rendering
.. autofunction:: nr.pvrq2.delete_node
.. autofunction:: nr.pvrq2.move_selected
.. autofunction:: nr.pvrq2.move_node
.. autofunction:: nr.pvrq2.cancel_rendering
.. autofunction:: nr.pvrq2.status_str


RenderJob Objects
~~~~~~~~~~~~~~~~~

.. autoclass:: nr.pvrq2.RenderJob
  :members:
  :show-inheritance:

FileRenderJob Objects
~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: nr.pvrq2.FileRenderJob
  :members:
  :show-inheritance:

Folder Objects
~~~~~~~~~~~~~~

.. autoclass:: nr.pvrq2.Folder
  :members:
  :show-inheritance:

BaseNode Objects
~~~~~~~~~~~~~~~~

.. autoclass:: nr.pvrq2.BaseNode
  :members:


TreeNodeBase Objects
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: nr.pvrq2.node.TreeNodeBase
  :members:
