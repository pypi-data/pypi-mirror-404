import pytest

from shine2mqtt.growatt.protocol.config import ConfigRegistry, RegisterInfo


@pytest.fixture
def test_registers():
    return {
        4: {
            "name": "update_interval",
            "description": "Update Interval min",
            "fmt": "s",
        },
        21: {
            "name": "datalogger_sw_version",
            "description": "Datalogger software Version",
            "fmt": "s",
        },
    }


@pytest.fixture
def registry(test_registers):
    return ConfigRegistry(test_registers)


def test_get_register_by_name(registry):
    assert registry.get_register_by_name("update_interval") == 4
    assert registry.get_register_by_name("datalogger_sw_version") == 21
    assert registry.get_register_by_name("unknown") is None


def test_get_register_info(registry):
    info = registry.get_register_info(4)
    assert info is not None
    assert isinstance(info, RegisterInfo)
    assert info.name == "update_interval"
    assert info.description == "Update Interval min"
    assert info.fmt == "s"

    assert registry.get_register_info(999) is None


def test_has_register(registry):
    assert registry.has_register(4) is True
    assert registry.has_register(21) is True
    assert registry.has_register(999) is False


def test_default_uses_config_registers():
    registry = ConfigRegistry()
    assert registry.has_register(4) is True
    info = registry.get_register_info(4)
    assert info is not None
    assert info.name == "update_interval"


def test_register_info_immutable():
    info = RegisterInfo(name="test", description="Test", fmt="s")
    with pytest.raises(AttributeError):
        info.name = "changed"  # ty:ignore[invalid-assignment]
