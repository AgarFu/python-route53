import unittest
import route53
from route53.exceptions import AlreadyDeletedError
from route53.transport import BaseTransport
from tests.utils import get_route53_connection
import datetime
import os
from test_basic import BaseTestCase

try:
    from .credentials import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
except ImportError:
    AWS_ACCESS_KEY_ID = 'XXXXXXXXXXXXXXXXXXXX'
    AWS_SECRET_ACCESS_KEY = 'YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY'


class IntegrationBaseTestCase(BaseTestCase):
    """
    A base unit test class that has some generally useful stuff for the
    various test cases.
    """
    test_zone_name = 'route53-unittest-zone.com.'

    def __init__(self, *args, **kwargs):
        super(IntegrationBaseTestCase, self).__init__(*args, **kwargs)
        if ((AWS_ACCESS_KEY_ID == 'XXXXXXXXXXXXXXXXXXXX') or (AWS_SECRET_ACCESS_KEY == 'YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY')):
            self.skip = True
        else:
            self.skp = False

    def setUp(self):
        self.conn = get_route53_connection(**self.CONNECTION_OPTIONS)
        self.submittedAt = datetime.datetime.now()

    def tearDown(self):
        for zone in self.conn.list_hosted_zones():
            if zone.name == self.test_zone_ame:
                zone.delete(force=True)


class IntegrationHostedZoneTestCase(IntegrationBaseTestCase):
    """
    Tests for manipulating hosted zones.
    """

    def test_sequence(self):
        """
        Runs through a sequence of calls to test hosted zones.
        """
        if self.skip:
            self.SkipTest("There is no api credentials")

        # Create a new hosted zone.
        new_zone, change_info = self.conn.create_hosted_zone(
            self.test_zone_name, comment='A comment here.'
        )
        # Make sure the change info came through.
        self.assertIsInstance(change_info, dict)

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

        # Now attempt to retrieve the newly created HostedZone.
        zone = self.conn.get_hosted_zone_by_id(new_zone.id)
        # Its nameservers should be populated.
        self.assertNotEqual([], zone.nameservers)

        zone.delete()
        # Trying to delete a second time raises an exception.
        self.assertRaises(AlreadyDeletedError, zone.delete)
        # Attempting to add a record set to an already deleted zone does the same.
        self.assertRaises(AlreadyDeletedError,
            zone.create_a_record,
                'test.' + self.test_zone_name,
                ['8.8.8.8']
        )


class IntegrationResourceRecordSetTestCase(IntegrationBaseTestCase):
    """
    Tests related to RRSets. Deletions are tested in the cleanUp() method,
    on the base class, more or less.
    """

    def test_create_rrset(self):
        """
        Tests creation of various record sets.
        """
        if self.skip:
            self.SkipTest("There is no api credentials")

        new_zone, change_info = self.conn.create_hosted_zone(
            self.test_zone_name
        )
        self.assertIsInstance(change_info, dict)
        self.assertEqual(change_info['request_status'], 'INSYNC')
        self.assertEqual(change_info['request_submitted_at'].year, self.submittedAt.year)
        self.assertIsInstance(new_zone, route53.hosted_zone.HostedZone)

        new_record, change_info = new_zone.create_a_record(
            name='test.route53-unittest-zone.com.',
            values=['8.8.8.8'],
            ttl=40,
#            weight=10
        )
        self.assertIsInstance(change_info, dict)
        self.assertEqual(change_info['request_status'], 'PENDING')
        self.assertEqual(change_info['request_submitted_at'].year, self.submittedAt.year)
        self.assertIsInstance(new_record, route53.hosted_zone.AResourceRecordSet)

        # Initial values should equal current values.
        for key, val in new_record._initial_vals.items():
            self.assertEqual(getattr(new_record, key), val)

    def test_change_existing_rrset(self):
        """
        Tests changing an existing record set.
        """
        if self.skip:
            self.SkipTest("There is no api credentials")

        new_zone, change_info = self.conn.create_hosted_zone(
            self.test_zone_name
        )

        new_record, change_info = new_zone.create_a_record(
            name='test.route53-unittest-zone.com.',
            values=['8.8.8.8'],
        )
        self.assertIsInstance(change_info, dict)
        self.assertEqual(change_info['request_status'], 'PENDING')
        self.assertEqual(change_info['request_submitted_at'].year, self.submittedAt.year)
        self.assertIsInstance(new_record, route53.hosted_zone.AResourceRecordSet)

        new_record.values = ['8.8.8.7']
        new_record.save()

        # Initial values should equal current values after the save.
        for key, val in new_record._initial_vals.items():
            self.assertEqual(getattr(new_record, key), val)
