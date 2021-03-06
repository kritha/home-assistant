"""The tests for the Mqtt vacuum platform."""
import pytest

from homeassistant.setup import async_setup_component
from homeassistant.const import (
    CONF_PLATFORM, STATE_OFF, STATE_ON, STATE_UNAVAILABLE, CONF_NAME)
from homeassistant.components import vacuum, mqtt
from homeassistant.components.vacuum import (
    ATTR_BATTERY_LEVEL, ATTR_BATTERY_ICON, ATTR_STATUS,
    ATTR_FAN_SPEED, mqtt as mqttvacuum)
from homeassistant.components.mqtt import CONF_COMMAND_TOPIC
from homeassistant.components.mqtt.discovery import async_start
from tests.common import (
    async_mock_mqtt_component,
    async_fire_mqtt_message, MockConfigEntry)
from tests.components.vacuum import common


default_config = {
    CONF_PLATFORM: 'mqtt',
    CONF_NAME: 'mqtttest',
    CONF_COMMAND_TOPIC: 'vacuum/command',
    mqttvacuum.CONF_SEND_COMMAND_TOPIC: 'vacuum/send_command',
    mqttvacuum.CONF_BATTERY_LEVEL_TOPIC: 'vacuum/state',
    mqttvacuum.CONF_BATTERY_LEVEL_TEMPLATE:
        '{{ value_json.battery_level }}',
    mqttvacuum.CONF_CHARGING_TOPIC: 'vacuum/state',
    mqttvacuum.CONF_CHARGING_TEMPLATE: '{{ value_json.charging }}',
    mqttvacuum.CONF_CLEANING_TOPIC: 'vacuum/state',
    mqttvacuum.CONF_CLEANING_TEMPLATE: '{{ value_json.cleaning }}',
    mqttvacuum.CONF_DOCKED_TOPIC: 'vacuum/state',
    mqttvacuum.CONF_DOCKED_TEMPLATE: '{{ value_json.docked }}',
    mqttvacuum.CONF_STATE_TOPIC: 'vacuum/state',
    mqttvacuum.CONF_STATE_TEMPLATE: '{{ value_json.state }}',
    mqttvacuum.CONF_FAN_SPEED_TOPIC: 'vacuum/state',
    mqttvacuum.CONF_FAN_SPEED_TEMPLATE: '{{ value_json.fan_speed }}',
    mqttvacuum.CONF_SET_FAN_SPEED_TOPIC: 'vacuum/set_fan_speed',
    mqttvacuum.CONF_FAN_SPEED_LIST: ['min', 'medium', 'high', 'max'],
}


@pytest.fixture
def mock_publish(hass):
    """Initialize components."""
    yield hass.loop.run_until_complete(async_mock_mqtt_component(hass))


async def test_default_supported_features(hass, mock_publish):
    """Test that the correct supported features."""
    assert await async_setup_component(hass, vacuum.DOMAIN, {
        vacuum.DOMAIN: default_config,
    })
    entity = hass.states.get('vacuum.mqtttest')
    entity_features = \
        entity.attributes.get(mqttvacuum.CONF_SUPPORTED_FEATURES, 0)
    assert sorted(mqttvacuum.services_to_strings(entity_features)) == \
        sorted(['turn_on', 'turn_off', 'stop',
                'return_home', 'battery', 'status',
                'clean_spot'])


