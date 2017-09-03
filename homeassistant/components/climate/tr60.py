"""
RCS TR60 programmable thermostat

Example configuration:

climate:
  - platform: tr60
    name: tr60
    port: /dev/ttyUSB0
    speed: 9600
    bits: 8
    stop: 1
    parity: none

For more details about this platform, please refer to the documentation
https://home-assistant.io/components/climate.flexit/
"""
import logging
import voluptuous as vol

from homeassistant.const import (
    CONF_NAME, CONF_SLAVE, TEMP_CELSIUS,
    ATTR_TEMPERATURE, DEVICE_DEFAULT_NAME)
from homeassistant.components.climate import (ClimateDevice, PLATFORM_SCHEMA)
import homeassistant.components.modbus as modbus
import homeassistant.helpers.config_validation as cv

DEPENDENCIES = ['serial']

CONF_BAUD = 'baud'
DEFAULT_BAUD = 9600
DEFAULT_PORT = "/dev/ttyS0"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEVICE_DEFAULT_NAME): cv.string
    vol.Optional(CONF_BAUD, default=DEFAULT_BAUD): cv.string,
    vol.Required(CONF_DEVICE, default=DEFAULT_DEVICE): cv.string,
})

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the TR60 Platform."""
    baudrate = config.get(CONF_BAUD, None)
    name = config.get(CONF_NAME, None)
    port = config.get(CONF_DEVICE, DEFAULT_PORT)
    add_devices([TR60(port, baudrate, name)], True)

class TR60_serial():
    """Serial interface to RCS TR60."""
    def __init__(self, port, baudrate):
        self.ser = None
        self.status = {}
        self.status["M"]=""
        self.status["OA"]=""
        self.status["T"]=""
        self.status["FM"]=""
        self.status["SP"]=""
        self.status["SPH"]=""
        self.status["SPC"]=""
        self.status["H1A"]=""
        self.status["C1A"]=""
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS)
        except (IOError, OSError):
            _LOGGER.error("tr60: Error opening serial port %s",port)
            return

    def getserial(self):
        serin=""
        timeout=0
        while self.ser.inWaiting() == 0:
            timeout+=1
            if timeout > 10000:
                return serin
        while self.ser.inWaiting() > 0:
            serin += self.ser.read(self.ser.inWaiting())
        return serin

    def send_thermostat(self, string):
        discard=self.getserial() # flush garbage.
        self.ser.write(string)
        time.sleep(1)
        serin=self.getserial()
        serin=serin[1:-1]
        serin=serin.strip()
        return serin

    def update_status(self):
        parts = []
        serin=self.send_thermostat("A=%d R=1\r"%self.addr)
        if len(serin) != 0:  # Nothing from thermostat.
            parts=serin.split(" ")
        print "from R=1: {0}".format(serin)
        serin=self.send_thermostat("A=%d R=2\r"%self.addr)
        print "from R=2: {0}".format(serin)
        if (serin) != 0:  # Nothing from thermostat.
            parts+=serin.split(" ")
        kv={}
        for part in parts:
            try:
                attr,value=part.split("=")
            except ValueError:
                print "Parse Error: {0}".format(parts)
                pass
            if attr in ['T', 'SP', 'SPC', 'SPH', 'M', 'FM', 'OA', 'H1A', 'C1A' ] :
                self.status[attr]=value

    def set_setback(self, mode):
        if 'home' in mode:
            x=self.send_thermostat("A=%d SB=1\r"%self.addr)
        if 'away' in mode:
            x=self.send_thermostat("A=%d SB=2\r"%self.addr)
        if 'vacation' in mode:
            x=self.send_thermostat("A=%d SB=3\r"%self.addr)

    def set_fan_mode(self, mode):
        if 'on' in mode:
            x=self.send_thermostat("A=%d SF=1\r"%self.addr)
        if 'off' in mode:
            x=self.send_thermostat("A=%d SF=0\r"%self.addr)

    def set_heat_mode(self, mode):
        if 'off' in mode:
            x=self.send_thermostat("A=%d M=0\r"%self.addr)
        if 'heat' in mode:
            x=self.send_thermostat("A=%d M=1\r"%self.addr)
        if 'cool' in mode:
            x=self.send_thermostat("A=%d M=2\r"%self.addr)
        if 'auto' in mode:
            x=self.send_thermostat("A=%d M=3\r"%self.addr)

    def get_heat_mode(self, arg):
        return self.status["M"]

    def get_outside_air_temp(self, arg):
        return self.status["OA"]

    def get_inside_air_temp(self, arg):
        return self.status["T"]

    def get_fan_mode(self, arg):
        return self.status["FM"]

    def get_setpoint(self, arg):
        return self.status["SP"]

    def get_setpoint_heat(self, arg):
        return self.status["SPH"]

    def get_setpoint_cool(self, arg):
        return self.status["SPC"]

    def get_heat_runtime(self, arg):
        return self.status["H1A"]

    def get_cool_runtime(self, arg):
        return self.status["C1A"]


class TR60(ClimateDevice):
    """Representation of a Flexit AC unit."""

    def __init__(self, port, baudrate, name):
        """Initialize the unit."""
        from pyflexit import pyflexit
        self._name = name
        self._port = port
        self._baudrate = baudrate
        self._sph = None
        self._spc = None
        self._current_temperature = None
        self._outdoor_temperature = None
        self._current_fan_mode = None
        self._current_operation = None
        self._fan_list = ['Off', 'On']
        self._current_operation = None
        self._filter_hours = None
        self._filter_alarm = None
        self._heat_recovery = None
        self._heating = None
        self._cooling = None
        self._alarm = False
        self.unit = TR60_serial(self._port, self._baudrate)

    def update(self):
        """Update unit attributes."""
        if not self.unit.update():
            _LOGGER.warning("Modbus read failed")

        self._target_temperature = self.unit.get_target_temp
        self._current_temperature = self.unit.get_temp
        self._outdoor_temperature = self.unit.get_oa_temp
        self._current_fan_mode =\
            self._fan_list[self.unit.get_fan_speed]
        self._filter_hours = self.unit.get_filter_hours
        # Mechanical heat recovery, 0-100%
        self._heat_recovery = self.unit.get_heat_recovery
        # Heater active 0-100%
        self._heating = self.unit.get_heating
        # Cooling active 0-100%
        self._cooling = self.unit.get_cooling
        # Filter alarm 0/1
        self._filter_alarm = self.unit.get_filter_alarm
        # Current operation mode
        self._current_operation = self.unit.get_operation

    @property
    def device_state_attributes(self):
        """Return device specific state attributes."""
        return {
            'filter_hours':     self._filter_hours,
            'filter_alarm':     self._filter_alarm,
            'heat_recovery':    self._heat_recovery,
            'heating':          self._heating,
            'cooling':          self._cooling
        }

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def name(self):
        """Return the name of the climate device."""
        return self._name

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temperature

    @property
    def outdoor_temperature(self):
        """Return the outdoor air temperature."""
        return self._outdoor_temcurrentperature

    @property
    def setpoint_heat(self):
        """Return the Heating setpoint"""
        return self._sph

    @property
    def setpoint_cool(self):
        """Return the Cooling setpoint"""
        return self._sph

    @property
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        return self._current_operation

    @property
    def current_fan_mode(self):
        """Return the fan setting."""
        return self._current_fan_mode

    @property
    def fan_list(self):
        """Return the list of available fan modes."""
        return self._fan_list

    def set_sph(self, sph):
        """Set new Heat setpoint."""
    self._sph = sph
        self.unit.sph(self._sph)

    def set_spc(self, spc):
        """Set new Cool setpoint."""
    self._spc = spc
        self.unit.spc(self._spc)

    def set_fan_mode(self, fan):
        """Set new fan mode."""
        self.unit.set_fan_speed(self._fan_list.index(fan))
