# -*-  coding: utf-8 -*-
"""
We created a Falcon based WSGI server.
Integrated session support with beaker.
Then route all requests to workflow engine.

We process request and response objects for json data in middleware layer,
so activity methods (which will be invoked from workflow engine)
can read json data from request.context.jsonin
and writeback to request.context.jsonout

"""
# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from wsgiref import simple_server

from zengine.engine import ZEngine
from ulakbus import settings
from ulakbus.zdispatch.dispatcher import app, falcon_app

__author__ = 'Evren Esat Ozkan'


class WFEngine(ZEngine):

    WORKFLOW_DIRECTORY = settings.WORKFLOW_PACKAGES_PATH,
    ACTIVITY_MODULES_PATH = settings.ACTIVITY_MODULES_IMPORT_PATH

    def save_workflow(self, wf_name, serialized_wf_instance):
        if 'workflows' not in self.current.request.session:
            self.current.request.session['workflows'] = {}
        self.current.request.session['workflows'][wf_name] = serialized_wf_instance
        self.current.request.session.save()

    def load_workflow(self, workflow_name):
        try:
            return self.current.request.session['workflows'].get(workflow_name, None)
        except KeyError:
            return None


class Connector(object):
    """
    this is a callable object to catch all requests and map them to workflow engine.
    domain.com/show_dashboard/blah/blah/x=2&y=1 will invoke a workflow named show_dashboard
    """
    # def __init__(self):
    # self.logger = logging.getLogger('dispatch.' + __name__)
    def __init__(self):
        self.engine = WFEngine()

    def __call__(self, req, resp, wf_name):
        self.engine.set_current(request=req, response=resp, workflow_name=wf_name)
        self.engine.load_or_create_workflow()
        self.engine.run()

    def on_post(self, req, resp, wf_name):
        self.engine.set_current(request=req, response=resp, workflow_name=wf_name)
        self.engine.load_or_create_workflow()
        self.engine.run()



workflow_connector = Connector()
falcon_app.add_route('/{wf_name}/', workflow_connector)


# Useful for debugging problems in your API; works with pdb.set_trace()
if __name__ == '__main__':
    httpd = simple_server.make_server('127.0.0.1', 8000, app)
    httpd.serve_forever()
