from dataclasses import dataclass

@dataclass(frozen=True)
class Aspect:

    """
    Aspect objects represent shared labels for data associated with an atom.

    Instances equal the strings they contain for convenience with lookup.
    >>> asp = Aspect("index")
    >>> assert asp == "index"
    >>> mapping = {"index": 1}
    >>> assert mapping[asp] == 1
    """

    name: str

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        else:
            return self == other

    def __lt__(self, other):
        if isinstance(other, Aspect):
            return self.name < other.name
        elif isinstance(other, str):
            return self.name < other
        else:
            return self < other

# Atom
AltLocAspect = Aspect("altloc")  # Identifier for one of multiple alternative locations
CoordXAspect = Aspect("x")  # Atom's x-coordinate
CoordYAspect = Aspect("y")  # Atom's y-coordinate
CoordZAspect = Aspect("z")  # Atom's z-coordinate
ElementAspect = Aspect("element")  # Element of the atom
IndexAspect = Aspect("index")  # Ordinal index of the atom in its molecule
InsertionAspect = Aspect("insertion")  # Identifier for insertion of the atom into the index
NameAspect = Aspect("name")  # Name of the atom
OccupancyAspect = Aspect("occupancy")  # Fractional occupancy of the atom in this alt. loc.
PositionAspect = Aspect("position")  # Position of the atom in the molecule or relative to the backbone
TemperatureFactorAspect = Aspect("temp_f") # Atom's isotropic temperature factor
FormalChargeAspect = Aspect("fcharge")  # Atom's formal charge, e.g. -1, 0, +1
SectionAspect = Aspect("section")  # ATOM or HETATM label

# Residue
ResNameAspect = Aspect("resname")  # Name of the residue the atom is part of
ResOLCAspect = Aspect("res_olc")  # One-letter code for the residue the atom is a part of
ResTLCAspect = Aspect("res_tlc")  # Three-letter code for the residue the atom is a part of
ResIndexAspect = Aspect("resindex")  # Ordinal index of the atom's residue in its polymer

# Molecule
ChainAspect = Aspect("chain")  # Chain the atom is part of or associated with
EntityAspect = Aspect("entity")  # Entity, i.e. distinct chemical species, the atom is a part of
PolymerAspect = Aspect("polymer")  # Polymer type the atom is part of


