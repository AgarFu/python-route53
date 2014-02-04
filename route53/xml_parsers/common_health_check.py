"""
Contains a parser for HealthChecks tags. These are used in several kinds of
XML responses (ListHostedZones and CreateHostedZone, for example).
"""

from route53.health_check import HealthCheck

# This dict maps tag names in the API response to a kwarg key used to
# instantiate HostedZone instances.
HEALTH_CHECK_TAG_TO_KWARG_MAP = {
    'Id': 'id',
    'Name': 'name',
    'CallerReference': 'caller_reference',
}

def parse_health_check(e_healthcheck, connection):
    """
    This a common parser that allows the passing of any valid HostedZone
    tag. It will spit out the appropriate HostedZone object for the tag.

    :param lxml.etree._Element e_zone: The root node of the etree parsed
        response from the API.
    :param Route53Connection connection: The connection instance used to
        query the API.
    :rtype: HostedZone
    :returns: An instantiated HostedZone object.
    """

    # This dict will be used to instantiate a HostedZone instance to yield.
    kwargs = {}
    # Within HostedZone tags are a number of sub-tags that include info
    # about the instance.
    for e_field in e_healthcheck:
        # Cheesy way to strip off the namespace.
        tag_name = e_field.tag.split('}')[1]
        field_text = e_field.text

        if tag_name == 'HealthCheckConfig':
            # HealthCheckConfig has the IPAddress, Port, Type, ResourcePath,
            # FullyQualifiedDomainName, SearchString tag beneath it, needing
            # special handling.
            e_ipaddress = e_field.find('./{*}IPAddress')
            kwargs['ipaddress'] = e_ipaddress.text if e_ipaddress is not None else None

            e_port = e_field.find('./{*}Port')
            kwargs['port'] = e_port.text if e_port is not None else None

            e_type = e_field.find('./{*}Type')
            kwargs['type'] = e_type.text if e_type is not None else None

            e_resource_path = e_field.find('./{*}ResourcePath')
            kwargs['resource_path'] = e_resource_path.text if e_resource_path is not None else None

            e_fqdn = e_field.find('./{*}FullyQualifiedDomainName')
            kwargs['fqdn'] = e_fqdn.text if e_fqdn is not None else None

            e_search_string = e_field.find('./{*}SearchString')
            kwargs['search_string'] = e_search_string.text if e_search_string is not None else None
            continue
        elif tag_name == 'Id':
            # This comes back with a path prepended. Yank that sillyness.
            field_text = field_text

        # Map the XML tag name to a kwarg name.
        kw_name = HEALTH_CHECK_TAG_TO_KWARG_MAP[tag_name]
        # This will be the key/val pair used to instantiate the
        # HostedZone instance.
        kwargs[kw_name] = field_text

    return HealthCheck(connection, **kwargs)

