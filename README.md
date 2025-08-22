# NC-2 Controller Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

This custom integration allows you to control and monitor devices connected to an [NC-2 Controller](https://ambiot.io/products/nc-2) within Home Assistant.

It uses the official REST API for control and listens to the MQTT broker for instant status updates.

## Features

*   **Light Control:** Turn on/off, dim, and change the color temperature of your DALI lights.
*   **Relay Control:** Turn on/off relays connected to the NC-2 controller.
*   **Real-time Status:** Uses MQTT for instant status updates for both lights and relays.
*   **Auto-discovery:** Automatically discovers and adds all your lights and relays upon setup.
*   **UI Configuration:** Fully configurable through the Home Assistant user interface.

## Prerequisites

1.  A functional NC-2 Controller accessible on your network.
2.  A running MQTT Broker that both your Home Assistant instance and your NC-2 Controller are connected to.

## Installation

### Recommended: HACS (Home Assistant Community Store)

1.  Ensure you have [HACS](https://hacs.xyz/) installed.
2.  Go to HACS > Integrations > (three-dots menu) > Custom repositories.
3.  Add the URL to this repository.
4.  Select the category "Integration".
5.  The "NC2 Controller" integration will now appear. Click "Install".
6.  Restart Home Assistant.

### Manual Installation

1.  Using a file browser, navigate to the `custom_components` directory in your Home Assistant configuration folder.
2.  Create a new folder named `nc2_integration`.
3.  Copy all the files from this repository's `custom_components/nc2_integration/` directory into the new folder you created.
4.  Restart Home Assistant.

## Configuration

1.  Navigate to **Settings > Devices & Services**.
2.  Click **+ Add Integration**.
3.  Search for "NC2 Controller" and select it.
4.  In the configuration dialog, enter the following:
    *   **Host:** The IP address of your NC-2 Controller.
    *   **Username:** The username for the NC-2 Controller's web interface.
    *   **Password:** The password for the NC-2 Controller's web interface.
5.  Click **Submit**.

The integration will be set up, and your lights and relays will be automatically added.

## License

This project is licensed under the MIT License.
