# APRSD Weewx Plugin

[![PyPI](https://img.shields.io/pypi/v/aprsd-weewx-plugin.svg)](https://pypi.org/project/aprsd-weewx-plugin/)
[![Status](https://img.shields.io/pypi/status/aprsd-weewx-plugin.svg)](https://pypi.org/project/aprsd-weewx-plugin/)
[![Python Version](https://img.shields.io/pypi/pyversions/aprsd-weewx-plugin)](https://pypi.org/project/aprsd-weewx-plugin)
[![License](https://img.shields.io/pypi/l/aprsd-weewx-plugin)](https://opensource.org/licenses/GNU%20GPL%20v3.0)

[![Read the Docs](https://img.shields.io/readthedocs/aprsd-weewx-plugin/latest.svg?label=Read%20the%20Docs)](https://aprsd-weewx-plugin.readthedocs.io/)
[![Tests](https://github.com/hemna/aprsd-weewx-plugin/workflows/Tests/badge.svg)](https://github.com/hemna/aprsd-weewx-plugin/actions?workflow=Tests)
[![Codecov](https://codecov.io/gh/hemna/aprsd-weewx-plugin/branch/main/graph/badge.svg)](https://codecov.io/gh/hemna/aprsd-weewx-plugin)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

## Features

* **MQTT Integration**: Connects to Weewx weather station via MQTT to receive real-time weather data
* **APRS Weather Queries**: Responds to APRS messages with current weather conditions
* **Automatic Weather Reporting**: Optionally reports weather data to APRS-IS at regular intervals
* **Comprehensive Weather Data**: Includes temperature, dewpoint, wind speed/direction, humidity, pressure, and rainfall
* **Flexible Units**: Supports both imperial (Fahrenheit, mph, inHg) and metric (Celsius, m/s, mBar) units

## Requirements

* **APRSD**: Version 4.2.0 or higher
* **Weewx**: Weather station software configured to publish MQTT messages
* **MQTT Broker**: Accessible MQTT server (e.g., Mosquitto, Eclipse Mosquitto)
* **Python**: 3.8 or higher

## Installation

You can install **APRSD Weewx Plugin** via [pip](https://pip.pypa.io/) from [PyPI](https://pypi.org/):

```console
$ pip install aprsd-weewx-plugin
```

## Configuration

### Basic Configuration

Add the plugin to your APRSD configuration file (typically `aprsd.yml`):

```yaml
aprsd:
  enabled_plugins:
    - aprsd_weewx_plugin.weewx.WeewxMQTTPlugin

  aprsd_weewx_plugin:
    enabled: true
    mqtt_host: localhost
    mqtt_port: 1883
    mqtt_user: weewx
    mqtt_password: your_password_here
```

### Automatic Weather Reporting

To enable automatic weather reporting to APRS-IS, add latitude and longitude:

```yaml
aprsd_weewx_plugin:
  enabled: true
  mqtt_host: localhost
  mqtt_port: 1883
  latitude: 37.7749
  longitude: -122.4194
  report_interval: 300  # Report every 5 minutes (in seconds)
```

### Weewx MQTT Configuration

Ensure your Weewx installation is configured to publish weather data to MQTT. Add this to your Weewx configuration:

```ini
[MQTT]
    host = localhost
    port = 1883
    topic = weather/loop
    unit_system = US
```

## Usage

### Querying Weather via APRS

Once configured, you can query weather data by sending an APRS message to your station's callsign with a message starting with `w` or `W`:

**Example APRS Interaction:**

```text
You: WB4BOR-1>APRS,TCPIP*:>w WB4BOR
WB4BOR: WX: 72.5F/54.0F Wind 5@270G12 65% RA 0.00 0.00/hr 29.92inHg
```

**Response Format:**

```text
WX: <temp>/<dewpoint> Wind <speed>@<direction>G<gust> <humidity>% RA <day_rain> <rate>/hr <pressure>inHg
```

**Example Response Breakdown:**

* `72.5F/54.0F` - Temperature 72.5°F, Dewpoint 54.0°F
* `Wind 5@270G12` - Wind speed 5 mph from 270° (west) with gusts to 12 mph
* `65%` - Relative humidity
* `RA 0.00 0.00/hr` - Daily rainfall 0.00 inches, current rate 0.00 inches/hour
* `29.92inHg` - Barometric pressure

### Automatic Weather Reporting

When latitude and longitude are configured, the plugin automatically sends weather packets to APRS-IS at the configured interval. These packets appear on APRS.fi and other APRS services.

### Exporting Configuration

You can export the plugin's configuration options using the CLI tool:

```console
$ aprsd-weewx-plugin-export-config
```

This will output all available configuration options in JSON format.

## Contributing

Contributions are very welcome.
To learn more, see the [Contributor Guide](contributing).

## License

Distributed under the terms of the [GNU GPL v3.0 license](https://opensource.org/licenses/GNU%20GPL%20v3.0),
**APRSD Weewx Plugin** is free and open source software.

## Issues

If you encounter any problems,
please [file an issue](https://github.com/hemna/aprsd-weewx-plugin/issues) along with a detailed description.

## Credits

This project was generated from [@hemna](https://github.com/hemna)'s [APRSD Plugin Python Cookiecutter](https://github.com/hemna/cookiecutter-aprsd-plugin) template.
