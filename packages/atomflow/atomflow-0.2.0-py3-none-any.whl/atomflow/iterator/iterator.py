from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from operator import attrgetter
import os
import pathlib

from atomflow.atom import Atom
from atomflow.components import NameComponent, ResidueComponent, IndexComponent
from atomflow.formats import Format


END = object()


class AtomIterator:

    """
    Base iterator over groups of atoms, generally made at the start of an iterator chain.

    Can be initialised directly from an iterable of iterables of Atoms objects. By itself,
    outputs groups as it receives them.
    >>> atom_a = Atom(NameComponent("A"), ResidueComponent("X"), IndexComponent(3))
    >>> atom_b = Atom(NameComponent("B"), ResidueComponent("X"), IndexComponent(1))
    >>> atom_c = Atom(NameComponent("C"), ResidueComponent("Y"), IndexComponent(2))

    >>> groups = [(atom_a,), (atom_b, atom_c)]
    >>> a_iter = AtomIterator(groups)
    >>> assert list(a_iter) == [(atom_a,), (atom_b, atom_c)]

    AtomIterator.from_list() creates an iterator over groups containing individual atoms.
    >>> a_iter = AtomIterator.from_list([atom_a, atom_b, atom_c])
    >>> assert list(a_iter) == [(atom_a,), (atom_b,), (atom_c,)]

    AtomIterator.collect() creates an iterator that yields all atoms as a single group.
    >>> a_iter = AtomIterator.from_list([atom_a, atom_b, atom_c]).collect()
    >>> assert list(a_iter) == [(atom_a, atom_b, atom_c)]

    AtomIterator.to_list() returns a list with groups have been flattened.
    >>> groups = [(atom_a, atom_b), (atom_c,)]
    >>> assert AtomIterator(groups).to_list() == [atom_a, atom_b, atom_c]

    Subclasses are iterators that can be passed between each other via functions
    inherited from this class.
    >>> a_iter = AtomIterator.from_list([atom_a, atom_b, atom_c])
    >>> a_list = a_iter.group_by("resname").filter("name", none_of=["B"]).to_list()
    >>> assert a_list == [atom_c]
    """

    def __init__(self, atom_groups: Iterable[Iterable[Atom]]):
        self._atom_groups = iter(atom_groups)

    def __next__(self):
        return next(self._atom_groups)

    def __iter__(self):
        return self

    def group_by(self, aspect: str | None = None) -> GroupIterator:

        """Group sequential atoms which share the aspect value. Precede with .collect().sort(aspect) to group
        all atoms"""

        return GroupIterator(self, aspect)

    def filter(self, aspect: str,
               any_of: None | Iterable = None, none_of: None | Iterable = None) -> FilterIterator:

        """Filter atom groups based on the given criteria. If the value of aspect for any one atom in a group matches
        the any_of or none_of conditions, the whole group is included or excluded, respectively."""

        return FilterIterator(self, aspect, any_of, none_of)

    @classmethod
    def from_list(cls, atoms: Iterable[Atom]) -> GroupIterator:

        """Convert an iterable of atoms into an iterator over groups containing individual atoms."""

        return GroupIterator([atoms])

    def collect(self) -> AtomIterator:

        """Create an iterator that returns all atoms in one group."""

        return AtomIterator([tuple(self.to_list())])

    def sort(self, aspect: str) -> SortedIterator:

        """Sort each group by the given aspect."""

        return SortedIterator(self, aspect, rev=False)

    def to_list(self) -> list[Atom]:

        """Return a list of atoms with all groups flattened."""

        return [atm for grp in self for atm in grp]

    def write(self,
              path: str | os.PathLike,
              path_fmt: Iterable[str] | None = None,
              ) -> tuple[list[str], list[Exception]]:

        """
        Writes atoms group-wise to the path. Intended format is inferred from the file
        extension. Variations of the file name are produced automatically if needed.

        :param path: location for output file, e.g. './data/struct.pdb'
        :param path_fmt: aspects to insert into empty curly brace pairs in path name. Values are
        taken from the first atom in the group. E.g., for atoms grouped by chain, with chain aspect
        values "A" and "B":
        <AtomIterator>.write(path="./struct_{}.pdb", path_fmt=["chain"])
        -> ["./struct_A.pdb", "./struct_B.pdb"]

        :return: ([paths to outputs], [errors])
        """

        path = pathlib.Path(path)
        ext = path.suffix

        # Retrieve the correct format
        writer = Format.get_format(ext)

        filenames = []
        errors = []

        for i, group in enumerate(self):

            stem = path.stem

            # Format filename with aspects
            if path_fmt:
                group = list(group)
                atom = group[0]
                stem = stem.format(*[atom[asp] for asp in path_fmt])

            # If filename has already been used, make a variant
            filename = str(path.parent / f"{stem}{ext}")
            variant_count = 0
            while filename in filenames:
                variant_count += 1
                filename = str(path.parent / f"{stem}_{variant_count}{ext}")

            # Attempt to write atoms to format
            try:
                writer.to_file(group, filename)
                filenames.append(str(filename))
            except Exception as e:
                errors.append(e)

        return filenames, errors


