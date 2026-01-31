def get_sensor_topic(namespace_vessel: str, sensor_name: str) -> str:
    """Generate sensor camera topic path for a sensor."""
    return f"/{namespace_vessel}/sensors/cameras/{sensor_name}"


def get_sensor_frame_topic(namespace_vessel: str, sensor_name: str) -> str:
    """Generate frame topic path for camera images."""
    if namespace_vessel == "":
        return f"perception/frames/{sensor_name}"
    else:
        return f"/{namespace_vessel}/perception/frames/{sensor_name}"


def get_sensor_frame_compressed_topic(namespace_vessel: str, sensor_name: str) -> str:
    """Generate compressed frame topic path."""
    return f"{get_sensor_frame_topic(namespace_vessel, sensor_name)}/compressed"


def get_sensor_frame_id(namespace_vessel: str, sensor_name: str) -> str:
    """Generate optical frame ID for a camera sensor."""
    return f"{namespace_vessel}_{sensor_name}_optical_frame"


def get_sensor_node_name(node_type: str, sensor_name: str) -> str:
    """Generate ROS node name for a sensor-specific node."""
    return f"{node_type}_{sensor_name}"


def get_namespace_vessel_application(namespace_vessel: str, namespace_application: str) -> str:
    """Generate the namespace of the vessel and application, separated by '/'"""
    return f"{namespace_vessel}/{namespace_application}"


def get_camera_namespace(namespace_full: str, camera_name: str) -> str:
    """Generate ROS namespace for PTZ driver."""
    return f"{namespace_full}/cameras/{camera_name}"


def get_camera_topic_base(namespace_vessel: str, camera_name: str) -> str:
    """Generate base topic path for PTZ control."""
    return f"/{namespace_vessel}/sensors/cameras/{camera_name}"
