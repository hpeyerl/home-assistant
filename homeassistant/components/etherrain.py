"""

Support for Quick Smart Etherrain/8.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/etherrain/

"""
import logging

import etherrain
import voluptuous as vol

from homeassistant.const import (
    CONF_HOST, CONF_PASSWORD, CONF_USERNAME)
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['etherrain=0.3']

_LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10
DOMAIN = 'etherrain'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string
    })
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    """Set up the Etherrain component."""

    conf = config[DOMAIN]

    hostname = conf[CONF_HOST]
    username = conf.get(CONF_USERNAME, None)
    password = conf.get(CONF_PASSWORD, None)

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN]['server_origin'] = server_origin
    hass.data[DOMAIN]['username'] = username
    hass.data[DOMAIN]['password'] = password
    hass.data[DOMAIN][er] = etherrain.EtherRain(hostname, username, password, timeout=DEFAULT_TIMEOUT)

    return hass.data[DOMAIN][er].login()

# retrieve current status
# http://<er_addr>/result.cgi?xs
#
# <body>
#       EtherRain Device Status <br>
#       un:EtherRain 8
#       ma: 01.00.44.03.0A.01  <br>
#       ac: <br>
#       os: RD <br>
#       cs: OK <br>
#       rz: UK <br>
#       ri: 0 <br>
#       rn: 0 <br>
# </body>
def get_state(valve):
    """Get the current state of a valve."""
    hass.data[DOMAIN][er].update_status()
    status = hass.data[DOMAIN][er].get_state()

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

def water_off():
        """Turn off all valves."""
        hass.data[DOMAIN][er].stop()

def water_on(valve, duration):
        """Turn on a specific valve for some number of minutes."""
        hass.data[DOMAIN][er].irrigate(valve, duration)
