try:
    from pygrabber.dshow_graph import FilterGraph
except ImportError:
    FilterGraph = None
    def get_available_cameras() -> dict[int, str]:
        return {}
else:
    # !: This whole thing is full of type errors, but do you care?
    def get_available_cameras() -> dict[int, str]:
        """https://stackoverflow.com/questions/70886225/get-camera-device-name-and-port-for-opencv-videostream-python"""
        devices = FilterGraph().get_input_devices() # type: ignore -- typing for this sucks
        available_cameras: dict[int, str] = {}
        for device_index, device_name in enumerate(devices):
            available_cameras[device_index] = device_name
        return available_cameras

__all__ = (
    "get_available_cameras",
)
