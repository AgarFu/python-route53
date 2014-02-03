import unittest
import route53
from route53.exceptions import AlreadyDeletedError
from route53.transport import BaseTransport
from tests.utils import get_route53_connection
import datetime
import os


class BaseTestCase(unittest.TestCase):
    """
    A base unit test class that has some generally useful stuff for the
    various test cases.
    """
    CONNECTION_OPTIONS = {}

    test_zone_name = 'route53-unittest-zone.com.'

    def setUp(self):
        self.conn = get_route53_connection(**self.CONNECTION_OPTIONS)
        self.submittedAt = datetime.datetime.now()

class DummyTransport(route53.transport.BaseTransport):
    def __init__(self, *args, **kwargs):
        super(DummyTransport, self).__init__(*args, **kwargs)
        self.response = []

    def set_response(self, response):
        self.response.append(response)

    def set_response_from_file(self, response_file, **kwargs):
        response_path = os.path.join(os.path.dirname(__file__), 'responses', response_file)
        self.response.append(open(response_path, 'r').read() % kwargs)

    def _send_get_request(self, path, params, headers):
        #print "\n-- GET Method --\n - path: %s\n - params: %s\n - headers: %s" % (path, params, headers)
        return self.response.pop(0)

    def _send_post_request(self, path, params, headers):
        #print "\n-- POST Method --\n - path: %s\n - params: %s\n - headers: %s" % (path, params, headers)
        return self.response.pop(0)

    def _send_delete_request(self, path, headers):
        #print "\n-- DELETE Method --\n - path: %s\n - headers: %s" % (path, headers)
        return self.response.pop(0)


class BaseTransportTestCase(unittest.TestCase):
    """
    Tests for the various HTTP transports.
    """

    def test_hmac_signing(self):
        """
        Makes sure our HMAC signing methods are matching expected output
        for a pre-determined key/value.
        """

        conn = route53.connect(
            aws_access_key_id='BLAHBLAH',
            aws_secret_access_key='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
        )
        trans = BaseTransport(conn)
        signed = trans._hmac_sign_string('Thu, 14 Aug 2008 17:08:48 GMT')
        self.assertEquals(signed, 'PjAJ6buiV6l4WyzmmuwtKE59NJXVg5Dr3Sn4PCMZ0Yk=')


class HostedZoneTestCase(BaseTestCase):
    """
    Tests for manipulating hosted zones.
    """
    CONNECTION_OPTIONS = {'transport_class':DummyTransport}

    def test_sequence(self):
        """
        Runs through a sequence of calls to test hosted zones.
       """

        self.conn._transport.set_response_from_file('CreateHostedZoneResponse.xml', SubmittedAt=self.submittedAt.strftime('%Y-%m-%dT%H:%M:%SZ'))
        # Create a new hosted zone.
        new_zone, change_info = self.conn.create_hosted_zone(
            self.test_zone_name, comment='A comment here.'
        )
        # Make sure the change info came through.
        self.assertIsInstance(change_info, dict)

        self.conn._transport.set_response_from_file('ListHostedZonesResponse.xml')
        self.conn._transport.set_response_from_file('GetHostedZoneResponse.xml')
        # Now get a list of all zones. Look for the one we just created.
        found_match = False
        for zone in self.conn.list_hosted_zones():
            if zone.name == new_zone.name:
                found_match = True

                # ListHostedZones doesn't return nameservers.
                # We lazy load them in this case. Initially, the nameservers
                # are empty.
                self.assertEqual(zone._nameservers, [])
                # This should return the nameservers
                self.assertNotEqual(zone.nameservers, [])
                # This should now be populated.
                self.assertNotEqual(zone._nameservers, [])

                break
        # If a match wasn't found, we're not happy.
        self.assertTrue(found_match)

        self.conn._transport.set_response_from_file('GetHostedZoneResponse.xml')
        # Now attempt to retrieve the newly created HostedZone.
        zone = self.conn.get_hosted_zone_by_id(new_zone.id)
        # Its nameservers should be populated.
        self.assertNotEqual([], zone.nameservers)

        self.conn._transport.set_response_from_file('DeleteHostedZoneResponse.xml', SubmittedAt=self.submittedAt.strftime('%Y-%m-%dT%H:%M:%SZ'))
        zone.delete()
        # Trying to delete a second time raises an exception.
        self.assertRaises(AlreadyDeletedError, zone.delete)
        # Attempting to add a record set to an already deleted zone does the same.
        self.assertRaises(AlreadyDeletedError,
            zone.create_a_record,
                'test.' + self.test_zone_name,
                ['8.8.8.8']
        )


