"""
Integrate with NSone.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/nsone/
"""
import asyncio
from datetime import timedelta
import logging
import json

import voluptuous as vol

from homeassistant.const import CONF_API_KEY, CONF_DOMAIN, CONF_ZONE
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'nsone'
INTERVAL = timedelta(minutes=5)
IP_URL = 'https://api.ipify.org/?format=json'
UPDATE_URL = 'https://api.nsone.net/v1/zones'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_ZONE): cv.string,
        vol.Required(CONF_API_KEY): cv.string,
        vol.Optional(CONF_DOMAIN, default=None): cv.string,
    })
}, extra=vol.ALLOW_EXTRA)


@asyncio.coroutine
def async_setup(hass, config):
    """Initialize the nsone DNS component."""
    zone = config[DOMAIN][CONF_ZONE]
    if config[DOMAIN][CONF_DOMAIN]:
        domain = config[DOMAIN][CONF_DOMAIN]
    else:
        domain = zone
    api_key = config[DOMAIN][CONF_API_KEY]

    session = async_get_clientsession(hass)
    resp = yield from session.get(IP_URL)
    data = yield from resp.json()
    my_ip = data['ip']

    if not my_ip:
        return False

    result = yield from _update_nsonedns(session, zone, domain, api_key, my_ip)

    if not result:
        return False

    @asyncio.coroutine
    def update_domain_interval(now):
        """Update the nsone DNS entry."""
        resp = yield from session.get(IP_URL)
        data = yield from resp.json()
        my_ip = data['ip']

        if not my_ip:
            return False

        yield from _update_nsonedns(session, zone, domain, api_key, my_ip)

    async_track_time_interval(hass, update_domain_interval, INTERVAL)

    return result


@asyncio.coroutine
def _update_nsonedns(session, zone, domain, api_key, my_ip):
    """Update nsone DNS entry."""
    headers = {'X-NSONE-Key': api_key}
    payload = {"answers": [{"answer": [my_ip]}]}

    _LOGGER.debug("Updating NSone %s/%s/%s/A with %s",
                  UPDATE_URL, zone, domain, json.dumps(payload))
    resp = yield from session.post(
        "{}/{}/{}/A".format(UPDATE_URL, zone, domain),
        headers=headers,
        data=json.dumps(payload))

    if resp.status != 200:
        _LOGGER.warning(
            "Updating nsone zone/domain failed: %s/%s", zone, domain)
        return False

    return True
