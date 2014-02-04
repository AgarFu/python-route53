from route53.xml_parsers.common_health_check import parse_health_check

def list_health_checks_parser(root, connection):
    """
    Parses the API responses for the
    :py:meth:`route53.connection.Route53Connection.list_health_checks` method.

    :param lxml.etree._Element root: The root node of the etree parsed
        response from the API.
    :param Route53Connection connection: The connection instance used to
        query the API.
    :rtype: HealthCheck
    :returns: A generator of fully formed HostedZone instances.
    """

    # The rest of the list pagination tags are handled higher up in the stack.
    # We'll just worry about the HostedZones tag, which has HostedZone tags
    # nested beneath it.
    health_checks = root.find('./{*}HealthChecks')

    for health_check in health_checks:
        yield parse_health_check(health_check, connection)
