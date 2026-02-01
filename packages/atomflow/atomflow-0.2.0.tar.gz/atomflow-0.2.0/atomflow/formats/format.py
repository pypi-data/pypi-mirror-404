from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
import os

from atomflow.atom import Atom


class Format(ABC):

    """
    Representation of a file format that can be read from and written to.
    """

    _register = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for ext in cls.extensions:
            Format._register[ext] = cls

    @classmethod
    def get_format(cls, ext: str) -> Format:

        """
        Fetch the subclass registered for a given extension.

        :param ext: file suffix, e.g. '.pdb'.
        :return:
        """

        try:
            return cls._register[ext]
        except KeyError:
            raise ValueError(f"No format found for extension '{ext}'")

    @property
    @abstractmethod
    def extensions(self) -> tuple[str]:

        """
        File suffixes this format relates to. E.g., ('.fasta', '.faa', '.fna'). When writing,
        the first of these is used.
        """

    @property
    @abstractmethod
    def recipe(self) -> Mapping:

        """
        Description of which aspects an atom must implement to be written to this format. Expected
        to be a nested mapping with keys as logical operators for the iterable of aspects/mappings
        that follow.

        E.g.:
        recipe = {"or" : [NameAspect, {"and": [ElementAspect, PositionAspect]}]}
        -> Atom object must have either a NameAspect, or both element and position aspects.

        :return:
        """


    @classmethod
    @abstractmethod
    def read_file(cls, path: str | os.PathLike) -> list[Atom]:

        """
        Read a file in this format into a list of atoms.
        """

    @classmethod
    @abstractmethod
    def to_file(cls, atoms: Iterable[Atom], path: str | os.PathLike) -> None:

        """
        Write an iterable of atoms to a file in this format.
        """