from zmqruntime.execution.client import ExecutionClient
from zmqruntime.execution.server import ExecutionServer
from zmqruntime.messages import ControlMessageType, ExecuteRequest, ExecutionStatus, MessageFields


class DummyExecutionServer(ExecutionServer):
    def execute_task(self, execution_id: str, request: ExecuteRequest):
        return {"result": 1}


def test_execution_server_handle_execute_and_run():
    server = DummyExecutionServer(port=5555)
    request = ExecuteRequest(
        plate_id="plate-1",
        pipeline_code="print('hi')",
        config_params={"x": 1},
    )
    response = server._handle_execute(request.to_dict())
    assert response[MessageFields.STATUS] == "accepted"
    execution_id = response[MessageFields.EXECUTION_ID]
    record = server.active_executions[execution_id]
    assert record[MessageFields.STATUS] == ExecutionStatus.QUEUED.value

    server._run_execution(execution_id, request, record)
    assert record[MessageFields.STATUS] == ExecutionStatus.COMPLETE.value


class DummyExecutionClient(ExecutionClient):
    def __init__(self):
        super().__init__(port=5555)
        self._connected = True

    def _spawn_server_process(self):
        return None

    def send_data(self, data):
        return None

    def serialize_task(self, task, config):
        return {"task": task}

    def connect(self, timeout: float = 10.0):
        self._connected = True
        return True

    def _send_control_request(self, request, timeout_ms=5000):
        return request


def test_execution_client_submit_adds_type():
    client = DummyExecutionClient()
    response = client.submit_execution({"hello": "world"})
    assert response[MessageFields.TYPE] == ControlMessageType.EXECUTE.value
