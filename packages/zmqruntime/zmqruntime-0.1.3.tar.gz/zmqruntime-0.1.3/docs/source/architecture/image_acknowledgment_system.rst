Image Acknowledgment System
===========================

Overview
--------

The acknowledgment system tracks viewer-side processing of streamed images.
Viewers send an ``ImageAck`` message after processing each image, and a global
listener updates per-viewer queue trackers so clients can monitor progress.

Message Flow
~~~~~~~~~~~~

.. code-block:: text

   Producer                    Viewer
     |                           |
     |-- image batch ----------->|
     |                           |  (display / copy)
     |                           |-- ImageAck ------>
     |                           |
     v                           v
   GlobalAckListener  --->  QueueTracker

Core Components
~~~~~~~~~~~~~~~

**ImageAck** (``zmqruntime/messages.py``)
  Acknowledgment payload containing ``image_id``, ``viewer_port``, ``viewer_type``,
  ``status``, and timestamp metadata.

**QueueTracker** (``zmqruntime/queue_tracker.py``)
  Tracks pending and processed image IDs for a single viewer.

**GlobalQueueTrackerRegistry** (``zmqruntime/queue_tracker.py``)
  Singleton registry that stores ``QueueTracker`` instances by viewer port.

**GlobalAckListener** (``zmqruntime/ack_listener.py``)
  Singleton PULL socket listener that routes ``ImageAck`` messages to the
  correct queue tracker.

Integration Notes
~~~~~~~~~~~~~~~~~

- Producers register sent image IDs with the appropriate ``QueueTracker``.
- Viewers send ``ImageAck`` messages after processing each image.
- ``GlobalAckListener`` updates queue trackers on receipt of acknowledgments.
