from collections import defaultdict

from sphinx.domains import Index

class UAVariableIndex(Index):
    """A custom index that creates an uavariable matrix."""

    name = 'uavariable'
    localname = 'UAVariable Index'
    shortname = 'UAVariable'

    def generate(self, docnames=None):
        content = defaultdict(list)

        # sort the list of recipes in alphabetical order
        variables = self.domain.get_objects()
        #variables = sorted(variables, key=lambda variable: UAVariable[0])

        # generate the expected output, shown below, from the above using the
        # first letter of the recipe as a key to group thing
        #
        # name, subtype, docname, anchor, extra, qualifier, description
        for _name, dispname, typ, docname, anchor, _priority in variables:
            content[dispname[0].lower()].append(
                (dispname, 0, docname, anchor, docname, '', typ))

        # convert the dict to the sorted list of tuples expected
        content = sorted(content.items())

        return content, True
