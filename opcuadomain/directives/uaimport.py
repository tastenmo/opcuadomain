import os

from typing import Sequence, cast
from urllib.parse import urlparse

from asyncua import ua
#from opcua.common.xmlimporter import XmlImporter
from asyncua.common.xmlparser import XMLParser, NodeData, Field

from docutils import nodes
from docutils.parsers.rst import Directive, directives

from sphinx.environment import BuildEnvironment

from opcuadomain.logging import get_logger

logger = get_logger(__name__)


class UAImportDirective(Directive):
    has_content = False

    required_arguments = 1
    optional_arguments = 0

    option_spec = {}

    final_argument_whitespace = False

    def run(self) -> Sequence[nodes.Node]:

        opcua_import_path = self.arguments[0]

        ua_nodes = []

        # check if given arguemnt is a url to a opc server
        url = urlparse(opcua_import_path)
        if url.scheme and url.netloc:
            logger.info(f"Browse nodeset from {opcua_import_path}." )

            raise NotImplementedError(f"Browsing a opc-server is not implemented yet. {opcua_import_path}")

        else:
            logger.info(f"Import nodeset from {opcua_import_path}." )

            if not os.path.isabs(opcua_import_path):
                curr_dir = os.path.dirname(self.docname)
                abs_opcua_import_path = os.path.join(self.env.app.srcdir, curr_dir, opcua_import_path)
            else:
                abs_opcua_import_path = os.path.join(self.env.app.srcdir, opcua_import_path[1:])

            if not os.path.exists(abs_opcua_import_path):
                raise ReferenceError(f"Could not load nodeset file {abs_opcua_import_path}")
            
            parser = XMLParser()

            parser.parse_sync(abs_opcua_import_path)


            opcua = self.env.get_domain('opcua')

            ua_namespaces = parser.get_used_namespaces()
            
            #for ns in ua_namespaces:
            #    opcua.add_namespace(ns)
            
            ua_aliases = parser.get_aliases()

            ua_nodes = parser.get_node_datas()

            opcua.data['UANodes'] = ua_nodes
            opcua.data['UAAliases'] = ua_aliases
            opcua.data['UANamespaces'] = ua_namespaces
            
        return []
    
    @property
    def env(self) -> BuildEnvironment:
        return cast(BuildEnvironment, self.state.document.settings.env)

    @property
    def docname(self) -> str:
        return self.env.docname
    





