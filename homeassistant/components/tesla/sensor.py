"""Support for the Tesla sensors."""
import logging

from homeassistant.const import (
    LENGTH_KILOMETERS,
    LENGTH_MILES,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)
from homeassistant.helpers.entity import Entity

from . import DOMAIN as TESLA_DOMAIN, TeslaDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Tesla sensor platform."""
    pass


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Tesla binary_sensors by config_entry."""
    controller = hass.data[TESLA_DOMAIN][config_entry.entry_id]["controller"]
    entities = []
    for device in hass.data[TESLA_DOMAIN][config_entry.entry_id]["devices"]["sensor"]:
        if device.bin_type == 0x4:
            entities.append(TeslaSensor(device, controller, config_entry, "inside"))
            entities.append(TeslaSensor(device, controller, config_entry, "outside"))
        elif device.bin_type in [0xA, 0xB, 0x5]:
            entities.append(TeslaSensor(device, controller, config_entry))
    async_add_entities(entities, True)


class TeslaSensor(TeslaDevice, Entity):
    """Representation of Tesla sensors."""

    def __init__(self, tesla_device, controller, config_entry, sensor_type=None):
        """Initialize of the sensor."""
        self.current_value = None
        self._unit = None
        self.last_changed_time = None
        self.type = sensor_type
        super().__init__(tesla_device, controller, config_entry)

        if self.type:
            self._name = f"{self.tesla_device.name} ({self.type})"

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        if self.type:
            return f"{self.tesla_id}_{self.type}"
        return self.tesla_id

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.current_value

    @property
    def unit_of_measurement(self):
        """Return the unit_of_measurement of the device."""
        return self._unit

    async def async_update(self):
        """Update the state from the sensor."""
        _LOGGER.debug("Updating sensor: %s", self._name)
        await super().async_update()
        units = self.tesla_device.measurement

        if self.tesla_device.bin_type == 0x4:
            if self.type == "outside":
                self.current_value = self.tesla_device.get_outside_temp()
            else:
                self.current_value = self.tesla_device.get_inside_temp()
            if units == "F":
                self._unit = TEMP_FAHRENHEIT
            else:
                self._unit = TEMP_CELSIUS
        elif self.tesla_device.bin_type == 0xA or self.tesla_device.bin_type == 0xB:
            self.current_value = self.tesla_device.get_value()
            tesla_dist_unit = self.tesla_device.measurement
            if tesla_dist_unit == "LENGTH_MILES":
                self._unit = LENGTH_MILES
            else:
                self._unit = LENGTH_KILOMETERS
                self.current_value /= 0.621371
                self.current_value = round(self.current_value, 2)
        else:
            self.current_value = self.tesla_device.get_value()
            if self.tesla_device.bin_type == 0x5:
                self._unit = units
            elif self.tesla_device.bin_type in (0xA, 0xB):
                if units == "LENGTH_MILES":
                    self._unit = LENGTH_MILES
                else:
                    self._unit = LENGTH_KILOMETERS
                    self.current_value /= 0.621371
                    self.current_value = round(self.current_value, 2)
