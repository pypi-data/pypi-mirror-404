import os
import platform
from pathlib import Path

import pytest

from zmqruntime.config import TransportMode, ZMQConfig
from zmqruntime.transport import (
    get_default_transport_mode,
    get_ipc_socket_path,
    get_zmq_transport_url,
    remove_ipc_socket,
)


def test_get_default_transport_mode():
    mode = get_default_transport_mode()
    assert mode in (TransportMode.TCP, TransportMode.IPC)


def test_get_zmq_transport_url_tcp():
    url = get_zmq_transport_url(5555, host="localhost", mode=TransportMode.TCP)
    assert url == "tcp://localhost:5555"


def test_ipc_socket_path_and_url():
    config = ZMQConfig(app_name="zmqruntime-test", ipc_socket_prefix="test")
    if platform.system() == "Windows":
        assert get_ipc_socket_path(5555, config) is None
        with pytest.raises(ValueError):
            get_zmq_transport_url(5555, mode=TransportMode.IPC, config=config)
        return

    path = get_ipc_socket_path(5555, config)
    assert path is not None
    assert str(path).endswith(".sock")
    url = get_zmq_transport_url(5555, mode=TransportMode.IPC, config=config)
    assert url.startswith("ipc://")


def test_remove_ipc_socket(tmp_path):
    config = ZMQConfig(app_name="zmqruntime-test", ipc_socket_prefix="test")
    if platform.system() == "Windows":
        assert remove_ipc_socket(5555, config) is False
        return

    socket_path = get_ipc_socket_path(5555, config)
    assert socket_path is not None
    socket_path.parent.mkdir(parents=True, exist_ok=True)
    socket_path.write_text("test")
    assert socket_path.exists()
    assert remove_ipc_socket(5555, config) is True
    assert not socket_path.exists()