class ResourceRecordSetTestCase(BaseTestCase):
    """
    Tests related to RRSets. Deletions are tested in the cleanUp() method,
    on the base class, more or less.
    """
    CONNECTION_OPTIONS = {'transport_class':DummyTransport}

    def test_create_rrset(self):
        """
        Tests creation of various record sets.
        """

        self.conn._transport.set_response_from_file('CreateHostedZoneResponse.xml', SubmittedAt=self.submittedAt.strftime('%Y-%m-%dT%H:%M:%SZ'))
        new_zone, change_info = self.conn.create_hosted_zone(
            self.test_zone_name
        )
        self.assertIsInstance(change_info, dict)
        self.assertEqual(change_info['request_status'], 'INSYNC')
        self.assertEqual(change_info['request_submitted_at'].year, self.submittedAt.year)
        self.assertEqual(change_info['request_id'], '/change/unique identifier for the change batch request')
        self.assertIsInstance(new_zone, route53.hosted_zone.HostedZone)

        self.conn._transport.set_response_from_file('GetChangeResponse.xml', SubmittedAt=self.submittedAt.strftime('%Y-%m-%dT%H:%M:%SZ'))
        new_record, change_info = new_zone.create_a_record(
            name='test.route53-unittest-zone.com.',
            values=['8.8.8.8'],
            ttl=40,
#            weight=10
        )
        self.assertIsInstance(change_info, dict)
        self.assertEqual(change_info['request_status'], 'PENDING')
        self.assertEqual(change_info['request_submitted_at'].year, self.submittedAt.year)
        self.assertEqual(change_info['request_id'], 'unique identifier for the change batch request')
        self.assertIsInstance(new_record, route53.hosted_zone.AResourceRecordSet)

        # Initial values should equal current values.
        for key, val in new_record._initial_vals.items():
            self.assertEqual(getattr(new_record, key), val)

    def test_change_existing_rrset(self):
        """
        Tests changing an existing record set.
        """

        self.conn._transport.set_response_from_file('CreateHostedZoneResponse.xml', SubmittedAt = self.submittedAt.strftime('%Y-%m-%dT%H:%M:%SZ'))
        new_zone, change_info = self.conn.create_hosted_zone(
            self.test_zone_name
        )

        self.conn._transport.set_response_from_file('GetChangeResponse.xml', SubmittedAt = self.submittedAt.strftime('%Y-%m-%dT%H:%M:%SZ'))
        new_record, change_info = new_zone.create_a_record(
            name='test.route53-unittest-zone.com.',
            values=['8.8.8.8'],
        )
        self.assertIsInstance(change_info, dict)
        self.assertEqual(change_info['request_status'], 'PENDING')
        self.assertEqual(change_info['request_submitted_at'].year, self.submittedAt.year)
        self.assertEqual(change_info['request_id'], 'unique identifier for the change batch request')
        self.assertIsInstance(new_record, route53.hosted_zone.AResourceRecordSet)

        new_record.values = ['8.8.8.7']
        self.conn._transport.set_response_from_file('GetChangeResponse.xml', SubmittedAt = self.submittedAt.strftime('%Y-%m-%dT%H:%M:%SZ'))
        new_record.save()

        # Initial values should equal current values after the save.
        for key, val in new_record._initial_vals.items():
            self.assertEqual(getattr(new_record, key), val)


class HealthTestTestCase(BaseTestCase):
    """
    Tests for manipulating health check.
    """
    CONNECTION_OPTIONS = {'transport_class':DummyTransport}

    def test_list_health_checks(self):
        self.conn._transport.set_response_from_file('ListHealthChecksResponse.xml')
        for health_check in self.conn.list_health_checks():
            self.assertEqual(health_check.id, 'Test Health Check ID')

    def test_create_health_check(self):
        self.conn._transport.set_response_from_file('CreateHealthCheckResponse.xml')
        # Create a new health check.
        ipaddress = '1.2.3.4'
        port = 80
        type = 'HTTP'
        resource_path = '/health_check'
        fqdn = 'www.tuguu.com'
        search_string = 'alive'
        new_health_check = self.conn.create_health_check(
            ipaddress, port, type, resource_path, fqdn, search_string
        )
        self.assertIsInstance(new_health_check, route53.health_check.HealthCheck)

    def test_get_health_check(self):
        self.conn._transport.set_response_from_file('GetHealthCheckResponse.xml')
        health_check_id = 'Test Health Check'
        new_health_check = self.conn.get_health_check_by_id(health_check_id)
        self.assertEqual(new_health_check.id, health_check_id)
        self.assertIsInstance(new_health_check, route53.health_check.HealthCheck)

    def test_delete_health_check(self):
        self.conn._transport.set_response_from_file('GetHealthCheckResponse.xml')
        self.conn._transport.set_response_from_file('DeleteHealthCheckResponse.xml', SubmittedAt = self.submittedAt.strftime('%Y-%m-%dT%H:%M:%SZ'))
        health_check_id = 'Test Health Check'
        new_health_check = self.conn.get_health_check_by_id(health_check_id)
        self.assertEqual(new_health_check.id, health_check_id)
        self.assertIsInstance(new_health_check, route53.health_check.HealthCheck)
        new_health_check.delete()
        self.assertRaises(AlreadyDeletedError, new_health_check.delete)
