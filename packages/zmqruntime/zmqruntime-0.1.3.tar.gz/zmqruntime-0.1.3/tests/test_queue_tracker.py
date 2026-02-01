import time

from zmqruntime.queue_tracker import QueueTracker, GlobalQueueTrackerRegistry


def test_queue_tracker_progress():
    tracker = QueueTracker(viewer_port=5555, viewer_type="test", timeout_seconds=0.01)
    tracker.register_sent("img-1")
    tracker.register_sent("img-2")
    assert tracker.get_progress() == (0, 2)
    tracker.mark_processed("img-1")
    assert tracker.get_progress() == (1, 2)
    assert tracker.get_pending_count() == 1
    time.sleep(0.02)
    assert tracker.has_stuck_images() is True


def test_global_registry():
    registry = GlobalQueueTrackerRegistry()
    tracker = registry.get_or_create_tracker(1234, "test")
    assert registry.get_tracker(1234) is tracker
    registry.remove_tracker(1234)
    assert registry.get_tracker(1234) is None
