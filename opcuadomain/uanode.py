import hashlib
import os
import re
from typing import Any, List, Optional, Union

from docutils import nodes

from docutils.parsers.rst.states import RSTState
from docutils.statemachine import StringList
from jinja2 import Template
from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment
from sphinx.util.nodes import nested_parse_with_titles

from asyncua.common.xmlparser import NodeData
from asyncua.ua.object_ids import ObjectIds

from opcuadomain.nodes import uanodes

from opcuadomain.layout import build_need

from opcuadomain.logging import get_logger
from opcuadomain.utils import unwrap

logger = get_logger(__name__)

class UAPart(nodes.Inline, nodes.Element):
    pass

def add_uanode(
    app: Sphinx,
    state,
    data: NodeData,
    docname: str,
    lineno: int,
    content: str = "",
    status: str | None = None,
    tags: None | str | list[str] = None,
    hide: bool = False,
    style: None | str = None,
    layout: None | str = None,
    is_external: bool = False,
    ) -> nodes.Node:

    env = app.env

    opcua = env.get_domain('opcua')

    # Calculate target id, to be able to set a link back
    if is_external:
        target_node = None
    else:
        target_node = nodes.target("", "", ids=[data.nodeid], refid=data.nodeid)
        external_url = None

    if not hasattr(env, "needs_all_needs"):
        env.needs_all_needs = {}

    # Calculate doc type, e.g. .rst or .md
    if state and state.document and state.document.current_source:
        doctype = os.path.splitext(state.document.current_source)[1]
    else:
        doctype = ".rst"

    # build the basic attributes of the node
    basic_attribs = {"NodeId": data.nodeid, "NodeClass": data.nodetype, "BrowseName": data.browsename}

    if data.parent:
        basic_attribs["ParentNodeId"] = data.parent
        # Try to find the parent browse name
        parent_node = opcua.find_uanode_by_id(data.parent)
        if parent_node:
            basic_attribs["ParentBrowseName"] = parent_node.browsename

    DisplayName = data.browsename
    # This could be localized, but is not supported at the moment by SIOME and asyncua
    if isinstance(data.displayname, str):
        DisplayName = data.displayname

    # This could be localized, but is not supported at the moment by SIOME and asyncua
        
    # We prefix the content with the description, if available
    if isinstance(data.desc, str):
        content = data.desc + "\n" + content

    # Additional attributes are dependent on the nodetype
    additional_attribs = {}
    if data.datatype:
        additional_attribs["DataType"] = data.datatype

    if data.rank > 0:    
        additional_attribs["ValueRank"] = data.rank
        if data.dimensions:
            additional_attribs["ArrayDimensions"] = data.dimensions

    childs = opcua.find_child_nodes(data.nodeid)


    # Hierarchical References
    # [forward, ReferenceType, TargetId, NodeClass, Name, TypeDefinition, ModellingRule, DataType]
    hierarchical_refs = []
    for ref in data.refs:
        if ref.reftype == "HasSubtype" or ref.reftype == "Organizes" or ref.reftype == "HasComponent":
            hierarchical_refs.append({'Forward':ref.forward, 'ReferenceType':ref.reftype, 'TargetId': ref.target, 'NodeClass': "", 'Name': opcua.get_target_name(ref.target), 'TypeDefinition': "--", 'ModellingRule': "--", 'DataType': "--"})

    for child in childs:
        ModellingRule = ""
        TypeDefinition = ""
        DataType = ""
        if child.datatype:
            if re.match(r'i=|ns=', child.datatype):
                DataType = opcua.get_target_name(child.datatype)
            else:
                DataType = child.datatype

        # first find the non-hierarchical references
        for ref in child.refs:
            if ref.reftype == "HasModellingRule":
                ModellingRule = opcua.get_target_name(ref.target)
                #shorten the name
                m = re.match(r'ModellingRule_(.+)', ModellingRule)
                if m:
                    ModellingRule = m.group(1)
            if ref.reftype == "HasTypeDefinition":
                TypeDefinition = opcua.get_target_name(ref.target)

        for ref in child.refs:
            if ref.reftype == "HasComponent" or ref.reftype == "HasProperty":
                hierarchical_refs.append({'Forward': not ref.forward, 'ReferenceType':ref.reftype, 'TargetId': child.nodeid,  'NodeClass':child.nodetype, 'Name': child.browsename, 'TypeDefinition': TypeDefinition, 'ModellingRule': ModellingRule, 'DataType': DataType})
    #hierarchical_refs = opcua.find_references_by_target(data.nodeid)
                
    non_hierarchical_refs = []
    for ref in data.refs:
        if ref.reftype == "HasModellingRule":
            Target = opcua.get_target_name(ref.target)
            #shorten the name
            m = re.match(r'ModellingRule_(.+)', Target)
            if m:
                Target = m.group(1)
            non_hierarchical_refs.append({'Forward':ref.forward, 'ReferenceType':ref.reftype, 'Target': Target, 'Target NodeId': ref.target})

        if ref.reftype == "HasTypeDefinition":
            Target = opcua.get_target_name(ref.target)

            non_hierarchical_refs.append({'Forward':ref.forward, 'ReferenceType':ref.reftype, 'Target': Target, 'Target NodeId': ref.target})







    #ua_references = data.refs    

    ua_info = {
        "docname": docname,
        "doctype": doctype,
        "lineno": lineno,
        "type_name": data.nodetype,
        "title": DisplayName,
        "ua_attributes": basic_attribs,
        "ua_additional_attributes": additional_attribs,
        "ua_hierarchical_refs": hierarchical_refs,
        "ua_non_hierarchical_refs": non_hierarchical_refs,
        "content": content,
        "hide": hide,
        "is_external": is_external,
        "style": style,
        "layout": layout,

    }

    env.needs_all_needs[data.nodeid] = ua_info

    if ua_info["is_external"]:
        return[]
    
    if ua_info["hide"]:
        return [target_node]
    
    style_classes = ["need"]
    if style:
        style_classes.append(style)
    
    node_ua = uanodes("", classes=style_classes,ids=[data.nodeid], refid=data.nodeid)

    node_ua.line = ua_info["lineno"]

    node_ua_content = _render_template(content, docname, lineno, state)

    ua_parts = find_parts(node_ua_content)

    update_need_with_parts(env, ua_info, ua_parts)

    node_ua += node_ua_content.children

    ua_info["content_id"] = node_ua["ids"][0]

    # Create a copy of the content
    ua_info["content_node"] = node_ua.deepcopy()

    return_nodes = [target_node] + [node_ua]

    return return_nodes


