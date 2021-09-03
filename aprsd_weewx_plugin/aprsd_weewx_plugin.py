"""Main module."""
import datetime
import json
import logging
import queue

import paho.mqtt.client as mqtt
from aprsd import plugin, threads, trace, utils


LOG = logging.getLogger("APRSD")

mqtt_queue = queue.Queue(maxsize=20)


class WeewxMQTTPlugin(plugin.APRSDRegexCommandPluginBase):
    """Weather

    Syntax of request

    weather

    """

    version = "1.0"
    command_regex = "^[wW]"
    command_name = "weather"

    enabled = False

    def setup(self):
        """Ensure that the plugin has been configured."""
        try:
            LOG.info("Looking for weewx.mqtt.host config entry")
            utils.check_config_option(self.config, ["services", "weewx", "mqtt", "host"])
            self.enabled = True
        except Exception as ex:
            LOG.error(f"Failed to find config weewx:mqtt:host {ex}")
            LOG.info("Disabling the weewx mqtt subsription thread.")
            self.enabled = False

    def create_threads(self):
        if self.enabled:
            LOG.info("Creating WeewxMQTTThread")
            return WeewxMQTTThread(
                msg_queues=mqtt_queue,
                config=self.config,
            )
        else:
            LOG.info("WeewxMQTTPlugin not enabled due to missing config.")

    @trace.trace
    def process(self, packet):
        LOG.info("WeewxMQTT Plugin")
        packet.get("from")
        packet.get("message_text", None)
        # ack = packet.get("msgNo", "0")

        if self.enabled:
            # see if there are any weather messages in the queue.
            msg = None
            LOG.info("Looking for a message")
            if not mqtt_queue.empty():
                msg = mqtt_queue.get(timeout=1)
            else:
                msg = mqtt_queue.get(timeout=30)

            if not msg:
                return "No Weewx data"
            else:
                LOG.info(f"Got a message {msg}")
                # Wants format of 71.5F/54.0F Wind 1@49G7 54%
                if "outTemp_F" in msg:
                    temperature = "{:0.2f}F".format(float(msg["outTemp_F"]))
                    dewpoint = "{:0.2f}F".format(float(msg["dewpoint_F"]))
                else:
                    temperature = "{:0.2f}C".format(float(msg["outTemp_C"]))
                    dewpoint = "{:0.2f}C".format(float(msg["dewpoint_C"]))

                wind_direction = "{:0.0f}".format(float(msg["windDir"]))
                if "windSpeed_mps" in msg:
                    wind_speed = "{:0.0f}".format(float(msg["windSpeed_mps"]))
                    wind_gust = "{:0.0f}".format(float(msg["windGust_mps"]))
                else:
                    wind_speed = "{:0.0f}".format(float(msg["windSpeed_mph"]))
                    wind_gust = "{:0.0f}".format(float(msg["windGust_mph"]))

                wind = "{}@{}G{}".format(
                    wind_speed,
                    wind_direction,
                    wind_gust,
                )

                humidity = "{:0.0f}%".format(float(msg["outHumidity"]))

                ts = int("{:0.0f}".format(float(msg["dateTime"])))
                ts = datetime.datetime.fromtimestamp(ts)

                wx = "{} {}/{} Wind {} {}".format(
                    ts,
                    temperature,
                    dewpoint,
                    wind,
                    humidity,
                )
                LOG.debug(
                    "Got weather {} -- len {}".format(
                        wx,
                        len(wx),
                    ),
                )
                return wx

        else:
            return "WeewxMQTT Not enabled"


class WeewxMQTTThread(threads.APRSDThread):
    def __init__(self, msg_queues, config):
        super().__init__("WeewxMQTTThread")
        self.msg_queues = msg_queues
        self.config = config
        self.setup()

    def setup(self):
        LOG.info("Creating mqtt client")
        self._mqtt_host = self.config["services"]["weewx"]["mqtt"]["host"]
        self._mqtt_port = self.config["services"]["weewx"]["mqtt"]["port"]
        self._mqtt_user = self.config["services"]["weewx"]["mqtt"]["user"]
        self._mqtt_pass = self.config["services"]["weewx"]["mqtt"]["password"]
        LOG.info(
            "Connecting to mqtt {}:XXXX@{}:{}".format(
                self._mqtt_user,
                self._mqtt_host,
                self._mqtt_port,
            ),
        )
        self.client = mqtt.Client(client_id="WeewxMQTTPlugin")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self._mqtt_host, self._mqtt_port, 60)
        self.client.username_pw_set(username="hemna", password="ass")

    def on_connect(self, client, userdata, flags, rc):
        LOG.info(f"Connected to MQTT {self._mqtt_host} ({rc})")
        client.subscribe("weather/loop")

    def on_message(self, client, userdata, msg):
        #LOG.info(msg.payload)
        wx_data = json.loads(msg.payload)
        LOG.debug(f"Got WX data {wx_data}")
        mqtt_queue.put(wx_data)

    def stop(self):
        LOG.info("calling disconnect")
        self.thread_stop = True
        self.client.disconnect()

    def loop(self):
        LOG.info("Looping bitch")
        self.client.loop_forever()
        return True
