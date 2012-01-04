#
# core.py
#
# Copyright (C) 2009 Pradeep Jindal <praddyjindal@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

from deluge.log import LOG as log
from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export
from twisted.internet.task import LoopingCall

DEFAULT_PREFS = {
    "poll_interval": 60
}

class Core(CorePluginBase):
    def enable(self):
        self.config = deluge.configmanager.ConfigManager("randomize.conf", DEFAULT_PREFS)
        self.core_config = deluge.configmanager.ConfigManager("core.conf")
        self.enabled = False
        if not self.core_config["random_port"]:
            log.info("incoming port randomization is disabled in the core config, not doing anything")
            return 
        self.check_timer = LoopingCall(self.rand_if_firewalled)
        self.check_timer.start(int(self.config['poll_interval']))
        self.enabled = True


    def disable(self):
        self.config.save()
        if self.enable:
            self.check_timer.stop()

    def update(self):
        pass

    def rand_if_firewalled(self):
        core = component.get("Core")
        log.info("Current listen port: %d" % core.get_listen_port())
        def rand_port(is_open):
            firewalled = not is_open
            log.info("Its %s" % (firewalled and "firewalled, gonna try to change port" or "not firewalled"))
            if firewalled:
                core.set_config({"random_port": False})
                core.set_config({"random_port": True})
                log.info("Listen port changed to: %d" % core.get_listen_port())
                torrents = core.get_session_state()
                core.force_reannounce(torrents)
        core.test_listen_port().addCallback(rand_port)

    @export
    def set_config(self, config):
        """Sets the config dictionary"""
        changed = False
        if self.config != config:
            changed = True
        for key in config.keys():
            self.config[key] = config[key]
        if changed:
            # calling disable will also save the config
            self.disable()
            self.enable()

    @export
    def get_config(self):
        """Returns the config dictionary"""
        return self.config.config
