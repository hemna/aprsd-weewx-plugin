from oslo_config import cfg

from aprsd_weewx_plugin.conf import weewx


CONF = cfg.CONF
weewx.register_opts(CONF)
