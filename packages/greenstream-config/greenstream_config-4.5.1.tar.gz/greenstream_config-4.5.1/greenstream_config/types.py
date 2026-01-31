import re
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, RootModel, field_validator, model_validator


class CameraSensorType(str, Enum):
    """Supported camera sensor types for different sensor modalities."""

    COLOR = "color"
    IR = "ir"


class CameraSensor(BaseModel):
    """Individual camera sensor within a physical camera housing.

    Represents a logical camera stream (e.g., color, thermal) that shares
    the same physical mounting point and PTZ control with other sensors.
    """

    name: str = Field(
        description="Sensor identifier used in ROS topics and frame IDs. This should be prefixed with the camera housing name"
    )
    type: CameraSensorType = Field(
        default=CameraSensorType.COLOR, description="Type of camera sensor/modality"
    )
    with_camera_info: bool = Field(
        default=True, description="Whether to launch camera_info publisher for this sensor"
    )
    with_pipeline: bool = Field(default=True, description="Whether to launch the pipeline")
    with_image_compressor: bool = Field(
        default=True, description="Whether to launch the image compressor"
    )

    @field_validator("name")
    @classmethod
    def validate_ros_friendly_name(cls, v: str) -> str:
        """Ensure name follows ROS naming convention: lowercase with underscores, not starting with numbers."""
        if not re.match(r"^[a-z_][a-z0-9_]*$", v):
            raise ValueError(
                f"Name '{v}' is not ROS-friendly. Names must be lowercase with underscores, "
                "not starting with numbers (e.g., 'bow_color', 'stern_ir')"
            )
        return v


class Camera(BaseModel):
    """Physical camera housing/mount that can host multiple camera sensors.

    Represents the physical hardware unit including PTZ mechanisms.
    Multiple sensors (color, thermal, etc.) can share the same PTZ control.
    """

    name: str = Field(
        description="Physical camera housing identifier (e.g., 'bow', 'stern', 'port')"
    )
    with_ptz: bool = Field(
        default=False,
        description="Whether we should launch a PTZ driver",
    )
    sensors: List[CameraSensor] = Field(
        default_factory=list, description="List of camera sensors mounted in this housing"
    )

    @field_validator("name")
    @classmethod
    def validate_ros_friendly_name(cls, v: str) -> str:
        """Ensure name follows ROS naming convention: lowercase with underscores, not starting with numbers."""
        if not re.match(r"^[a-z_][a-z0-9_]*$", v):
            raise ValueError(
                f"Name '{v}' is not ROS-friendly. Names must be lowercase with underscores, "
                "not starting with numbers (e.g., 'bow', 'stern', 'port_camera')"
            )
        return v

    @model_validator(mode="after")
    def validate_camera_sensors(self):
        """Ensure camera has valid sensor configuration.

        If no sensors are specified, creates a default COLOR sensor named {camera_name}_{type}.
        """
        if not self.sensors:
            # Create default sensor with camera's name and type suffix
            sensor_type = CameraSensorType.COLOR
            self.sensors = [
                CameraSensor(name=f"{self.name}_{sensor_type.value}", type=sensor_type)
            ]

        return self


class Cameras(RootModel):
    root: list[Camera] = Field(default_factory=list)


class GreenstreamConfig(BaseModel):
    """Complete configuration for the Greenstream video streaming system.

    Defines the camera housings and their sensors, along with system-wide
    settings for WebRTC streaming and ROS integration.
    """

    cameras: List[Camera] = Field(
        description="List of physical camera housings and their sensors to deploy"
    )
    signalling_server_port: int = Field(
        default=8443, description="Port for the WebRTC signalling server"
    )
    namespace_vessel: str = Field(
        default="vessel_1", description="Vessel identifier for multi-vessel deployments"
    )
    namespace_application: str = Field(default="greenstream", description="Application namespace")
    ui_port: int = Field(default=8000, description="Port for the web UI server")
    debug: bool = Field(default=False, description="Enable debug logging and tracing")
    diagnostics_topic: str = Field(default="diagnostics", description="ROS diagnostics topic name")
    use_gpu: bool = Field(
        default=False, description="Whether to use the GPU for camera processing or not"
    )
    cert_path: Optional[str] = Field(None, description="SSL certificate path for HTTPS signalling")
    cert_password: Optional[str] = Field(None, description="SSL certificate password")
    is_live: bool = Field(
        default=True,
        description=(
            "Whether greenstream is being launched with live streams, will override camera "
            "sources for playback if False"
        ),
    )

    @model_validator(mode="after")
    def validate_global_configuration(self):
        """Ensure system-wide configuration is valid."""

        # Check for duplicate camera names
        camera_names = [camera.name for camera in self.cameras]
        if len(set(camera_names)) != len(camera_names):
            raise ValueError("Duplicate camera names found")

        # Check for duplicate sensor names across all cameras
        all_sensor_names = []
        for camera in self.cameras:
            for sensor in camera.sensors:
                all_sensor_names.append(sensor.name)
        if len(set(all_sensor_names)) != len(all_sensor_names):
            raise ValueError("Duplicate sensor names found across cameras")

        return self