class GroupIterator(AtomIterator):

    """
    Dispense sequential atoms grouped by a given aspect.
    >>> atom_a = Atom(NameComponent("A"), ResidueComponent("X"))
    >>> atom_b = Atom(NameComponent("B"), ResidueComponent("Y"))
    >>> atom_c = Atom(NameComponent("B"), ResidueComponent("X"))
    >>> g_iter = GroupIterator([(atom_a, atom_b, atom_c)], group_by="name")
    >>> assert list(g_iter) == [(atom_a,), (atom_b, atom_c)]

    Only collects sequential similar atoms.
    >>> g_iter = GroupIterator([(atom_a, atom_b, atom_c)], group_by="resname")
    >>> assert list(g_iter) == [(atom_a,), (atom_b,), (atom_c,)]

    If no grouping value is given, each atom is grouped separately
    >>> g_iter = GroupIterator([(atom_a, atom_b, atom_c)])
    >>> assert list(g_iter) == [(atom_a,), (atom_b,), (atom_c,)]
    """

    def __init__(self, atom_groups, group_by=None):

        super().__init__(atom_groups)

        self._group_by = group_by

        self._last_value = None
        self._queue = deque()
        self._source_state = None
        self._buffer = []

    def __next__(self):

        # If no atoms left to dispense, signal end of iteration
        if self._source_state == END:
            raise StopIteration

        while True:

            # If the queue is empty
            if len(self._queue) == 0:

                # Try to withdraw the next group of atoms from the source, and add to the queue
                try:
                    next_group = next(self._atom_groups)
                    self._queue.extend(next_group)

                # If source is empty, return the remaining buffer contents and set up end of iterator
                except StopIteration:
                    self._source_state = END
                    return tuple(self._buffer)

            # Get the next atom and its grouping value. If no grouping key was given, use
            # object id as the value so that each atom gets grouped separately.
            atom = self._queue.popleft()
            value = atom[self._group_by] if self._group_by is not None else id(atom)

            # If the atom is the first, or it has the same grouping value as the previous, add
            # it to the buffer
            if self._last_value in (None, value):
                self._buffer.append(atom)
                self._last_value = value

            # If the atom has a new grouping value, output the buffer and reinitialise with this atom
            else:
                out = self._buffer[:]
                self._buffer = [atom]
                self._last_value = value
                return tuple(out)


class FilterIterator(AtomIterator):

    """
    Filter Atoms based on either allowed or disallowed values of an aspect.

    >>> atom_a = Atom(NameComponent("A"))
    >>> atom_b = Atom(NameComponent("B"))
    >>> atom_c = Atom(NameComponent("C"))
    >>> atom_groups = [(atom_a,), (atom_b,), (atom_c,)]
    >>> f_iter = FilterIterator(atom_groups, "name", none_of=["B"])
    >>> assert list(f_iter) == [(atom_a,), (atom_c,)]

    If any one atom in a group matches the any_of or none_of conditions, the whole group is included or
    excluded, respectively.
    >>> atom_groups = [(atom_a, atom_c), (atom_b,)]
    >>> f_iter = FilterIterator(atom_groups, "name", none_of=["C"])
    >>> assert list(f_iter) == [(atom_b,)]
    >>> f_iter = FilterIterator(atom_groups, "name", any_of=["A"])
    >>> assert list(f_iter) == [(atom_a, atom_c)]
    """

    def __init__(self, atom_groups, aspect: str,
                 any_of: None | Iterable = None, none_of: None | Iterable = None):

        super().__init__(atom_groups)
        aspect = str(aspect)

        if any_of is None:
            self._filter = lambda group: not any(atom[aspect] in none_of for atom in group)
        elif none_of is None:
            self._filter = lambda group: any(atom[aspect] in any_of for atom in group)
        else:
            raise ValueError("One of 'any_of' or 'none_of' must be provided")

    def __next__(self):
        while True:
            group = next(self._atom_groups)
            if self._filter(group):
                return group


class SortedIterator(AtomIterator):

    """Sorts the atoms in each group by the given key, or by Atom string if no key given.

    >>> atom_a = Atom(NameComponent("A"))
    >>> atom_b = Atom(NameComponent("B"))
    >>> atom_c = Atom(NameComponent("C"))
    >>> atom_d = Atom(NameComponent("D"))
    >>> groups = [(atom_c, atom_a), (atom_b, atom_d)]

    >>> assert list(SortedIterator(groups, "name")) == [(atom_a, atom_c), (atom_b, atom_d)]
    >>> assert list(SortedIterator(groups, "name", rev=True)) == [(atom_c, atom_a), (atom_d, atom_b)]

    Collect first to sort over all atoms
    >>> a_iter = AtomIterator(groups).collect().sort("name")
    >>> assert list(a_iter) == [(atom_a, atom_b, atom_c, atom_d)]
    """

    def __init__(self, atom_groups, aspect: str, rev=False):
        super().__init__(atom_groups)

        aspect = str(aspect)
        self._key_fn = attrgetter(aspect)
        self._rev = rev

    def __next__(self):
        while True:
            group = next(self._atom_groups)
            return tuple(sorted(group, key=self._key_fn, reverse=self._rev))


def read(path: str | os.PathLike) -> AtomIterator:

    """
    Read a file into an iterator of atoms. Format is inferred from file extension.
    """

    path = pathlib.Path(path)
    reader = Format.get_format(path.suffix)
    atoms = reader.read_file(path)
    return AtomIterator.from_list(atoms)


if __name__ == '__main__':
    pass