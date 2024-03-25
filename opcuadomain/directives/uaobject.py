import typing
from typing import Any, Dict, List, Optional, Sequence, Tuple, TypeVar

from docutils import nodes
from docutils.nodes import definition_list, definition_list_item
from docutils.parsers.rst import directives
from docutils.parsers.rst.states import RSTState, RSTStateMachine
from docutils.statemachine import StringList

from sphinx.environment import BuildEnvironment
from sphinx.application import Sphinx

from sphinx import addnodes

#from sphinx.directives import ObjectDescription
from sphinx.util.docutils import SphinxDirective

from opcuadomain.defaults import OPCUA_DEFAULT_OPTIONS

from opcuadomain.uanode import add_uanode
from opcuadomain.utils import add_doc

from opcuadomain.logging import get_logger

logger = get_logger(__name__)

class UAObjectDirective(SphinxDirective):
    """A custom directive that describes a OPC-UA object."""

    has_content = False
    required_arguments = 1
    option_spec = OPCUA_DEFAULT_OPTIONS

    final_argument_whitespace = True

    def __init__(
        self,
        name: str,
        arguments: List[str],
        options: Dict[str, Any],
        content: StringList,
        lineno: int,
        content_offset: int,
        block_text: str,
        state: RSTState,
        state_machine: RSTStateMachine,
    ):
        super().__init__(name, arguments, options, content, lineno, content_offset, block_text, state, state_machine)
        self.log = get_logger(__name__)
        
    def run(self) -> Sequence[nodes.Node]:

        env = self.env

        opcua = self.env.get_domain('opcua')

        ua_node = opcua.find_uanode(self.arguments[0], "UAObject")

        if ua_node is None:
            raise ReferenceError(f"Could not find UAObject {self.arguments[0]}")
        
        hide = "hide" in self.options
        style = self.options.get("style")
        layout = self.options.get("layout", "")


        ua_nodes = add_uanode(
            env.app,
            self.state,
            ua_node,
            self.docname,
            self.lineno,
            hide=hide,
            style=style,
            layout=layout,
        )
        add_doc(env, self.docname)

        return ua_nodes
    
    @property
    def docname(self) -> str:
        return self.env.docname






