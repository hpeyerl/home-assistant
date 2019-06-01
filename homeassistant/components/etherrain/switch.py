import logging

import voluptuous as vol

from homeassistant.components import etherrain
from homeassistant.components.switch import (SwitchDevice, PLATFORM_SCHEMA)
from homeassistant.const import CONF_NAME
import homeassistant.helpers.config_validation as cv

CONF_VALVES = 'valves'
CONF_DURATION = 'duration'

VALVE_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_DURATION):cv.positive_int,
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_VALVES, default={}):
        vol.Schema({cv.positive_int: VALVE_SCHEMA}),
})

DEPENDENCIES = ['etherrain']

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """ Setup the Etherrain platform."""
    # Verify that we're logged into an Etherrain device

    if etherrain.LOGIN is False:
        _LOGGER.error("No active connection to an Etherrain device")
        return False

    valves = config.get(CONF_VALVES)

    switches = []
    for valvenum,duration in valves.items():
        switches.append(EtherRainSwitch(valvenum,duration))

    add_entities(switches)

class EtherRainSwitch(SwitchDevice):

    def __init__(self, valve, options):
        self._valve = valve
        self._duration = options.get(CONF_DURATION)
        self._name = options.get(CONF_NAME)

        self.on_handler = etherrain.ER.water_on
        self.off_handler = etherrain.ER.water_off

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return etherrain.ER.get_state(self._valve)

    def turn_on(self, **kwargs):
        self.on_handler(self._valve, self._duration)

    def turn_off(self, **kwargs):
        self.off_handler()