def _render_template(content: str, docname: str, lineno: int, state: RSTState) -> nodes.Element:
    rst = StringList()
    for line in content.split("\n"):
        rst.append(line, docname, lineno)
    node_ua_content = nodes.Element()
    node_ua_content.document = state.document
    _nested_parse_with_titles(state, rst, node_ua_content)
    return node_ua_content

def _nested_parse_with_titles(state: Any, content: StringList, node: nodes.Node,
                             content_offset: int = 0) -> str:
    """Version of state.nested_parse() that allows titles and does not require
    titles to have the same decoration as the calling document.

    This is useful when the parsed content comes from a completely different
    context, such as docstrings.
    """
    # hack around title style bookkeeping
    surrounding_title_styles = state.memo.title_styles
    surrounding_section_level = state.memo.section_level
    state.memo.title_styles = []
    state.memo.section_level = 0
    try:
        return state.nested_parse(content, content_offset, node, match_titles=1)
    finally:
        state.memo.title_styles = surrounding_title_styles
        state.memo.section_level = surrounding_section_level
        

part_pattern = re.compile(r"\(([\w-]+)\)(.*)")

def update_need_with_parts(env: BuildEnvironment, ua_info, part_nodes: List[UAPart]) -> None:
    app = unwrap(env.app)
    builder = unwrap(app.builder)
    for part_node in part_nodes:
        content = part_node.children[0].children[0]  # ->inline->Text
        result = part_pattern.match(content)
        if result:
            inline_id = result.group(1)
            part_content = result.group(2)
        else:
            part_content = content
            inline_id = hashlib.sha1(part_content.encode("UTF-8")).hexdigest().upper()[:3]

        if "parts" not in ua_info:
            ua_info["parts"] = {}

        if inline_id in ua_info["parts"]:
            logger.warning(
                "part_need id {} in need {} is already taken. need_part may get overridden.".format(
                    inline_id, ua_info["id"]
                )
            )

        ua_info["parts"][inline_id] = {
            "id": inline_id,
            "content": part_content,
            "document": ua_info["docname"],
            "links_back": [],
            "is_part": True,
            "is_need": False,
            "links": [],
        }

        part_id_ref = "{}.{}".format(ua_info["id"], inline_id)
        part_id_show = inline_id
        part_node["reftarget"] = part_id_ref

        part_link_text = f" {part_id_show}"
        part_link_node = nodes.Text(part_link_text)
        part_text_node = nodes.Text(part_content)

        from sphinx.util.nodes import make_refnode

        part_ref_node = make_refnode(builder, ua_info["docname"], ua_info["docname"], part_id_ref, part_link_node)
        part_ref_node["classes"] += ["needs-id"]

        part_node.children = []
        node_need_part_line = nodes.inline(ids=[part_id_ref], classes=["need-part"])
        node_need_part_line.append(part_text_node)
        node_need_part_line.append(part_ref_node)
        part_node.append(node_need_part_line)



def find_parts(node: nodes.Element) -> List[UAPart]:
    found_nodes = []
    for child in node.children:
        if isinstance(child, UAPart):
            found_nodes.append(child)
        else:
            found_nodes += find_parts(child)
    return found_nodes

def process_ua_nodes(app: Sphinx, doctree: nodes.document, fromdocname: str) -> None:
    """
    Finally creates the need-node in the docutils node-tree.

    :param app:
    :param doctree:
    :param fromdocname:
    :return:
    """

    builder = unwrap(app.builder)
    env = unwrap(builder.env)

    opcua = env.get_domain('opcua')

    for node in doctree.findall(uanodes):

        node_id = node.attributes["ids"][0]

        ua_node = opcua.get_uavariable(node_id)

        layout = "detailed"

        build_need(layout, node, ua_node, app, doctree, fromdocname=fromdocname)
