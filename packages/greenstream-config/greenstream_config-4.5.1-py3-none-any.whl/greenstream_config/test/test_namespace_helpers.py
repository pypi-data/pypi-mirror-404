from greenstream_config.namespace_helpers import (
    get_camera_namespace,
    get_camera_topic_base,
    get_sensor_frame_compressed_topic,
    get_sensor_frame_id,
    get_sensor_frame_topic,
    get_sensor_node_name,
    get_sensor_topic,
)


def test_get_sensor_topic():
    assert get_sensor_topic("vessel_1", "bow_color") == "/vessel_1/sensors/cameras/bow_color"


def test_get_sensor_frame_id():
    assert get_sensor_frame_id("vessel_1", "bow_color") == "vessel_1_bow_color_optical_frame"


def test_get_sensor_node_name():
    assert get_sensor_node_name("node", "bow_color") == "node_bow_color"


def test_get_sensor_frame_topic():
    assert (
        get_sensor_frame_topic("vessel_1", "bow_color") == "/vessel_1/perception/frames/bow_color"
    )


def test_get_sensor_frame_topic_empty_namespace():
    assert get_sensor_frame_topic("", "bow_color") == "perception/frames/bow_color"


def test_get_sensor_frame_compressed_topic():
    assert (
        get_sensor_frame_compressed_topic("vessel_1", "bow_color")
        == "/vessel_1/perception/frames/bow_color/compressed"
    )


def test_get_camera_namespace():
    assert get_camera_namespace("namespace", "bow") == "namespace/cameras/bow"


def test_get_camera_topic_base():
    assert get_camera_topic_base("vessel_1", "bow") == "/vessel_1/sensors/cameras/bow"
