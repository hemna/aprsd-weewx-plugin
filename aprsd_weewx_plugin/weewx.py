"""Main module."""
import datetime
import json
import logging
import queue
import time

import aprsd.messaging
import paho.mqtt.client as mqtt
from aprsd import plugin, threads


LOG = logging.getLogger("APRSD")


class ClearableQueue(queue.Queue):

    def clear(self):
        try:
            while True:
                self.get_nowait()
        except queue.Empty:
            pass


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
        LOG.info("Looking for weewx.mqtt.host config entry")
        if self.config.exists("services.weewx.mqtt.host"):
            self.enabled = True
        else:
            LOG.error("Failed to find config weewx:mqtt:host")
            LOG.info("Disabling the weewx mqtt subsription thread.")
            self.enabled = False

    def create_threads(self):
        if self.enabled:
            LOG.info("Creating WeewxMQTTThread")
            self.queue = ClearableQueue(maxsize=1)
            self.wx_queue = queue.Queue(maxsize=2)
            mqtt_thread = WeewxMQTTThread(
                config=self.config,
                msg_queues=self.queue,
                wx_queue=self.wx_queue,
            )
            threads = [mqtt_thread]

            # if we have position and a callsign to report
            # Then we can periodically report weather data
            # to APRS
            if (
                self.config.exists("services.weewx.location.latitude") and
                self.config.exists("services.weewx.location.longitude")
            ):
                LOG.info("Creating WeewxWXAPRSThread")
                wx_thread = WeewxWXAPRSThread(
                    config=self.config,
                    wx_queue=self.wx_queue,
                )
                threads.append(wx_thread)
            else:
                LOG.info(
                    "NOT starting Weewx WX APRS Thread due to missing "
                    "GPS location settings.",
                )

            return threads
        else:
            LOG.info("WeewxMQTTPlugin not enabled due to missing config.")

    def process(self, packet):
        LOG.info("WeewxMQTT Plugin")
        packet.get("from")
        packet.get("message_text", None)
        # ack = packet.get("msgNo", "0")

        if self.enabled:
            # see if there are any weather messages in the queue.
            msg = None
            LOG.info("Looking for a message")
            if not self.queue.empty():
                msg = self.queue.get(timeout=1)
            else:
                try:
                    msg = self.queue.get(timeout=30)
                except Exception:
                    return "No Weewx Data"

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

                wind_direction = "{:0.0f}".format(float(msg.get("windDir", 0)))
                LOG.info(f"wind direction {wind_direction}")
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

                # do rain in format of last hour/day/month/year

                rain = "RA {:.2f} {:.2f}/hr".format(
                    float(msg.get("dayRain_in", 0.00)),
                    float(msg.get("rainRate_inch_per_hour", 0.00)),
                )

                wx = "WX: {}/{} Wind {} {} {} {:.2f}inHg".format(
                    temperature,
                    dewpoint,
                    wind,
                    humidity,
                    rain,
                    float(msg.get("pressure_inHg", 0.00)),
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
    def __init__(self, config, msg_queues, wx_queue):
        super().__init__("WeewxMQTTThread")
        self.config = config
        self.msg_queues = msg_queues
        self.wx_queue = wx_queue
        self.setup()

    def setup(self):
        LOG.info("Creating mqtt client")
        self._mqtt_host = self.config["services"]["weewx"]["mqtt"]["host"]
        self._mqtt_port = self.config["services"]["weewx"]["mqtt"]["port"]
        LOG.info(
            "Connecting to mqtt {}:{}".format(
                self._mqtt_host,
                self._mqtt_port,
            ),
        )
        self.client = mqtt.Client(client_id="WeewxMQTTPlugin")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self._mqtt_host, self._mqtt_port, 60)
        if self.config.exists("services.weewx.mqtt.user"):
            username = self.config.get("services.weewx.mqtt.user")
            password = self.config.get("services.weewx.mqtt.password")
            LOG.info(f"Using MQTT username/password {username}/XXXXXX")
            self.client.username_pw_set(
                username=username,
                password=password,
            )
        else:
            LOG.info("Not using MQTT username/password")

    def on_connect(self, client, userdata, flags, rc):
        LOG.info(f"Connected to MQTT {self._mqtt_host} ({rc})")
        client.subscribe("weather/loop")

    def on_message(self, client, userdata, msg):
        wx_data = json.loads(msg.payload)
        LOG.debug(f"Got WX data {wx_data}")
        # Make sure we have only 1 item in the queue
        if self.msg_queues.qsize() >= 1:
            self.msg_queues.clear()
        self.msg_queues.put(wx_data)
        self.wx_queue.put(wx_data)

    def stop(self):
        LOG.info("Disconnecting from MQTT")
        self.thread_stop = True
        self.client.loop_stop()
        self.client.disconnect()

    def loop(self):
        self.client.loop_forever()
        # self.client.loop(timeout=10, max_packets=10)
        return True


