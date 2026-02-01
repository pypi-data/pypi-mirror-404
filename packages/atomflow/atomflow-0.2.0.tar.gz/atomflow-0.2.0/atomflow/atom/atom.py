from typing import Self, Iterable, Mapping

from atomflow.aspects import Aspect, NameAspect, PositionAspect, ElementAspect, IndexAspect
from atomflow.components import Component, NameComponent, IndexComponent


class Atom:

    r"""
    Data components can be added at initialisation.
    >>> name_cmp = NameComponent("CA")
    >>> atom = Atom(name_cmp)
    >>> assert atom._components == {NameAspect: [name_cmp]}

    Underlying data can be accessed with dot- or square bracket-notation with the aspect keyword.
    >>> assert atom.name == "CA"
    >>> assert atom["name"] == "CA"

    Either method raises AttributeError if the data doesn't exist.
    >>> atom.tree
    Traceback (most recent call last):
        ...
    AttributeError: Atom has no data for 'tree'

    The default short (s) string format only shows aspects and their associated values in alphabetical
    order:
    >>> atom = Atom(NameComponent("CA"), IndexComponent(1))
    >>> assert str(atom) == f"{atom:s}" == "Atom(index=1, name=CA)"

    Long (l) format lists components:
    >>> assert f"{atom:l}" == "Atom(\n\tIndexComponent(index=1),\n\tNameComponent(name=CA)\n)"

    Which prints as:
    Atom(
        IndexComponent(index=1),
        NameComponent(name=CA)
    )
    """

    def __init__(self, *components: Component | Iterable[Component]):
        self._components: dict[Aspect: list[Component]] = {}
        for c in components:
            self.add(c)

    def __getattr__(self, item):
        if comps := self._components.get(item):
            return getattr(comps[-1], item)
        raise AttributeError(f"Atom has no data for '{item}'")

    def __getitem__(self, item):
        return self.__getattr__(item)

    def __format__(self, format_spec):
        if not format_spec:
            return f"{self:s}"
        elif format_spec == 'l':
            cmp_vals = [str(cmps[-1]) for cmps in sorted(self._components.values())]
            cmp_lines = ",\n\t".join(cmp_vals)
            return f"Atom(\n\t{cmp_lines}\n)"
        elif format_spec == 's':
            vals = [f"{asp.name}={self[asp.name]}" for asp in sorted(self._components)]
            return f"Atom({', '.join(vals)})"
        else:
            raise ValueError(f"Unknown format code '{format_spec}' for object of type 'Atom'.")

    def __repr__(self):
        return f"{self}"

    def __eq__(self, other: Self):
        return str(self) == str(other)

    def __lt__(self, other: Self):
        return str(self) < str(other)

    def add(self, cmp: Component) -> None:

        """
        Add a component to the atom.
        >>> index_cmp = IndexComponent(1)
        >>> atom = Atom()
        >>> atom.add(index_cmp)
        >>> assert atom._components == {IndexAspect: [index_cmp]}

        New components overwrite others with the same aspects.
        >>> assert atom.index == 1
        >>> atom.add(IndexComponent(2))
        >>> assert atom.index == 2
        """

        for asp in cmp.aspects:
            self._components.setdefault(asp, []).append(cmp)

    def implements(self, item: Aspect | str | Mapping) -> bool:

        """
        Check if an atom implements an aspect or conforms to a recipe.

        Single aspects can be referred to by their instances, or their string names.
        >>> atom = Atom(NameComponent("CA"))
        >>> assert atom.implements(NameAspect) == True
        >>> assert atom.implements("name") == True
        >>> assert atom.implements(ElementAspect) == False

        Recipes are expected as branching mappings with each key as the logical operator
        for the following iterable of aspects.
        >>> recipe = {"or" : [NameAspect, {"and": [ElementAspect, PositionAspect]}]}
        >>> assert atom.implements(recipe) == True
        >>> recipe = {"and": [PositionAspect, {"or": [NameAspect, ElementAspect]}]}
        >>> assert atom.implements(recipe) == False
        """

        if isinstance(item, Aspect) or isinstance(item, str):
            return item in self._components

        elif isinstance(item, Mapping):
            for key in item:
                if key == "or":
                    if not any(self.implements(x) for x in item[key]):
                        return False
                elif key == "and":
                    if not all(self.implements(x) for x in item[key]):
                        return False
                else:
                    raise KeyError(f"Unknown operator: '{key}'")
        else:
            return False

        return True

    def get(self, asp: str | Aspect):

        """Retrieve data for an aspect, returning None if the data doesn't exist.

        >>> atom = Atom(NameComponent("CA"))
        >>> assert atom.get("name") == "CA"
        >>> assert atom.get("tree") is None
        """

        try:
            asp = asp.name if isinstance(asp, Aspect) else asp
            return self.__getattr__(asp)
        except AttributeError:
            return None

if __name__ == '__main__':
    pass