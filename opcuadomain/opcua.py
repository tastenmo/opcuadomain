from typing import Any, Dict, List

import re

from sphinx.application import Sphinx

from sphinx.domains import Domain, Index
from sphinx.roles import XRefRole
from sphinx.util.nodes import make_refnode
from sphinx.environment import BuildEnvironment

from opcuadomain.logging import get_logger

from opcuadomain.defaults import LAYOUTS


from directives.uaimport import UAImportDirective
from opcuadomain.directives.uanode import UANodeDirective

from directives.uavariable import UAVariableDirective
from directives.uaobject import UAObjectDirective

from indices.uavariablesindex import UAVariableIndex
from indices.uareferencesindex import UAReferenceIndex

from asyncua.ua.object_ids import ObjectIds, ObjectIdNames

from uanode import process_ua_nodes

class OpcuaDomain(Domain):

    name = 'opcua'
    label = 'OPC UA Sample'

    roles = {
        'ref': XRefRole(),
    }
    directives = {
        'uanode': UANodeDirective,
        'uaimport': UAImportDirective,

    }
    #indices = {
    #    UANodeIndex,
    #}
    initial_data = {
        'UANamespaces': [],  # name -> object
        'UAAliases': [],  # object list
        'UANodes': [],  # name -> object
    }

    def get_full_qualified_name(self, node):
        return f'UAVariable.{node.arguments[0]}'

    def get_objects(self):
        for uanode in self.data['UANodes']:
            yield (uanode.browsename, uanode.displayname, uanode.nodetype, "", uanode.nodeid, 0)

    def resolve_xref(self, env, fromdocname, builder, typ, target, node,
                     contnode):
        match = [(docname, anchor)
                 for name, sig, typ, docname, anchor, prio
                 in self.get_objects() if sig == target]

        if len(match) > 0:
            todocname = match[0][0]
            targ = match[0][1]

            return make_refnode(builder, fromdocname, todocname, targ,
                                contnode, targ)
        else:
            print('Awww, found nothing')
            return None
        
    def add_uavariable(self, signature, ingredients):
        """Add a new UAVariable to the domain."""
        name = f'UAVariable.{signature}'
        anchor = f'UAVariable-{signature}'

        #self.data['recipe_ingredients'][name] = ingredients
        # name, dispname, type, docname, anchor, priority
        self.data['UAVariables'].append(
            (name, signature, 'UAVariable', self.env.docname, anchor, 0))
        
    #def add_namespace(self, namespace):
    def find_uavariable(self, browse_name):
        """Find a UAVariable by name."""
        for uanode in self.data['UANodes']:
            if uanode.browsename == browse_name and uanode.nodetype == 'UAVariable':
                return uanode
        return None
    
    def get_uavariable(self, node_id):
        """Find a UAVariable by id."""
        for uanode in self.data['UANodes']:
            if uanode.nodeid == node_id and uanode.nodetype == 'UAVariable':
                return uanode
        return None
    
    def find_uanode_by_name(self, browse_name, node_type):
        """Find a UANode by browsename."""
        for uanode in self.data['UANodes']:
            if uanode.browsename == browse_name and uanode.nodetype == node_type:
                return uanode
        return None
    
    def find_uanode_by_id(self, node_id):
        """Find a UANode by browsename."""
        for uanode in self.data['UANodes']:
            if uanode.nodeid == node_id:
                return uanode
        return None
    
    def find_child_nodes(self, parent_id):
        result = []
        """Find a UANode by browsename."""
        for uanode in self.data['UANodes']:
            if uanode.parent == parent_id:
                result.append(uanode)
        return result
    
    def get_target_name(self, target):
        m = re.match(r'i=(\d+)', target)

        if m:
            if int(m.group(1)) in ObjectIdNames:
                return ObjectIdNames[int(m.group(1))]
            
        for alias in self.data['UAAliases']:
            if self.data['UAAliases'][alias] == target:
                return alias
            
        node = self.find_uanode_by_id(target)
        if node:
            return node.browsename
        
        return target



    


def setup(app):
    log = get_logger(__name__)
    log.info("Starting setup of OPC-UA-Domain")
    #log.debug("Load Sphinx-Data-Viewer for Sphinx-Needs")

    app.add_config_value("needs_extra_links", [], "html")
    app.add_config_value("needs_string_links", {}, "html")


    app.add_domain(OpcuaDomain)

    app.connect("env-before-read-docs", prepare_env)

    app.connect("doctree-resolved", process_ua_nodes)

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }

def prepare_env(app: Sphinx, env: BuildEnvironment, _docname: str) -> None:
    
    if not hasattr(env, "needs_all_docs"):
        # Used to store all docnames, which have need-function in it and therefor
        # need to be handled later
        env.needs_all_docs = {"all": []}

    app.config.needs_layouts = {**LAYOUTS}