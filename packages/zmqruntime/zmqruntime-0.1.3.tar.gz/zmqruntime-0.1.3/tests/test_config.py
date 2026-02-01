from zmqruntime.config import TransportMode, ZMQConfig


def test_transport_mode_values():
    assert TransportMode.TCP.value == "tcp"
    assert TransportMode.IPC.value == "ipc"


def test_zmq_config_defaults():
    config = ZMQConfig()
    assert config.control_port_offset == 1000
    assert config.default_port == 7777
    assert config.ipc_socket_dir == "ipc"
    assert config.ipc_socket_prefix == "zmq"
    assert config.ipc_socket_extension == ".sock"
    assert config.shared_ack_port == 7555
    assert config.app_name == "zmqruntime"
