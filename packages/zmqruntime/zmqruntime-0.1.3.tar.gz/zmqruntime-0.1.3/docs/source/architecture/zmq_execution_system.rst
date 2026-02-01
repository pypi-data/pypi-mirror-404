ZMQ Execution System
====================

Overview
--------

zmqruntime provides a dual-channel execution pattern built on
``ExecutionServer`` and ``ExecutionClient``. The control channel handles
commands (execute, status, cancel, ping), while the data channel streams
progress updates to clients.

Dual-Channel Pattern
~~~~~~~~~~~~~~~~~~~~

**Data Port** (e.g., 7777)
  PUB/SUB socket for progress updates from server to client

**Control Port** (data_port + ``control_port_offset``)
  REQ/REP socket for commands and responses

This separation ensures progress updates never block command processing.

Core Components
~~~~~~~~~~~~~~~

- **ZMQServer** (``zmqruntime/server.py``)
  Base server that owns data/control sockets and ping/pong handshake.

- **ZMQClient** (``zmqruntime/client.py``)
  Base client with auto-spawn and connection management.

- **ExecutionServer** (``zmqruntime/execution/server.py``)
  Queue-based sequential executor with progress streaming.

- **ExecutionClient** (``zmqruntime/execution/client.py``)
  Submit/poll/wait flow with optional progress callback.

Execution Flow
~~~~~~~~~~~~~~

.. code-block:: text

   Client                          Server
     |                               |
     |-- PING (control) ------------>|
     |<-- PONG (control) ------------|
     |                               |
     |-- EXECUTE (control) --------->|
     |                               |
     |<-- PROGRESS (data) -----------|
     |<-- PROGRESS (data) -----------|
     |                               |
     |<-- RESULTS (control) ---------|

Task Serialization
~~~~~~~~~~~~~~~~~~

Applications define serialization and execution logic:

- ``ExecutionClient.serialize_task`` returns a JSON-friendly dict that
  matches ``ExecuteRequest``.
- ``ExecutionServer.execute_task`` performs the work and returns results.

Server Lifecycle
~~~~~~~~~~~~~~~~

Clients can connect to existing servers or spawn new ones. Subclasses
control the spawn behavior (for example, detached/persistent vs
non-persistent child processes).