async def test_all_commands(hass, mock_publish):
    """Test simple commands to the vacuum."""
    default_config[mqttvacuum.CONF_SUPPORTED_FEATURES] = \
        mqttvacuum.services_to_strings(mqttvacuum.ALL_SERVICES)

    assert await async_setup_component(hass, vacuum.DOMAIN, {
        vacuum.DOMAIN: default_config,
    })

    common.turn_on(hass, 'vacuum.mqtttest')
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    mock_publish.async_publish.assert_called_once_with(
        'vacuum/command', 'turn_on', 0, False)
    mock_publish.async_publish.reset_mock()

    common.turn_off(hass, 'vacuum.mqtttest')
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    mock_publish.async_publish.assert_called_once_with(
        'vacuum/command', 'turn_off', 0, False)
    mock_publish.async_publish.reset_mock()

    common.stop(hass, 'vacuum.mqtttest')
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    mock_publish.async_publish.assert_called_once_with(
        'vacuum/command', 'stop', 0, False)
    mock_publish.async_publish.reset_mock()

    common.clean_spot(hass, 'vacuum.mqtttest')
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    mock_publish.async_publish.assert_called_once_with(
        'vacuum/command', 'clean_spot', 0, False)
    mock_publish.async_publish.reset_mock()

    common.locate(hass, 'vacuum.mqtttest')
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    mock_publish.async_publish.assert_called_once_with(
        'vacuum/command', 'locate', 0, False)
    mock_publish.async_publish.reset_mock()

    common.start_pause(hass, 'vacuum.mqtttest')
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    mock_publish.async_publish.assert_called_once_with(
        'vacuum/command', 'start_pause', 0, False)
    mock_publish.async_publish.reset_mock()

    common.return_to_base(hass, 'vacuum.mqtttest')
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    mock_publish.async_publish.assert_called_once_with(
        'vacuum/command', 'return_to_base', 0, False)
    mock_publish.async_publish.reset_mock()

    common.set_fan_speed(hass, 'high', 'vacuum.mqtttest')
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    mock_publish.async_publish.assert_called_once_with(
        'vacuum/set_fan_speed', 'high', 0, False)
    mock_publish.async_publish.reset_mock()

    common.send_command(hass, '44 FE 93', entity_id='vacuum.mqtttest')
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    mock_publish.async_publish.assert_called_once_with(
        'vacuum/send_command', '44 FE 93', 0, False)


async def test_status(hass, mock_publish):
    """Test status updates from the vacuum."""
    default_config[mqttvacuum.CONF_SUPPORTED_FEATURES] = \
        mqttvacuum.services_to_strings(mqttvacuum.ALL_SERVICES)

    assert await async_setup_component(hass, vacuum.DOMAIN, {
        vacuum.DOMAIN: default_config,
    })

    message = """{
        "battery_level": 54,
        "cleaning": true,
        "docked": false,
        "charging": false,
        "fan_speed": "max"
    }"""
    async_fire_mqtt_message(hass, 'vacuum/state', message)
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    state = hass.states.get('vacuum.mqtttest')
    assert STATE_ON == state.state
    assert 'mdi:battery-50' == \
        state.attributes.get(ATTR_BATTERY_ICON)
    assert 54 == state.attributes.get(ATTR_BATTERY_LEVEL)
    assert 'max' == state.attributes.get(ATTR_FAN_SPEED)

    message = """{
        "battery_level": 61,
        "docked": true,
        "cleaning": false,
        "charging": true,
        "fan_speed": "min"
    }"""

    async_fire_mqtt_message(hass, 'vacuum/state', message)
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    state = hass.states.get('vacuum.mqtttest')
    assert STATE_OFF == state.state
    assert 'mdi:battery-charging-60' == \
        state.attributes.get(ATTR_BATTERY_ICON)
    assert 61 == state.attributes.get(ATTR_BATTERY_LEVEL)
    assert 'min' == state.attributes.get(ATTR_FAN_SPEED)


async def test_battery_template(hass, mock_publish):
    """Test that you can use non-default templates for battery_level."""
    default_config.update({
        mqttvacuum.CONF_SUPPORTED_FEATURES:
            mqttvacuum.services_to_strings(mqttvacuum.ALL_SERVICES),
        mqttvacuum.CONF_BATTERY_LEVEL_TOPIC: "retroroomba/battery_level",
        mqttvacuum.CONF_BATTERY_LEVEL_TEMPLATE: "{{ value }}"
    })

    assert await async_setup_component(hass, vacuum.DOMAIN, {
        vacuum.DOMAIN: default_config,
    })

    async_fire_mqtt_message(hass, 'retroroomba/battery_level', '54')
    await hass.async_block_till_done()
    state = hass.states.get('vacuum.mqtttest')
    assert 54 == state.attributes.get(ATTR_BATTERY_LEVEL)
    assert state.attributes.get(ATTR_BATTERY_ICON) == \
        'mdi:battery-50'


