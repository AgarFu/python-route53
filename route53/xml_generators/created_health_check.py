import uuid
from io import BytesIO
from lxml import etree

def create_health_check_writer(connection, caller_reference, ipaddress, port, type, resource_path, fqdn, search_string):
    """
    Forms an XML string that we'll send to Route53 in order to create
    a new hosted zone.

    :param Route53Connection connection: The connection instance used to
        query the API.
    :param str name: The name of the hosted zone to create.
    """

    if not caller_reference:
        caller_reference = str(uuid.uuid4())

    e_root = etree.Element(
        "CreateHealthCheckRequest",
        xmlns=connection._xml_namespace
    )

    e_caller_reference = etree.SubElement(e_root, "CallerReference")
    e_caller_reference.text = caller_reference

    e_config = etree.SubElement(e_root, "HealthCheckConfig")

    if ipaddress is not None:
        e_comment = etree.SubElement(e_config, "IPAddress")
        e_comment.text = ipaddress

    if port is not None:
        e_port= etree.SubElement(e_config, "Port")
        e_port.text = str(port)

    if type is not None:
        e_type = etree.SubElement(e_config, "Type")
        e_type.text = type

    if resource_path is not None:
        e_resource_path = etree.SubElement(e_config, "ResourcePath")
        e_resource_path.text = resource_path

    if fqdn is not None:
        e_fqdn = etree.SubElement(e_config, "FullyQualifiedDomainName")
        e_fqdn.text = fqdn

    if search_string is not None:
        e_search_string = etree.SubElement(e_config, "SearchString")
        e_search_string.text = search_string

    e_tree = etree.ElementTree(element=e_root)

    fobj = BytesIO()
    # This writes bytes.
    e_tree.write(fobj, xml_declaration=True, encoding='utf-8', method="xml")
    return fobj.getvalue().decode('utf-8')
