"""Test the NO-IP component."""
import asyncio
import json
from datetime import timedelta

import pytest

from homeassistant.setup import async_setup_component
from homeassistant.components import nsone
from homeassistant.util.dt import utcnow

from tests.common import async_fire_time_changed

API_KEY = 'xyz789'

DOMAIN = 'test.example.com'

IP_RESP = "{\"ip\": \"0.0.0.0\"}"

PAYLOAD = {'answers': [{'answer': ['0.0.0.0']}]}

UPDATE_URL = nsone.UPDATE_URL

ZONE = 'test.example.com'


@pytest.fixture
def setup_no_ip(hass, aioclient_mock):
    """Fixture that sets up NSone."""
    aioclient_mock.post(
        "{}/{}/{}/A".format(UPDATE_URL, ZONE, DOMAIN),
        headers={'X-NSONE-Key': API_KEY},
        data=json.dumps(PAYLOAD))

    aioclient_mock.get(
        nsone.IP_URL,
        json=json.loads(IP_RESP))

    hass.loop.run_until_complete(async_setup_component(hass, nsone.DOMAIN, {
        nsone.DOMAIN: {
            'api_key': API_KEY,
            'domain': DOMAIN,
            'zone': ZONE,
        }
    }))


@asyncio.coroutine
def test_setup(hass, aioclient_mock):
    """Test setup works if update passes."""
    aioclient_mock.post(
        "{}/{}/{}/A".format(UPDATE_URL, ZONE, DOMAIN),
        headers={'X-NSONE-Key': API_KEY},
        data=json.dumps(PAYLOAD))

    aioclient_mock.get(
        nsone.IP_URL,
        json=json.loads(IP_RESP))

    result = yield from async_setup_component(hass, nsone.DOMAIN, {
        nsone.DOMAIN: {
            'api_key': API_KEY,
            'domain': DOMAIN,
            'zone': ZONE,
        }
    })
    assert result
    assert aioclient_mock.call_count == 2

    async_fire_time_changed(hass, utcnow() + timedelta(minutes=5))
    yield from hass.async_block_till_done()
    assert aioclient_mock.call_count == 4


@asyncio.coroutine
def test_setup_when_update_fails(hass, aioclient_mock):
    """Test setup fails if first update fails."""
    aioclient_mock.post(
        "{}/{}/{}/A".format(UPDATE_URL, ZONE, DOMAIN),
        headers={'X-NSONE-Key': API_KEY},
        data=json.dumps(PAYLOAD),
        status=400)

    aioclient_mock.get(
        nsone.IP_URL,
        json=json.loads(IP_RESP))

    result = yield from async_setup_component(hass, nsone.DOMAIN, {
        nsone.DOMAIN: {
            'api_key': API_KEY,
            'domain': DOMAIN,
            'zone': ZONE,
        }
    })
    assert not result
    assert aioclient_mock.call_count == 2


@asyncio.coroutine
def test_setup_fails_if_wrong_auth(hass, aioclient_mock):
    """Test setup fails if first update fails through wrong authentication."""
    aioclient_mock.post(
        "{}/{}/{}/A".format(UPDATE_URL, ZONE, DOMAIN),
        headers={'X-NSONE-Key': 'GIBBERISH'},
        data=json.dumps(PAYLOAD),
        status=400)

    aioclient_mock.get(
        nsone.IP_URL,
        json=json.loads(IP_RESP))

    result = yield from async_setup_component(hass, nsone.DOMAIN, {
        nsone.DOMAIN: {
            'api_key': API_KEY,
            'domain': DOMAIN,
            'zone': ZONE,
        }
    })
    assert not result
    assert aioclient_mock.call_count == 2
