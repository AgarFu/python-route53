from route53.xml_parsers.common_change_info import parse_change_info
from route53.xml_parsers.common_health_check import parse_health_check
from lxml import etree

def created_health_check_parser(root, connection):
    """
    Parses the API responses for the
    :py:meth:`route53.connection.Route53Connection.create_health_check` method.

    :param lxml.etree._Element root: The root node of the etree parsed
        response from the API.
    :param Route53Connection connection: The connection instance used to
        query the API.
    :rtype: HostedZone
    :returns: The newly created HostedZone.
    """

    health_check_xml = root.find('./{*}HealthCheck')
    # This pops out a HostedZone instance.
    health_check = parse_health_check(health_check_xml, connection)

    return health_check
