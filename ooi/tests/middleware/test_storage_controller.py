# -*- coding: utf-8 -*-

# Copyright 2015 Spanish National Research Council
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import uuid

import mock

from ooi.tests import fakes
from ooi.tests.middleware import test_middleware


def build_occi_volume(vol):
    name = vol["displayName"]
    vol_id = vol["id"]
    size = vol["size"]
    # TODO(enolfc): use proper status!
    status = "online"

    cats = []
    cats.append('storage; '
                'scheme="http://schemas.ogf.org/occi/infrastructure"; '
                'class="kind"'),
    attrs = [
        'occi.core.title="%s"' % name,
        'occi.storage.size=%s' % size,
        'occi.storage.state="%s"' % status,
        'occi.core.id="%s"' % vol_id,
    ]
    links = []
    links.append('<%s?action=backup>; rel=http://schemas.ogf.org/occi/'
                 'infrastructure/storage/action#backup' % vol_id)
    links.append('<%s?action=resize>; rel=http://schemas.ogf.org/occi/'
                 'infrastructure/storage/action#resize' % vol_id)
    links.append('<%s?action=snapshot>; rel=http://schemas.ogf.org/occi/'
                 'infrastructure/storage/action#snapshot' % vol_id)
    links.append('<%s?action=offline>; rel=http://schemas.ogf.org/occi/'
                 'infrastructure/storage/action#offline' % vol_id)
    links.append('<%s?action=online>; rel=http://schemas.ogf.org/occi/'
                 'infrastructure/storage/action#online' % vol_id)

    result = []
    for c in cats:
        result.append(("Category", c))
    for l in links:
        result.append(("Link", l))
    for a in attrs:
        result.append(("X-OCCI-Attribute", a))
    return result


class TestStorageController(test_middleware.TestMiddleware):
    """Test OCCI storage controller."""

    def test_list_vols_empty(self):
        tenant = fakes.tenants["bar"]
        app = self.get_app()

        req = self._build_req("/storage", tenant["id"], method="GET")

        m = mock.MagicMock()
        m.user.project_id = tenant["id"]
        req.environ["keystone.token_auth"] = m

        resp = req.get_response(app)

        self.assertEqual("/%s/os-volumes" % tenant["id"], req.path_info)

        expected_result = ""
        self.assertContentType(resp)
        self.assertExpectedResult(expected_result, resp)
        self.assertEqual(200, resp.status_code)

    def test_list_vols(self):
        tenant = fakes.tenants["foo"]
        app = self.get_app()

        req = self._build_req("/storage", tenant["id"], method="GET")

        resp = req.get_response(app)

        self.assertEqual("/%s/os-volumes" % tenant["id"], req.path_info)

        self.assertEqual(200, resp.status_code)
        expected = []
        for s in fakes.volumes[tenant["id"]]:
            expected.append(("X-OCCI-Location", "/storage/%s" % s["id"]))
        self.assertExpectedResult(expected, resp)

    def test_show_vol(self):
        tenant = fakes.tenants["foo"]
        app = self.get_app()

        for volume in fakes.volumes[tenant["id"]]:
            req = self._build_req("/storage/%s" % volume["id"],
                                  tenant["id"], method="GET")

            resp = req.get_response(app)
            expected = build_occi_volume(volume)
            self.assertContentType(resp)
            self.assertExpectedResult(expected, resp)
            self.assertEqual(200, resp.status_code)

    def test_vol_not_found(self):
        tenant = fakes.tenants["foo"]

        app = self.get_app()
        req = self._build_req("/storage/%s" % uuid.uuid4().hex,
                              tenant["id"], method="GET")
        resp = req.get_response(app)
        self.assertEqual(404, resp.status_code)


class StorageControllerTextPlain(test_middleware.TestMiddlewareTextPlain,
                                 TestStorageController):
    """Test OCCI compute controller with Accept: text/plain."""


class StorageControllerTextOcci(test_middleware.TestMiddlewareTextOcci,
                                TestStorageController):
    """Test OCCI compute controller with Accept: text/occi."""