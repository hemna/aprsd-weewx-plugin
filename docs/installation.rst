.. highlight:: shell

============
Installation
============

Prerequisites
-------------

Before installing the plugin, ensure you have:

* **APRSD** version 4.2.0 or higher installed and configured
* **Weewx** weather station software running and configured
* Access to an **MQTT broker** (local or remote)
* **Python** 3.8 or higher

Stable release
--------------

To install aprsd-weewx-plugin, run this command in your terminal:

.. code-block:: console

    $ pip install aprsd-weewx-plugin

This is the preferred method to install, as it will always install the most recent stable release.

If you don't have `pip`_ installed, this `Python installation guide`_ can guide
you through the process.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/


From sources
------------

The sources can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/hemna/aprsd-weewx-plugin

Or download the `tarball`_:

.. code-block:: console

    $ curl -OJL https://github.com/hemna/aprsd-weewx-plugin/tarball/master

Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ pip install .


Configuration
-------------

After installation, you need to configure the plugin in your APRSD configuration file.

Basic Configuration
~~~~~~~~~~~~~~~~~~~~

Add the plugin to your APRSD configuration (typically ``aprsd.yml``):

.. code-block:: yaml

    aprsd:
      enabled_plugins:
        - aprsd_weewx_plugin.weewx.WeewxMQTTPlugin

      aprsd_weewx_plugin:
        enabled: true
        mqtt_host: localhost
        mqtt_port: 1883
        mqtt_user: weewx
        mqtt_password: your_password_here

With Automatic Weather Reporting
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To enable automatic weather reporting to APRS-IS, add latitude and longitude:

.. code-block:: yaml

    aprsd_weewx_plugin:
      enabled: true
      mqtt_host: localhost
      mqtt_port: 1883
      mqtt_user: weewx
      mqtt_password: your_password_here
      latitude: 37.7749
      longitude: -122.4194
      report_interval: 300  # Report every 5 minutes (in seconds)

Configuration Options
~~~~~~~~~~~~~~~~~~~~~

* ``enabled`` (boolean): Enable/disable the plugin (default: false)
* ``mqtt_host`` (string): MQTT broker hostname (required)
* ``mqtt_port`` (integer): MQTT broker port (required)
* ``mqtt_user`` (string): MQTT username (optional)
* ``mqtt_password`` (string): MQTT password (optional, but recommended)
* ``latitude`` (float): Station latitude for automatic reporting (optional)
* ``longitude`` (float): Station longitude for automatic reporting (optional)
* ``report_interval`` (integer): Seconds between automatic reports (default: 60)

Weewx MQTT Setup
~~~~~~~~~~~~~~~~

Ensure your Weewx installation publishes weather data to MQTT. Add this to your Weewx configuration (``weewx.conf``):

.. code-block:: ini

    [MQTT]
        host = localhost
        port = 1883
        topic = weather/loop
        unit_system = US

The plugin subscribes to the ``weather/loop`` topic and expects JSON-formatted weather data.

Exporting Configuration
~~~~~~~~~~~~~~~~~~~~~~~

You can view all available configuration options using the CLI tool:

.. code-block:: console

    $ aprsd-weewx-plugin-export-config

This outputs all configuration options in JSON format.

.. _Github repo: https://github.com/hemna/aprsd-weewx-plugin
.. _tarball: https://github.com/hemna/aprsd-weewx-plugin/tarball/master
