"""Constants for the NC2 Controller integration."""

DOMAIN = "nc2_integration"

# Keys for config flow
CONF_HOST = "host"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

# Data keys in hass.data for API client
DATA_NC2_API = "nc2_api"

# API endpoints (relative paths)
API_LOGIN = "/api/v1/login"
API_RELAYS_STATUS = "/api/v1/modules/relay/1"
API_RELAY_CONTROL = "/api/v1/relays/{relay_id}/control"
API_LUMINAIRES_DIM = "/api/v1/luminaires/{luminaire_id}/dim"
API_LUMINAIRES_COLOR_TEMP = "/api/v1/luminaires/{luminaire_id}/colorOrLightTemperature"
API_DEVICES_LIST = "/api/v1/processRequestListOfModules" # Эндпоинт для получения списка модулей

# MQTT topics (based on your mqtt.yaml, adjust if needed)
MQTT_TOPIC_BASE = "nc2/{device_id}/back/{module_id}" # Возможно, эти ID динамические
MQTT_TOPIC_RELAY_STATUS = MQTT_TOPIC_BASE + "/relays/{relay_id}"
MQTT_TOPIC_LUMINAIRE_STATUS = MQTT_TOPIC_BASE + "/luminaires/{luminaire_id}"

# Default values (if any)
DEFAULT_SCAN_INTERVAL = 30 # seconds for polling