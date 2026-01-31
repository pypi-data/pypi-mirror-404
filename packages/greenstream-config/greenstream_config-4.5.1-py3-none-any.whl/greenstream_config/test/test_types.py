import pytest
from greenstream_config.types import Camera, CameraSensor, CameraSensorType
from pydantic import ValidationError


class TestCameraSensorValidation:
    """Test ROS-friendly name validation for CameraSensor."""

    def test_valid_lowercase_name(self):
        """Valid: lowercase name."""
        sensor = CameraSensor(name="bow_color", type=CameraSensorType.COLOR)
        assert sensor.name == "bow_color"

    def test_valid_name_with_underscores(self):
        """Valid: lowercase with underscores."""
        sensor = CameraSensor(name="stern_ir_sensor", type=CameraSensorType.IR)
        assert sensor.name == "stern_ir_sensor"

    def test_valid_name_with_numbers(self):
        """Valid: lowercase with numbers (not at start)."""
        sensor = CameraSensor(name="camera_1_color", type=CameraSensorType.COLOR)
        assert sensor.name == "camera_1_color"

    def test_valid_name_starting_with_underscore(self):
        """Valid: name starting with underscore."""
        sensor = CameraSensor(name="_private_sensor", type=CameraSensorType.COLOR)
        assert sensor.name == "_private_sensor"

    def test_invalid_uppercase_name(self):
        """Invalid: uppercase letters."""
        with pytest.raises(ValidationError, match="not ROS-friendly"):
            CameraSensor(name="BowColor", type=CameraSensorType.COLOR)

    def test_invalid_camel_case_name(self):
        """Invalid: camelCase name."""
        with pytest.raises(ValidationError, match="not ROS-friendly"):
            CameraSensor(name="bowColor", type=CameraSensorType.COLOR)

    def test_invalid_name_with_hyphen(self):
        """Invalid: name with hyphens."""
        with pytest.raises(ValidationError, match="not ROS-friendly"):
            CameraSensor(name="bow-color", type=CameraSensorType.COLOR)

    def test_invalid_name_with_space(self):
        """Invalid: name with spaces."""
        with pytest.raises(ValidationError, match="not ROS-friendly"):
            CameraSensor(name="bow color", type=CameraSensorType.COLOR)

    def test_invalid_name_starting_with_number(self):
        """Invalid: name starting with number."""
        with pytest.raises(ValidationError, match="not ROS-friendly"):
            CameraSensor(name="1_bow_color", type=CameraSensorType.COLOR)

    def test_invalid_name_with_special_chars(self):
        """Invalid: name with special characters."""
        with pytest.raises(ValidationError, match="not ROS-friendly"):
            CameraSensor(name="bow@color", type=CameraSensorType.COLOR)


class TestCameraValidation:
    """Test ROS-friendly name validation for Camera."""

    def test_valid_lowercase_name(self):
        """Valid: lowercase name."""
        camera = Camera(
            name="bow",
            with_ptz=False,
            sensors=[CameraSensor(name="bow_color", type=CameraSensorType.COLOR)],
        )
        assert camera.name == "bow"

    def test_valid_name_with_underscores(self):
        """Valid: lowercase with underscores."""
        camera = Camera(
            name="port_camera",
            with_ptz=False,
            sensors=[CameraSensor(name="port_camera_color", type=CameraSensorType.COLOR)],
        )
        assert camera.name == "port_camera"

    def test_valid_name_with_numbers(self):
        """Valid: lowercase with numbers (not at start)."""
        camera = Camera(
            name="camera_1",
            with_ptz=False,
            sensors=[CameraSensor(name="camera_1_color", type=CameraSensorType.COLOR)],
        )
        assert camera.name == "camera_1"

    def test_valid_name_starting_with_underscore(self):
        """Valid: name starting with underscore."""
        camera = Camera(
            name="_test_camera",
            with_ptz=False,
            sensors=[CameraSensor(name="_test_camera_color", type=CameraSensorType.COLOR)],
        )
        assert camera.name == "_test_camera"

    def test_invalid_uppercase_name(self):
        """Invalid: uppercase letters."""
        with pytest.raises(ValidationError, match="not ROS-friendly"):
            Camera(
                name="BowCamera",
                with_ptz=False,
                sensors=[CameraSensor(name="bow_color", type=CameraSensorType.COLOR)],
            )

    def test_invalid_camel_case_name(self):
        """Invalid: camelCase name."""
        with pytest.raises(ValidationError, match="not ROS-friendly"):
            Camera(
                name="bowCamera",
                with_ptz=False,
                sensors=[CameraSensor(name="bow_color", type=CameraSensorType.COLOR)],
            )

    def test_invalid_name_with_hyphen(self):
        """Invalid: name with hyphens."""
        with pytest.raises(ValidationError, match="not ROS-friendly"):
            Camera(
                name="bow-camera",
                with_ptz=False,
                sensors=[CameraSensor(name="bow_color", type=CameraSensorType.COLOR)],
            )

    def test_invalid_name_with_space(self):
        """Invalid: name with spaces."""
        with pytest.raises(ValidationError, match="not ROS-friendly"):
            Camera(
                name="bow camera",
                with_ptz=False,
                sensors=[CameraSensor(name="bow_color", type=CameraSensorType.COLOR)],
            )

    def test_invalid_name_starting_with_number(self):
        """Invalid: name starting with number."""
        with pytest.raises(ValidationError, match="not ROS-friendly"):
            Camera(
                name="1_bow",
                with_ptz=False,
                sensors=[CameraSensor(name="bow_color", type=CameraSensorType.COLOR)],
            )

    def test_invalid_name_with_special_chars(self):
        """Invalid: name with special characters."""
        with pytest.raises(ValidationError, match="not ROS-friendly"):
            Camera(
                name="bow@camera",
                with_ptz=False,
                sensors=[CameraSensor(name="bow_color", type=CameraSensorType.COLOR)],
            )

    def test_default_sensor_creation(self):
        """Test that a camera without sensors gets a default sensor named {camera_name}_color."""
        camera = Camera(name="bow", with_ptz=False)
        assert len(camera.sensors) == 1
        assert camera.sensors[0].name == "bow_color"
        assert camera.sensors[0].type == CameraSensorType.COLOR

    def test_default_sensor_with_ptz(self):
        """Test that a PTZ camera without sensors gets a default sensor named {camera_name}_color."""
        camera = Camera(name="stern", with_ptz=True)
        assert len(camera.sensors) == 1
        assert camera.sensors[0].name == "stern_color"
        assert camera.sensors[0].type == CameraSensorType.COLOR

    def test_explicit_sensors_preserved(self):
        """Test that explicitly provided sensors are preserved and default is not created."""
        camera = Camera(
            name="bow",
            with_ptz=False,
            sensors=[
                CameraSensor(name="bow_color", type=CameraSensorType.COLOR),
                CameraSensor(name="bow_ir", type=CameraSensorType.IR),
            ],
        )
        assert len(camera.sensors) == 2
        assert camera.sensors[0].name == "bow_color"
        assert camera.sensors[1].name == "bow_ir"
