from route53.xml_parsers.common_health_check import parse_health_check

def get_health_check_by_id_parser(root, connection):
    """
    Parses the API responses for the
    :py:meth:`route53.connection.Route53Connection.get_health_check_by_id` method.

    :param lxml.etree._Element root: The root node of the etree parsed
        response from the API.
    :param Route53Connection connection: The connection instance used to
        query the API.
    :rtype: HealthCheck
    :returns: The requested HealthCheck.
    """

    e_zone = root.find('./{*}HealthCheck')
    # This pops out a HealthCheck instance.
    health_check =  parse_health_check(e_zone, connection)
    return health_check