class WeewxWXAPRSThread(threads.APRSDThread):
    def __init__(self, config,  wx_queue):
        super().__init__(self.__class__.__name__)
        self.config = config
        self.wx_queue = wx_queue
        self.latitude = self.config.get("services.weewx.location.latitude")
        self.longitude = self.config.get("services.weewx.location.longitude")
        self.callsign = self.config.get("services.weewx.callsign")
        self.last_send = datetime.datetime.now()

        if self.latitude and self.longitude:
            self.position = self.get_latlon(
                float(self.latitude),
                float(self.longitude),
            )
        self.address = f"{self.callsign}>APRS,TCPIP*:"

    def decdeg2dmm_m(self, degrees_decimal):
        is_positive = degrees_decimal >= 0
        degrees_decimal = abs(degrees_decimal)
        minutes, seconds = divmod(degrees_decimal * 3600, 60)
        degrees, minutes = divmod(minutes, 60)
        degrees = degrees if is_positive else -degrees

        # degrees = str(int(degrees)).zfill(2).replace("-", "0")
        degrees = abs(int(degrees))
        # minutes = str(round(minutes + (seconds / 60), 2)).zfill(5)
        minutes = int(round(minutes + (seconds / 60), 2))
        hundredths = round(seconds / 60, 2)

        return {
            "degrees": degrees, "minutes": minutes, "seconds": seconds,
            "hundredths": hundredths,
        }

    def convert_latitude(self, degrees_decimal):
        det = self.decdeg2dmm_m(degrees_decimal)
        if degrees_decimal > 0:
            direction = "N"
        else:
            direction = "S"

        degrees = str(det.get("degrees")).zfill(2)
        minutes = str(det.get("minutes")).zfill(2)
        det.get("seconds")
        hundredths = str(det.get("hundredths")).split(".")[1]

        LOG.debug(
            f"LAT degress {degrees}  minutes {str(minutes)} "
            "seconds {seconds} hundredths {hundredths} direction {direction}",
        )

        lat = f"{degrees}{str(minutes)}.{hundredths}{direction}"
        return lat

    def convert_longitude(self, degrees_decimal):
        det = self.decdeg2dmm_m(degrees_decimal)
        if degrees_decimal > 0:
            direction = "E"
        else:
            direction = "W"

        degrees = str(det.get("degrees")).zfill(3)
        minutes = str(det.get("minutes")).zfill(2)
        det.get("seconds")
        hundredths = str(det.get("hundredths")).split(".")[1]

        LOG.debug(
            f"LON degress {degrees}  minutes {str(minutes)} "
            "seconds {seconds} hundredths {hundredths} direction {direction}",
        )

        lon = f"{degrees}{str(minutes)}.{hundredths}{direction}"
        return lon

    def get_latlon(self, latitude_str, longitude_str):
        return "{}/{}_".format(
            self.convert_latitude(float(latitude_str)),
            self.convert_longitude(float(longitude_str)),
        )

    def str_or_dots(self, number, length):
        # If parameter is None, fill with dots, otherwise pad with zero
        # if not number:
        #     retn_value = "." * length
        # else:
        format_type = {"int": "d", "float": ".0f"}[type(number).__name__]
        retn_value = "".join(("%0", str(length), format_type)) % number

        return retn_value

    def make_aprs_wx(self, wx_data):
        # LOG.debug(wx_data)
        wind_dir = float(wx_data.get("windDir", 0.00))
        wind_speed = float(wx_data.get("windSpeed_mph", 0.00))
        wind_gust = float(wx_data.get("windGust_mph", 0.00))
        temperature = float(wx_data.get("outTemp_F", 0.00))
        rain_last_hr = float(wx_data.get("hourRain_in", 0.00))
        rain_last_24_hrs = float(wx_data.get("rain24_in", 0.00))
        rain_since_midnight = float(wx_data.get("day_Rain_in", 0.00))
        humidity = float(wx_data.get("outHumidity", 0.00))
        # * 330.863886667
        pressure = float(wx_data.get("relbarometer", 0.00)) * 10
        LOG.info(f"wind_dir {wind_dir}")
        LOG.info(f"wind_speed {wind_speed}")
        LOG.info(f"wind_gust {wind_gust}")
        LOG.info(f"temperature {temperature}")
        LOG.info(f"rain_last_hr {rain_last_hr}")
        LOG.info(f"rain_last_24_hrs {rain_last_24_hrs}")
        LOG.info(f"rain_since_midnight {rain_since_midnight}")
        LOG.info(f"humidity {humidity}")
        LOG.info(f"pressure {pressure}")

        # Assemble the weather data of the APRS packet
        return "{}/{}g{}t{}r{}p{}P{}h{}b{}".format(
            self.str_or_dots(wind_dir, 3),
            self.str_or_dots(wind_speed, 3),
            self.str_or_dots(wind_gust, 3),
            self.str_or_dots(temperature, 3),
            self.str_or_dots(rain_last_hr, 3),
            self.str_or_dots(rain_last_24_hrs, 3),
            self.str_or_dots(rain_since_midnight, 3),
            self.str_or_dots(humidity, 2),
            self.str_or_dots(pressure, 5),
        )

    def build_packet(self, wx_data):
        utc_datetime = datetime.datetime.now()
        packet_data = "{}@{}z{}{}{}".format(
            self.address,
            utc_datetime.strftime("%d%H%M"),
            self.position,
            self.make_aprs_wx(wx_data),
            "APRSD",
        )

        return packet_data

    def loop(self):
        now = datetime.datetime.now()
        delta = now - self.last_send
        max_timeout = {"hours": 0.0, "minutes": 1, "seconds": 0}
        max_delta = datetime.timedelta(**max_timeout)
        if delta >= max_delta:
            if not self.wx_queue.empty():
                wx = self.wx_queue.get(timeout=1)
            else:
                try:
                    wx = self.wx_queue.get(timeout=5)
                except Exception:
                    time.sleep(1)
                    return True

            if not wx:
                # just keep looping
                time.sleep(1)
                return True

            # we have Weather now, so lets format the data
            # and then send it out to APRS
            raw_aprs_text = self.build_packet(wx)
            packet = aprsd.messaging.RawMessage(raw_aprs_text)
            LOG.debug(f"RAW WX Packet {packet}")
            packet.retry_count = 1
            packet.send()
            self.last_send = datetime.datetime.now()
            time.sleep(1)
            return True
        else:
            time.sleep(1)
            return True
