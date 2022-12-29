from oslo_config import cfg


weewx_group = cfg.OptGroup(
    name="aprsd_weewx_plugin",
    title="APRSD Weewx Plugin settings",
)

weewx_opts = [
    cfg.FloatOpt(
        "latitude",
        default=None,
        help="Latitude of the station you want to report as",
    ),
    cfg.FloatOpt(
        "longitude",
        default=None,
        help="Longitude of the station you want to report as",
    ),
    cfg.IntOpt(
        "report_interval",
        default=60,
        help="How long (in seconds) in between weather reports",
    ),
]

weewx_mqtt_opts = [
    cfg.StrOpt(
        "mqtt_user",
        help="MQTT username",
    ),
    cfg.StrOpt(
        "mqtt_password",
        secret=True,
        help="MQTT password",
    ),
    cfg.StrOpt(
        "mqtt_host",
        help="MQTT Hostname to connect to",
    ),
    cfg.PortOpt(
        "mqtt_port",
        help="MQTT Port",
    ),
]

ALL_OPTS = (
    weewx_opts +
    weewx_mqtt_opts
)


def register_opts(cfg):
    cfg.register_group(weewx_group)
    cfg.register_opts(ALL_OPTS, group=weewx_group)


def list_opts():
    register_opts(cfg.CONF)
    return {
        weewx_group.name: ALL_OPTS,
    }
