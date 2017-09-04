"""

Support for Etherrain valves.

"""
import logging

import voluptuous as vol

from homeassistant.components.switch import (SwitchDevice, PLATFORM_SCHEMA)
import homeassistant.components.etherrain as er
import homeassistant.helpers.config_validation as cv


_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['etherrain']
DOMAIN = 'etherrain'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required("valve_id"): cv.positive_int,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Etherrain irrigation platform."""
    valve_id = config.get("valve_id")
    valve_name = config.get("name")
    duration = config.get("duration")

    api = hass.data[DOMAIN]['er']

    add_devices([ERValveSwitches(api, valve_id, valve_name, duration)])


class ERValveSwitches(SwitchDevice):
    """Representation of an Etherrain valve."""

    def __init__(self, api, valve_id, valve_name, duration):
        """Initialize ERValveSwitches."""
        self.api = api
        self._valve_id = valve_id
        self._valve_name = valve_name
        if duration is not None:
            self._duration = duration
        else:
            self._duration = 60
        self._on_state = 1
        self._off_state = 0
        self._state = None

    @property
    def name(self):
        """Get valve name."""
        return self._valve_name

    def update(self):
        """Update valve state."""
        self.api.update()
        state = self.api.get_state(self._valve_id)

        self._state = state
        # _LOGGER.info("update etherrain switch {0} - {1}".format(
        # self._valve_id, self._state))

    @property
    def is_on(self):
        """Return valve state."""
        # _LOGGER.info("is_on: etherrain switch {0} - {1}".format(
        # self._valve_id, self._state))
        return self._state

    def turn_on(self):
        # _LOGGER.info("turn on etherrain switch {0}".format(self._valve_id))
        self._state = True
        self.api.water_on(self._valve_id, self._duration)

    def turn_off(self):
        """Turn a valve off."""
        # We should first check the state and if it's "BZ" and the valve_id
        # matches, then turn it off.  For now, just turn it off regardless.
        self._state = False
        self.api.water_off()
        # _LOGGER.info("turn off etherrain switch {0}".format(self._valve_id))
