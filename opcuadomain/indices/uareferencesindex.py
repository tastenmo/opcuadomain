from collections import defaultdict

from sphinx.domains import Index

class UAReferenceIndex(Index):
    """A custom index that creates an OPC-UA reference matrix."""

    name = 'uareference'
    localname = 'UAReference Index'
    shortname = 'UAReference'

    def generate(self, docnames=None):
        content = defaultdict(list)

        variables = {name: (dispname, typ, docname, anchor)
                   for name, dispname, typ, docname, anchor, _
                   in self.domain.get_objects()}
        variable_references = self.domain.data['UAReferences']
        reference_variables = defaultdict(list)

        # flip from recipe_ingredients to ingredient_recipes
        for opcua_name, references in variable_references.items():
            for reference in references:
                reference_variables[reference].append(opcua_name)

        # convert the mapping of ingredient to recipes to produce the expected
        # output, shown below, using the ingredient name as a key to group
        #
        # name, subtype, docname, anchor, extra, qualifier, description
        for reference, opcua_names in reference_variables.items():
            for opcua_name in opcua_names:
                dispname, typ, docname, anchor = variables[opcua_name]
                content[reference].append(
                    (dispname, 0, docname, anchor, docname, '', typ))

        # convert the dict to the sorted list of tuples expected
        content = sorted(content.items())

        return content, True