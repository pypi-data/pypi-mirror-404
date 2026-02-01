from collections import Counter
import os
from typing import Iterable

from atomflow.components import *
from atomflow.aspects import *
from atomflow.atom import Atom
from atomflow.formats import Format
from atomflow.knowledge.codes import POLYMER_CODE_SETS, POLYMER_RESIDUE_CODES


class PDBFormat(Format):

    recipe = {
        "and": [
            IndexAspect,
            ElementAspect,
            ResNameAspect,
            ChainAspect,
            ResIndexAspect,
            CoordXAspect,
            CoordYAspect,
            CoordZAspect,
        ]
    }

    extensions = (".pdb",)

    _fields = {
        "section": slice(6),
        "serial_no": slice(6, 11),
        "atom_name": slice(12, 16),
        "alt_loc": slice(16, 17),
        "residue_name": slice(17, 20),
        "strand_id": slice(21, 22),
        "residue_no": slice(22, 26),
        "ins_code": slice(26, 27),
        "x": slice(30, 38),
        "y": slice(38, 46),
        "z": slice(46, 54),
        "occupancy": slice(54, 60),
        "t_factor": slice(60, 66),
        "symbol": slice(76, 78),
        "charge": slice(78, 80)
    }

    _cmp_map = {
        "section": SectionComponent,
        "serial_no": IndexComponent,
        "atom_name": NameComponent,
        "alt_loc": AltLocComponent,
        "residue_name": ResidueComponent,
        "strand_id": ChainComponent,
        "residue_no": ResIndexComponent,
        "ins_code": InsertionComponent,
        "x": CoordXComponent,
        "y": CoordYComponent,
        "z": CoordZComponent,
        "occupancy": OccupancyComponent,
        "t_factor": TemperatureFactorComponent,
        "symbol": ElementComponent,
        "charge": FormalChargeComponent,
    }

    _asp_map = {
        "section": SectionAspect,
        "serial_no": IndexAspect,
        "atom_name": NameAspect,
        "alt_loc": AltLocAspect,
        "residue_name": ResNameAspect,
        "strand_id": ChainAspect,
        "residue_no": ResIndexAspect,
        "ins_code": InsertionAspect,
        "x": CoordXAspect,
        "y": CoordYAspect,
        "z": CoordZAspect,
        "occupancy": OccupancyAspect,
        "t_factor": TemperatureFactorAspect,
        "symbol": ElementAspect,
        "charge": FormalChargeAspect,
    }

    _defaults = {
        "occupancy": 1,
        "t_factor": 10,
    }

    _line_template =\
            "{section: <6}{serial_no: >5} {name_field}{alt_loc: >1}"\
            "{residue_name: >3} {strand_id}{residue_no: >4}{ins_code: >1}   "\
            "{x: >8.3f}{y: >8.3f}{z: >8.3f}{occupancy: >6.2f}{t_factor: >6.2f}          "\
            "{symbol: >2}{charge: <2}"

    @classmethod
    def _extract_data(cls, path) -> dict:
        data = {}
        with open(path, "r") as file:
            lines = (line.strip() for line in file.readlines() if line[:6] in ("ATOM  ", "HETATM"))
        for line in lines:
            for field, col in cls._fields.items():
                data.setdefault(field, []).append(line[col].strip())
        return data

    @classmethod
    def _classify_chains(cls, data: dict) -> dict[str, PolymerComponent]:

        """
        Assigns polymer components to chain IDs, based on the modal residue type.

        :param data: dict of data extracted from a pdb file, with at least 'section',
        'residue name' and 'strand_id' keys.
        """

        chains = {}
        for rec, res, chain in zip(data["section"], data["residue_name"], data["strand_id"]):
            count = chains.setdefault(chain, Counter())
            for poly_type, res_codes in POLYMER_CODE_SETS.items():
                if res in res_codes:
                    count[poly_type] = count.setdefault(poly_type, 0) + 1
                    break
            else:
                count["other"] = count.setdefault("other", 0) + 1

        return {k: PolymerComponent(v.most_common(1)[0][0]) for k, v in chains.items()}

    @classmethod
    def _atoms_from_data(cls, data: dict) -> list[Atom]:

        """
        Composes Atom objects using data extracted from a PDB file.
        """

        polymer_classes = cls._classify_chains(data)

        atoms = []
        for i in range(len(data["section"])):
            cmps = []
            for field, col in data.items():
                value = col[i]
                if not value:
                    continue
                if cmp_type := cls._cmp_map.get(field):
                    cmps.append(cmp_type(value))
                if data["section"][i] == "HETATM":
                    continue
                # For ATOM records, assign polymer type
                # if field == "strand_id" and value in polymer_classes:
                #     cmps.append(polymer_classes[value])
            atoms.append(Atom(*cmps))

        return atoms

    @classmethod
    def _atoms_to_dict(cls, atoms: Iterable[Atom]) -> dict:

        data = {k: [] for k in PDBFormat._fields}

        for atom in atoms:
            if not atom.implements(cls.recipe):
                raise ValueError(f"{atom} does not implement aspects required for PDB format")
            for field, col in data.items():
                if field == "section":
                    value = "ATOM" if atom.resname in POLYMER_RESIDUE_CODES else "HETATM"
                    col.append(value)
                    continue
                aspect = cls._asp_map[field]
                if atom.implements(aspect):
                    col.append(atom[aspect.name])
                elif default := cls._defaults.get(field):
                    col.append(default)
                else:
                    col.append('')
        return data


    @classmethod
    def _dict_to_file(cls, data: dict, path) -> None:

        lines = []
        for i in range(len(data["section"])):
            values = {k: col[i] for k, col in data.items()}

            # Build name field
            name = values["atom_name"]
            element = values["symbol"]
            if name == "UNK":
                name_field = " UNK"
            elif name == '':
                name_field = f"{element: >2}  "
            else:
                position = name[len(element):]
                name_field = f"{element: >2}{position: <2}"
            # Hydrogen names sometimes spill over on the right - remove leading space to correct
            if len(name_field) > 4:
                name_field = name_field.lstrip()

            values.update({"name_field": name_field})
            line = cls._line_template.format(**values)
            lines.append(line)

        with open(path, "w") as file:
            file.write("\n".join(lines))

    @classmethod
    def read_file(cls, path: str | os.PathLike) -> list[Atom]:

        data = cls._extract_data(path)
        return cls._atoms_from_data(data)

    @classmethod
    def to_file(cls, atoms: Iterable[Atom], path: str | os.PathLike) -> None:

        data = cls._atoms_to_dict(atoms)
        cls._dict_to_file(data, path)


if __name__ == '__main__':

    path = "../../tests/data/pdb/3WDD.pdb"

    original = PDBFormat.read_file(path)
    PDBFormat.to_file(original, "./test.pdb")
    new = PDBFormat.read_file("./test.pdb")

    assert  original == new
