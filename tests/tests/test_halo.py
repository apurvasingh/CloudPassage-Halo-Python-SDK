import os
import imp
import pytest
import json
import datetime
import hashlib



module_path = os.path.abspath('../')
policy_path = os.path.abspath('./policies/')

file, filename, data = imp.find_module('cloudpassage', [module_path])
halo = imp.load_module('halo', file, filename, data)

# Temporary...
#get = imp.load_module('get', file, filename, data)

key_id = os.environ.get('HALO_KEY_ID')
secret_key = os.environ.get('HALO_SECRET_KEY')
ro_key_id = os.environ.get('RO_HALO_KEY_ID')
ro_secret_key = os.environ.get('RO_HALO_SECRET_KEY')
bad_key = "abad53c"
api_hostname = os.environ.get('HALO_API_HOSTNAME')
proxy_host = '190.109.164.81'
proxy_port = '1080'

# This will make cleaning up easier...
content_prefix = '_SDK_test-'

content_name = content_prefix + str(hashlib.md5(str(datetime.datetime.now())).hexdigest())

class TestHaloSession:
    def test_halosession_instantiation(self):
        session = halo.HaloSession(key_id, secret_key)
        assert session

    def test_halosession_useragent_override(self):
        ua_override = content_prefix
        session = halo.HaloSession(key_id, secret_key, user_agent=ua_override)
        session.authenticate_client()
        header = session.build_header()
        assert session.user_agent == ua_override
        assert header["User-Agent"] == ua_override

    def test_halosession_build_url_prefix(self):
        session = halo.HaloSession(key_id, secret_key)
        default_good = "https://api.cloudpassage.com:443"
        fn_out = session.build_url_prefix()
        assert fn_out == default_good

    def test_halosession_build_header(self):
        session = halo.HaloSession(key_id, secret_key)
        session.authenticate_client()
        header = session.build_header()
        assert "Authorization" in header
        assert header["Content-Type"] == "application/json"

    def test_halosession_with_proxy(self):
        session = halo.HaloSession(key_id, secret_key,
                            proxy_host=proxy_host,
                            proxy_port=proxy_port)
        assert ((session.proxy_host == proxy_host) and
                (session.proxy_port == proxy_port))

    def test_halosession_authentication(self):
        session = halo.HaloSession(key_id, secret_key)
        session.authenticate_client()
        assert ((session.auth_token is not None) and
                (session.auth_scope is not None))

    def test_halosession_throws_auth_exception(self):
        session = halo.HaloSession(bad_key, secret_key)
        authfailed = False
        try:
            session.authenticate_client()
        except halo.CloudPassageAuthentication:
            authfailed = True
        assert authfailed

    def test_halosession_get(self):
        url = "/v1/events"
        session = halo.HaloSession(key_id, secret_key)
        session.authenticate_client()
        get_json = session.get(url)
        assert "events" in get_json

    def test_halosession_get_404(self):
        url = "/v1/barf"
        pathfailed = False
        session = halo.HaloSession(key_id, secret_key)
        session.authenticate_client()
        try:
            get_json = session.get(url)
        except halo.CloudPassageResourceExistence:
            pathfailed = True
        assert pathfailed

    def test_halosession_get_renew_key(self):
        """We test key renewal by farting up the key and trying to GET"""
        url = "/v1/events"
        session = halo.HaloSession(key_id, secret_key)
        session.authenticate_client()
        session.auth_token = "fishandchips"
        get_json = session.get(url)
        assert "events" in get_json

    def test_halosession_get_set_key(self):
        """Test to make sure that we set key automatically"""
        url = "/v1/events"
        session = halo.HaloSession(key_id, secret_key)
        get_json = session.get(url)
        assert "events" in get_json

    def test_halosession_post_validation_exception(self):
        """We use strings that are too long for group creation"""
        rejected = False
        groupname = content_name
        url = "/v1/groups"
        reqbody = {"group": {
            "name": str(groupname + groupname),
                      "linux_firewall_policy_id": None,
                      "windows_firewall_policy_id": None,
                      "policy_ids": [],
                      "tag": str(groupname + groupname)}
                      }
        session = halo.HaloSession(key_id, secret_key)
        session.authenticate_client()
        try:
            resp = session.post(url, reqbody)
        except halo.CloudPassageValidation:
            rejected = True
        assert rejected

    def test_halosession_post_insufficient_scope(self):
        """We use read-only keys to attempt a POST"""
        rejected = False
        groupname = content_name
        url = "/v1/groups"
        reqbody = {"group": {
            "name": groupname[:20],
                      "linux_firewall_policy_id": None,
                      "windows_firewall_policy_id": None,
                      "policy_ids": [],
                      "tag": groupname[:20]}
                      }
        session = halo.HaloSession(ro_key_id, ro_secret_key)
        session.authenticate_client()
        try:
            resp = session.post(url, reqbody)
        except halo.CloudPassageAuthorization:
            rejected = True
        assert rejected

