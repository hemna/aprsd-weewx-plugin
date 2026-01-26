Usage
=====

The APRSD Weewx Plugin provides two main functions:

1. **Weather Query Responses**: Responds to APRS messages with current weather data
2. **Automatic Weather Reporting**: Periodically sends weather packets to APRS-IS

Querying Weather via APRS
--------------------------

Once the plugin is configured and running, you can query weather data by sending an APRS message to your station's callsign. The plugin responds to messages that start with ``w`` or ``W``.

Example Interaction
~~~~~~~~~~~~~~~~~~~

Here's a typical interaction:

**You send:**
::

    WB4BOR-1>APRS,TCPIP*:>w WB4BOR

**Plugin responds:**
::

    WB4BOR>APRS,TCPIP*:>WX: 72.5F/54.0F Wind 5@270G12 65% RA 0.00 0.00/hr 29.92inHg

Response Format
~~~~~~~~~~~~~~~

The weather response follows this format:

::

    WX: <temp>/<dewpoint> Wind <speed>@<direction>G<gust> <humidity>% RA <day_rain> <rate>/hr <pressure>inHg

Field Breakdown
~~~~~~~~~~~~~~~

* **Temperature/Dewpoint**: Current temperature and dewpoint (Fahrenheit or Celsius)
* **Wind**: Wind speed (mph or m/s), direction in degrees, and gust speed
* **Humidity**: Relative humidity percentage
* **Rain**: Daily rainfall total and current rain rate
* **Pressure**: Barometric pressure (inHg or mBar)

Example Responses
~~~~~~~~~~~~~~~~~

**Imperial Units (Fahrenheit, mph, inHg):**
::

    WX: 72.5F/54.0F Wind 5@270G12 65% RA 0.00 0.00/hr 29.92inHg

**Metric Units (Celsius, m/s, mBar):**
::

    WX: 22.5C/12.2C Wind 2@270G5 65% RA 0.00 0.00/hr 1013.25mBar

**With Rain:**
::

    WX: 68.0F/55.0F Wind 8@180G15 72% RA 0.25 0.10/hr 30.05inHg

Automatic Weather Reporting
---------------------------

When latitude and longitude are configured, the plugin automatically sends weather packets to APRS-IS at regular intervals. These packets:

* Appear on APRS.fi and other APRS mapping services
* Include your station's position and weather data
* Are sent at the interval specified by ``report_interval`` (default: 60 seconds)

Example APRS Weather Packet
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The plugin sends standard APRS weather packets that look like this on APRS.fi:

::

    WB4BOR>APRS,TCPIP*:@251234z3745.50N/12225.00W_270/005g012t072r000p000P000h65b10130

This packet includes:
* Timestamp (25th day, 12:34 UTC)
* Position (37°45.50'N, 122°25.00'W)
* Wind direction 270° at 5 mph, gusting to 12 mph
* Temperature 72°F
* Rainfall data
* Pressure and humidity

Troubleshooting
---------------

No Response to Weather Queries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the plugin doesn't respond to weather queries:

1. Check that the plugin is enabled in your APRSD configuration
2. Verify MQTT connection is working (check APRSD logs)
3. Ensure Weewx is publishing to the ``weather/loop`` topic
4. Check that MQTT credentials are correct

No Automatic Reports
~~~~~~~~~~~~~~~~~~~~~

If automatic weather reports aren't appearing:

1. Verify ``latitude`` and ``longitude`` are configured
2. Check that your APRSD callsign is set correctly
3. Ensure APRSD is connected to APRS-IS
4. Review the ``report_interval`` setting

MQTT Connection Issues
~~~~~~~~~~~~~~~~~~~~~~~

If you see MQTT connection errors:

1. Verify the MQTT broker is running and accessible
2. Check firewall settings for the MQTT port
3. Verify MQTT username and password (if required)
4. Test MQTT connection with a tool like ``mosquitto_sub``:

   .. code-block:: console

       $ mosquitto_sub -h localhost -p 1883 -t weather/loop

Testing the Plugin
------------------

You can test the plugin by:

1. **Checking APRSD logs** for plugin initialization messages
2. **Sending a test message** via APRS to your callsign with "w" or "W"
3. **Monitoring MQTT traffic** to verify Weewx is publishing data
4. **Checking APRS.fi** for automatic weather reports (if enabled)

Example Test Session
~~~~~~~~~~~~~~~~~~~~

1. Start APRSD with the plugin enabled
2. Wait for MQTT connection confirmation in logs
3. Send APRS message: ``w YOURCALL``
4. Receive weather response
5. Check APRS.fi for automatic reports (if configured)
