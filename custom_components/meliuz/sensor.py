import hashlib
import json
import logging
import string
from collections import defaultdict
from datetime import datetime, timedelta

import homeassistant.helpers.config_validation as cv
import pytz
import requests
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    ATTR_FRIENDLY_NAME,
    ATTR_UNIT_OF_MEASUREMENT,
    CONF_NAME,
    CONF_RESOURCES,
    STATE_UNKNOWN,
)
from homeassistant.helpers.entity import Entity
from homeassistant.util.dt import utc_from_timestamp

_LOGGER = logging.getLogger(__name__)

ICON = "mdi:cash"
SENSOR_NAME = "Meliuz {} {}"
ATTR_LAST_UPDATED = 'last_updated'
BALANCE_CONFIRMED = "balance confirmed"
PENDING_CONFIRMED = "pending confirmed"

SCAN_INTERVAL = timedelta(minutes=60)

ATTRIBUTION = "Data provided by meliuz api"

DOMAIN = "meliuz"

CONF_TOKEN = "token"
CONF_NAME = "name"

BALANCE_URL = "https://customer.meliuz.com.br/v2/me?include=indication_count,has_online_transaction,has_retail_transaction,has_online_transaction_only_purchase"
TRANSACTIONS_URL = "https://customer.meliuz.com.br/me/transactions?page=1&limit=100&kind=&status=&raw_text=&expiring=false"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_TOKEN): cv.string,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup the currency sensor"""
    name = config["name"]
    token = config["token"]

    add_entities(
        [MeliuzConfirmedBalanceSensor(hass, name, token, SCAN_INTERVAL), MeliuzPendingBalanceSensor(hass, name, token, SCAN_INTERVAL)],
        True,
    )


class MeliuzSensor(Entity):
    def __init__(self, hass, name, token, interval):
        """Inizialize sensor"""
        self._name = name
        self._state = STATE_UNKNOWN
        self._last_updated = STATE_UNKNOWN
        self._hass = hass
        self._interval = interval
        self._token = token
        self.balance = {}

    @property
    def name(self):
        """Returns the name of the sensor."""
        return SENSOR_NAME.format(self._name, self._name_suffix)

    @property
    def _name_suffix(self):
        """Returns the name suffix of the sensor."""
        raise NotImplementedError

    @property
    def _headers(self):
        return {"Authorization": f"Bearer {self._token}"}

    @property
    def icon(self):
        """Return the default icon"""
        return ICON

    @property
    def state(self):
        return self.balance.get("confirmed_balance")

    @property
    def unit_of_measurement(self):
        """Returns the unit of measurement."""
        raise NotImplementedError

    @property
    def last_updated(self):
        """Returns date when it was last updated."""
        if self._last_updated != 'unknown':
            stamp = float(self._last_updated)
            return utc_from_timestamp(int(stamp))

    @property
    def state_attributes(self):
        """Returns the state attributes. """
        return {
            ATTR_FRIENDLY_NAME: self.name,
            ATTR_UNIT_OF_MEASUREMENT: self.unit_of_measurement,
            ATTR_LAST_UPDATED: self.last_updated,
        }

    @property
    def icon(self):
        """Return the icon."""
        raise NotImplementedError

    @property
    def confirmed_balance(self):
        return self.balance.get("confirmed_balance")

    @property
    def pending_balance(self):
        return self.balance.get("pending_balance")

    @property
    def device_state_attributes(self):
        return {"pending_balance": self.pending_balance, "confirmed_balance": self.confirmed_balance}

    def update(self):
        self.balance = requests.get(BALANCE_URL, headers=self._headers).json().get("data")

class MeliuzConfirmedBalanceSensor(MeliuzSensor):

    @property
    def _name_suffix(self):
        """Returns the name suffix of the sensor."""
        return BALANCE_CONFIRMED

    @property
    def icon(self):
        """Return the default icon"""
        return ICON

    @property
    def state(self):
        return self.balance.get("confirmed_balance")

    @property
    def unit_of_measurement(self):
        """Returns the unit of measurement."""
        return "R$"

    @property
    def confirmed_balance(self):
        return self.balance.get("confirmed_balance")

    @property
    def device_state_attributes(self):
        return {"confirmed_balance": self.confirmed_balance}


class MeliuzPendingBalanceSensor(MeliuzSensor):

    @property
    def _name_suffix(self):
        """Returns the name suffix of the sensor."""
        return PENDING_CONFIRMED

    @property
    def icon(self):
        """Return the default icon"""
        return ICON

    @property
    def unit_of_measurement(self):
        """Returns the unit of measurement."""
        return "R$"

    @property
    def state(self):
        return self.balance.get("pending_balance")

    @property
    def pending_balance(self):
        return self.balance.get("pending_balance")

    @property
    def device_state_attributes(self):
        return {"pending_balance": self.pending_balance}