async def test_status_invalid_json(hass, mock_publish):
    """Test to make sure nothing breaks if the vacuum sends bad JSON."""
    default_config[mqttvacuum.CONF_SUPPORTED_FEATURES] = \
        mqttvacuum.services_to_strings(mqttvacuum.ALL_SERVICES)

    assert await async_setup_component(hass, vacuum.DOMAIN, {
        vacuum.DOMAIN: default_config,
    })

    async_fire_mqtt_message(hass, 'vacuum/state', '{"asdfasas false}')
    await hass.async_block_till_done()
    state = hass.states.get('vacuum.mqtttest')
    assert STATE_OFF == state.state
    assert "Stopped" == state.attributes.get(ATTR_STATUS)


async def test_default_availability_payload(hass, mock_publish):
    """Test availability by default payload with defined topic."""
    default_config.update({
        'availability_topic': 'availability-topic'
    })

    assert await async_setup_component(hass, vacuum.DOMAIN, {
        vacuum.DOMAIN: default_config,
    })

    state = hass.states.get('vacuum.mqtttest')
    assert STATE_UNAVAILABLE == state.state

    async_fire_mqtt_message(hass, 'availability-topic', 'online')
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    state = hass.states.get('vacuum.mqtttest')
    assert STATE_UNAVAILABLE != state.state

    async_fire_mqtt_message(hass, 'availability-topic', 'offline')
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    state = hass.states.get('vacuum.mqtttest')
    assert STATE_UNAVAILABLE == state.state


async def test_custom_availability_payload(hass, mock_publish):
    """Test availability by custom payload with defined topic."""
    default_config.update({
        'availability_topic': 'availability-topic',
        'payload_available': 'good',
        'payload_not_available': 'nogood'
    })

    assert await async_setup_component(hass, vacuum.DOMAIN, {
        vacuum.DOMAIN: default_config,
    })

    state = hass.states.get('vacuum.mqtttest')
    assert STATE_UNAVAILABLE == state.state

    async_fire_mqtt_message(hass, 'availability-topic', 'good')
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    state = hass.states.get('vacuum.mqtttest')
    assert STATE_UNAVAILABLE != state.state

    async_fire_mqtt_message(hass, 'availability-topic', 'nogood')
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    state = hass.states.get('vacuum.mqtttest')
    assert STATE_UNAVAILABLE == state.state


async def test_discovery_removal_vacuum(hass, mock_publish):
    """Test removal of discovered vacuum."""
    entry = MockConfigEntry(domain=mqtt.DOMAIN)
    await async_start(hass, 'homeassistant', {}, entry)

    data = (
        '{ "name": "Beer",'
        '  "command_topic": "test_topic" }'
    )

    async_fire_mqtt_message(hass, 'homeassistant/vacuum/bla/config',
                            data)
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    state = hass.states.get('vacuum.beer')
    assert state is not None
    assert state.name == 'Beer'

    async_fire_mqtt_message(hass, 'homeassistant/vacuum/bla/config', '')
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    state = hass.states.get('vacuum.beer')
    assert state is None


async def test_discovery_update_vacuum(hass, mock_publish):
    """Test update of discovered vacuum."""
    entry = MockConfigEntry(domain=mqtt.DOMAIN)
    await async_start(hass, 'homeassistant', {}, entry)

    data1 = (
        '{ "name": "Beer",'
        '  "command_topic": "test_topic" }'
    )
    data2 = (
        '{ "name": "Milk",'
        '  "command_topic": "test_topic" }'
    )

    async_fire_mqtt_message(hass, 'homeassistant/vacuum/bla/config',
                            data1)
    await hass.async_block_till_done()

    state = hass.states.get('vacuum.beer')
    assert state is not None
    assert state.name == 'Beer'

    async_fire_mqtt_message(hass, 'homeassistant/vacuum/bla/config',
                            data2)
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    state = hass.states.get('vacuum.beer')
    assert state is not None
    assert state.name == 'Milk'
    state = hass.states.get('vacuum.milk')
    assert state is None
