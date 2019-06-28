import json

from .errors import MonitorError


class Monitor(object):
    """A monitoring task for a device.

    This task is robust to some API-level failures. If the monitoring
    task expires, it attempts to start a new one automatically. This
    makes one `Monitor` object suitable for long-term monitoring.
    """

    def __init__(self, session, device_id):
        self.session = session
        self.device_id = device_id

    def start(self):
        self.work_id = self.session.monitor_start(self.device_id)

    def stop(self):
        self.session.monitor_stop(self.device_id, self.work_id)

    def poll(self):
        """Get the current status data (a bytestring) or None if the
        device is not yet ready.
        """

        try:
            return self.session.monitor_poll(self.device_id, self.work_id)
        except MonitorError:
            # Try to restart the task.
            self.stop()
            self.start()
            return None

    @staticmethod
    def decode_json(data):
        """Decode a bytestring that encodes JSON status data."""

        return json.loads(data.decode('utf8'))

    def poll_json(self):
        """For devices where status is reported via JSON data, get the
        decoded status result (or None if status is not available).
        """

        data = self.poll()
        return self.decode_json(data) if data else None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, type, value, tb):
        self.stop()
