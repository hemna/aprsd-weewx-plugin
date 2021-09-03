"""Main module."""
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
            utils.check_config_option(self.config, ["services", "weewx", "mqtt", "host"])
            self.enabled = True
        except Exception as ex:
            LOG.error(f"Failed to find config weewx:mqtt:host {ex}")
            LOG.info("Disabling the weewx mqtt subsription thread.")
            self.enabled = False

    def create_threads(self):
        if self.enabled:
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
            msg = mqtt_queue.get(timeout=1)
            if not msg:
                return "No Weewx data"
            else:
                temp = msg["outTemp"]
                return temp

        else:
            return "WeewxMQTT Not enabled"


class WeewxMQTTThread(threads.APRSDThread):
    def __init__(self, msg_queues, config):
        super().__init__("WeewxMQTTThread")
        self.msg_queues = msg_queues
        self.config = config
        self.setup()

    def setup(self):
        self._mqtt_host = self.config["services"]["weewx"]["mqtt"]["host"]
        self._mqtt_port = self.config["services"]["weewx"]["mqtt"]["port"]
        self.client = mqtt.Client(self._mqtt_host, self._mqtt_port, 60)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        LOG.info(f"Connected to MQTT {self._mqtt_host}")
        client.subscribe("weather/loop")

    def on_message(self, client, userdata, msg):
        LOG.debug("adding msg to queue")
        mqtt_queue.put(msg.payload)

    def stop(self):
        self.client.disconnect()
        self.thread_stop = True

    def loop(self):
        self.client.loop_forever()
        return True
