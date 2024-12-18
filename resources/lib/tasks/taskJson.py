#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2014 KenV99
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import sys
import traceback
import xbmc
import json
from resources.lib.taskABC import AbstractTask, KodiLogger, notify
from resources.lib.utils.poutil import KodiPo
kodipo = KodiPo()
_ = kodipo.getLocalizedString
__ = kodipo.getLocalizedStringId

class TaskJsonNotify(AbstractTask):
    tasktype = 'json_rpc_notify'
    variables = [
        {
            'id':'jsonnotify',
            'settings':{
                'default':'kodi.callbacks',
                'label':'Sender string',
                'type':'text'
            }
        },
    ]

    def __init__(self):
        super(TaskJsonNotify, self).__init__(name='TaskJson')

    @staticmethod
    def validate(taskKwargs, xlog=KodiLogger.log):
        return True

    def run(self):
        if self.taskKwargs['notify'] is True:
            notify(_('Task %s launching for event: %s') % (self.taskId, str(self.topic)))
        err = False
        msg = ''
        message = str(self.topic)
        data = json.dumps(self.publisherKwargs)
        try:
            qs = '{ "jsonrpc": "2.0", "id": 0, "method": "JSONRPC.NotifyAll", "params": {"sender":"%s", "message":"%s", "data":%s} }' %(self.taskKwargs['jsonnotify'], message, data)
            qs = qs.encode('utf-8', 'ignore')
            json_query = xbmc.executeJSONRPC(qs)
            json_query = str(json_query, 'utf-8', 'ignore')
            json_response = json.loads(json_query)
        except Exception as e:
            err = True
            msg = str(e)
        else:
            if 'result' in json_response:
                if json_response['result'] != 'OK':
                    err = True
                    msg = 'JSON Notify Error %s' % json_response['result']
            else:
                err = True
                msg = 'JSON Notify Error: %s' % str(json_response)

        self.threadReturn(err, msg)