#Will re-enable as part of a test that cleans up after itself
#    def test_halosession_post_success(self):
#        groupname = content_name
#        url = "/v1/groups"
#        reqbody = {"group": {
#            "name": groupname[:20],
#                        "linux_firewall_policy_id": None,
#                        "windows_firewall_policy_id": None,
#                        "policy_ids": [],
#                        "tag": groupname[:20]}
#                    }
#        session = halo.HaloSession(key_id, secret_key)
#        session.authenticate_client()
#        resp = session.post(url, reqbody)
#        assert "group" in resp

    def test_halosession_put_validation_exception(self):
        """Field too big!!"""
        groupname = content_name[:21]
        rejected = False
        grouptag = content_name + content_name + content_name
        posturl = "/v1/groups"
        postbody = {"group": {
            "name": groupname,
            "linux_firewall_policy_id": None,
            "windows_firewall_policy_id": None,
            "policy_ids": [],
            "tag": groupname}
            }
        putbody = {"group": {"tag": grouptag}}
        session = halo.HaloSession(key_id, secret_key)
        session.authenticate_client()
        post_ret = session.post(posturl, postbody)
        grp_id = post_ret["group"]["id"]
        put_url = posturl + "/" + grp_id
        try:
            session.put(put_url, putbody)
        except halo.CloudPassageValidation:
            rejected = True
        assert rejected

    def test_halosession_put_insufficient_scope(self):
        """Looking for an authorization exception"""
        groupname = content_name[:22]
        rejected = False
        posturl = "/v1/groups"
        postbody = {"group": {
            "name": groupname,
            "linux_firewall_policy_id": None,
            "windows_firewall_policy_id": None,
            "policy_ids": [],
            "tag": groupname}
            }
        putbody = {"group": {"tag": "NEWTAG"}}
        session = halo.HaloSession(key_id, secret_key)
        session.authenticate_client()
        post_ret = session.post(posturl, postbody)
        grp_id = post_ret["group"]["id"]
        put_url = posturl + "/" + grp_id
        try:
            session = halo.HaloSession(ro_key_id, ro_secret_key)
            session.authenticate_client()
            session.put(put_url, putbody)
        except halo.CloudPassageAuthorization:
            rejected = True
        assert rejected


    def test_halosession_delete_insufficient_scope(self):
        """Looking for an authorization exception"""
        groupname = content_name[:23]
        rejected = False
        posturl = "/v1/groups"
        postbody = {"group": {
            "name": groupname,
            "linux_firewall_policy_id": None,
            "windows_firewall_policy_id": None,
            "policy_ids": [],
            "tag": groupname}
            }
        session = halo.HaloSession(key_id, secret_key)
        session.authenticate_client()
        post_ret = session.post(posturl, postbody)
        grp_id = post_ret["group"]["id"]
        del_url = posturl + "/" + grp_id
        try:
            session_ro = halo.HaloSession(ro_key_id, ro_secret_key)
            session_ro.authenticate_client()
            response = session_ro.delete(del_url)
            print session_ro.auth_scope
            print response
        except halo.CloudPassageAuthorization:
            rejected = True
        assert rejected

