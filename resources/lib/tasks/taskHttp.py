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

import http.client
import requests
import urllib.request, urllib.parse, urllib.error
from urllib.parse import urlparse
import socket
from resources.lib.taskABC import AbstractTask, KodiLogger, notify
from resources.lib.utils.poutil import KodiPo
kodipo = KodiPo()
_ = kodipo.getLocalizedString
__ = kodipo.getLocalizedStringId

class TaskHttp(AbstractTask):
    tasktype = 'http'
    variables = [
        {
            'id':'http',
            'settings':{
                'default':'',
                'label':'HTTP string (without parameters)',
                'type':'text'
            }
        },
        {
            'id':'user',
            'settings':{
                'default':'',
                'label':'user for Basic Auth (optional)',
                'type':'text'
            }
        },
        {
            'id':'pass',
            'settings':{
                'default':'',
                'label':'password for Basic Auth (optional)',
                'type':'text',
                'option':'hidden'
            }
        },
        {
            'id': 'request-type',
            'settings': {
                'default': 'GET',
                'label': 'Request Type',
                'type': 'labelenum',
                'values': ['GET', 'POST', 'POST-GET', 'PUT', 'DELETE', 'HEAD', 'OPTIONS']
            }
        },
        {
            'id': 'content-type',
            'settings': {
                'default': 'application/json',
                'label': 'Content-Type (for POST or PUT only)',
                'type': 'labelenum',
                'values': ['application/json', 'application/x-www-form-urlencoded', 'text/html', 'text/plain']
            }
        }
    ]

    def __init__(self):
        super(TaskHttp, self).__init__(name='TaskHttp')
        self.runtimeargs = ''

    @staticmethod
    def validate(taskKwargs, xlog=KodiLogger.log):
        o = urlparse(taskKwargs['http'])
        if o.scheme != '' and o.netloc != '':
            return True
        else:
            xlog(msg=_('Invalid url: %s') % taskKwargs['http'])
            return False

    def sendRequest(self, session, verb, url, postget=False):
        if (postget or verb == 'POST' or verb == 'PUT') and '??' in url:
            url, data = url.split('??', 1)
            try:
                data = data.encode('utf-8', 'replace')
            except UnicodeEncodeError:
                pass
            if postget:
                data = None
        else:
            data = None
        req = requests.Request(verb, url, data=data)
        try:
            prepped = session.prepare_request(req)
        except http.client.InvalidURL as e:
            err = True
            msg = str(e)
            return err, msg
        if verb == 'POST' or verb == 'PUT':
            prepped.headers['Content-Type'] = self.taskKwargs['content-type']
        try:
            pu = prepped.url.decode('utf-8')
        except (AttributeError, UnicodeDecodeError):
            pu = ''
        try:
            pb = prepped.body.decode('utf-8')
        except (AttributeError, UnicodeDecodeError):
            pb = ''
        msg = 'Prepped URL: %s\nBody: %s' % (pu, pb)
        try:
            resp = session.send(prepped, timeout=20)
            msg += '\nStatus: %s' % resp.status_code
            resp.raise_for_status()
            err = False
            if resp.text == '':
                respmsg = 'No response received'
            else:
                respmsg = resp.text
            msg += '\nResponse for %s: %s' %(verb, respmsg)
            resp.close()
        except requests.ConnectionError:
            err = True
            msg = _('Requests Connection Error')
        except requests.HTTPError as e:
            err = True
            msg = '%s: %s' %(_('Requests HTTPError'), str(e))
        except requests.URLRequired as e:
            err = True
            msg = '%s: %s' %(_('Requests URLRequired Error'), str(e))
        except requests.Timeout as e:
            err = True
            msg = '%s: %s' %(_('Requests Timeout Error'), str(e))
        except requests.RequestException as e:
            err = True
            msg = '%s: %s' %(_('Generic Requests Error'), str(e))
        except urllib.error.HTTPError as e:
            err = True
            msg = _('HTTPError\n') + str(e.code)
        except urllib.error.URLError as e:
            err = True
            msg = _('URLError\n') + str(e.reason)
        except http.client.BadStatusLine:
            err = False
            self.log(msg=_('Http Bad Status Line caught and passed'))
        except http.client.HTTPException as e:
            err = True
            msg = _('HTTPException\n') + str(e)
        except socket.timeout:
            err = True
            msg = _('The request timed out, host unreachable')
        except Exception as e:
            err = True
            msg = str(e)
        return err, msg


    def run(self):
        if self.taskKwargs['notify'] is True:
            notify(_('Task %s launching for event: %s') % (self.taskId, str(self.topic)))
        if isinstance(self.runtimeargs, list):
            if len(self.runtimeargs) > 0:
                self.runtimeargs = ''.join(self.runtimeargs)
            else:
                self.runtimeargs = ''
        s = requests.Session()
        url = self.taskKwargs['http']+self.runtimeargs
        if self.taskKwargs['user'] != '' and self.taskKwargs['pass'] != '':
            s.auth = (self.taskKwargs['user'], self.taskKwargs['pass'])
        if self.taskKwargs['request-type'] == 'POST-GET':
            verb = 'POST'
        else:
            verb = self.taskKwargs['request-type']

        err, msg = self.sendRequest(s, verb, url)

        if self.taskKwargs['request-type'] == 'POST-GET':
            err2, msg2 = self.sendRequest(s, 'GET', url, postget=True)
            err = err or err2
            msg = '\n'.join([msg, msg2])

        s.close()
        self.threadReturn(err, msg)
