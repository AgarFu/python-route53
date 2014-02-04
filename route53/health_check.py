from route53.change_set import ChangeSet
from route53.exceptions import AlreadyDeletedError

class HealthCheck(object):
    """
    A health check is a mecanism implemented by Route 53 to check if a host is
    alive.

    .. warning:: Do not instantiate this directly yourself. Go through
        one of the methods on :py:class:`route53.connection.Route53Connection`.
    """

    def __init__(self, connection, id, caller_reference, ipaddress, port, type, resource_path, fqdn, search_string=None):
        """
        :param Route53Connection connection: The connection instance that
            was used to query the Route53 API, leading to this object's
            creation.
        :param str id: Route53's unique ID for this health check.
        :param str name: The name of the domain.
        :param str caller_reference: A unique string that identifies the
            request to create the hosted zone.
        :param int resource_record_set_count: The number of resource record
            sets in the hosted zone.
        """

        self.connection = connection
        self.id = id
        self.caller_reference = caller_reference
        self.ipaddress = ipaddress
        self.port = int(port)
        self.type = type
        self.resource_path = resource_path
        self.fqdn = fqdn
        self.search_string = search_string

        # This is set to True when this HealthCheck has been deleted in Route53.
        self._is_deleted = False

    def __str__(self):
        return '<HealthCheck: %s -- %s>' % (self.ipaddress, self.id)

    def _halt_if_already_deleted(self):
        """
        Convenience method used to raise an AlreadyDeletedError exception if
        this HealthCheck has been deleted.

        :raises: AlreadyDeletedError
        """

        if self._is_deleted:
            raise AlreadyDeletedError("Can't manipulate a deleted health check.")

    def delete(self, force=False):
        """
        Deletes this hosted zone. After this method is ran, you won't be able
        to add records, or do anything else with the zone. You'd need to
        re-create it, as zones are read-only after creation.

        :keyword bool force: If ``True``, delete the
            :py:class:`HostedZone <route53.hosted_zone.HostedZone>`, even if it
            means nuking all associated record sets. If ``False``, an
            exception is raised if this
            :py:class:`HostedZone <route53.hosted_zone.HostedZone>`
            has record sets.
        :rtype: dict
        :returns: A dict of change info, which contains some details about
            the request.
        """

        self._halt_if_already_deleted()

#        if force:
#            # Forcing deletion by cleaning up all record sets first. We'll
#            # do it all in one change set.
#            cset = ChangeSet(connection=self.connection, hosted_zone_id=self.id)
#
#            for rrset in self.record_sets:
#                # You can delete a HostedZone if there are only SOA and NS
#                # entries left. So delete everything but SOA/NS entries.
#                if rrset.rrset_type not in ['SOA', 'NS']:
#                    cset.add_change('DELETE', rrset)
#
#            if cset.deletions or cset.creations:
#                # Bombs away.
#                self.connection._change_resource_record_sets(cset)

        # Now delete the HostedZone.
        retval = self.connection.delete_health_check_by_id(self.id)

        # Used to protect against modifying a deleted HostedZone.
        self._is_deleted = True

        return retval
