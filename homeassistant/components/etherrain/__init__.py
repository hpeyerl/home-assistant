"""

Support for Quick Smart Etherrain/8.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/etherrain/

"""
import logging

import voluptuous as vol

from homeassistant.const import (
    CONF_HOST, CONF_PASSWORD, CONF_USERNAME)
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['etherrain==0.6']

_LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10
DOMAIN = 'etherrain'

LOGIN=False
ER=None

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string
    })
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    """Set up the Etherrain component."""
    import etherrain

    conf = config[DOMAIN]

    global LOGIN
    global ER

    hostname = conf[CONF_HOST]
    username = conf.get(CONF_USERNAME, None)
    password = conf.get(CONF_PASSWORD, None)

    hass.data[DOMAIN] = {}
    ER = EtherRainAPI(hostname, username, password, timeout=DEFAULT_TIMEOUT)

    LOGIN=ER.logged_in

    return LOGIN

class EtherRainAPI(object):

    def __init__(self, hostname, username, password, timeout):
        import etherrain
        self.er = etherrain.EtherRain(hostname, username, password, timeout=DEFAULT_TIMEOUT)
        self.logged_in = self.er.login()
        self.update()

    def update(self):
        self.er.update_status()

    def get_state(self, valve):
        """Get the current state of a valve."""
        self.update()
        status = self.er.get_status()

        if 'os' in status and status['os'] == 'WT':
            # _LOGGER.info("valve={0} and waiting".format(valve, status['ri']))
            return 1
        if 'ri' in status and int(status['ri']) == valve-1:
            if 'os' in status and status['os'] == 'RD':
                # _LOGGER.info("valve={0} and ready".format(valve, status['ri']))
                return 0
            if 'os' in status and status['os'] == 'BZ':
                # _LOGGER.info("valve={0} and busy".format(valve, status['ri']))
                return 1
        else:
            return 0


    # pylint: disable=no-member

    def water_off(self):
        """Turn off all valves."""
        self.er.stop()

    def water_on(self, valve, duration):
        """Turn on a specific valve for some number of minutes."""
        self.er.irrigate(valve, duration)
