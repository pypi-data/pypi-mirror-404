import pathlib
from collections import defaultdict
import os
from typing import Iterable

from atomflow.components import *
from atomflow.atom import Atom
from atomflow.formats import Format
from atomflow.knowledge import AA_RES_TO_SYM

COLUMN_PADDING = 1
WRAP_AT = 80

class CIFFormat(Format):

    recipe = {
        "and": [
            IndexAspect,
            ChainAspect,
            NameAspect,
            ResNameAspect,
            ElementAspect,
            CoordXAspect,
            CoordYAspect,
            CoordZAspect,
        ]
    }

    extensions = (".cif", ".mmcif")

    _cmp_map = {
        "group_PDB": SectionComponent,
        "id": IndexComponent,
        "label_alt_id": AltLocComponent,
        "label_asym_id": ChainComponent,
        "label_atom_id": NameComponent,
        "label_comp_id": ResidueComponent,
        "label_seq_id": ResIndexComponent,
        "type_symbol": ElementComponent,
        "Cartn_x": CoordXComponent,
        "Cartn_y": CoordYComponent,
        "Cartn_z": CoordZComponent,
        "occupancy": OccupancyComponent,
        "pdbx_PDB_ins_code": InsertionComponent,
        "B_iso_or_equiv": TemperatureFactorComponent,
        "pdbx_formal_charge": FormalChargeComponent,
        "auth_asym_id": ChainComponent,
    }

    _asp_map = {
        "group_PDB": SectionAspect,
        "id": IndexAspect,
        "label_alt_id": AltLocAspect,
        "label_asym_id": ChainAspect,
        "label_atom_id": NameAspect,
        "label_comp_id": ResNameAspect,
        "label_seq_id": ResIndexAspect,
        "type_symbol": ElementAspect,
        "Cartn_x": CoordXAspect,
        "Cartn_y": CoordYAspect,
        "Cartn_z": CoordZAspect,
        "occupancy": OccupancyAspect,
        "pdbx_PDB_ins_code": InsertionAspect,
        "B_iso_or_equiv": TemperatureFactorAspect,
        "pdbx_formal_charge": FormalChargeAspect,
        "auth_asym_id": ChainAspect,
    }

    _field_formats = {
        "id": "{}",
        "label_seq_id": "{}",
        "Cartn_x": "{:.3f}",
        "Cartn_y": "{:.3f}",
        "Cartn_z": "{:.3f}",
        "occupancy": "{:.2f}",
        "B_iso_or_equiv": "{:.2f}",
    }

    @classmethod
    def read_file(cls, path: str | os.PathLike) -> list[Atom]:
        data = cls._extract_data(path, categories=("_atom_site",))
        return cls._atoms_from_dict(data)

    @classmethod
    def _atoms_from_dict(cls, data: dict) -> list[Atom]:

        atoms = []

        for dataset in data.values():
            atom_table = dataset["_atom_site"]
            for atom_i in range(len(atom_table["id"])):
                cmps = []
                values = [col[atom_i] for col in atom_table.values()]
                for field_name, value in zip(atom_table, values):
                    # Skip unknown/placeholder values
                    if value in "?.":
                        continue
                    elif field_name in cls._cmp_map:
                        cmp_type = cls._cmp_map[field_name]
                        cmps.append(cmp_type(value))
                atoms.append(Atom(*cmps))

        return atoms

    @classmethod
    def to_file(cls, atoms: Iterable[Atom], path: str | os.PathLike) -> None:
        path = pathlib.Path(path)
        header = path.name[:-len(path.suffix)]
        data = {f"data_{header}": cls._atoms_to_dict(atoms)}
        cls._write_from_dict(data, path)

    @staticmethod
    def _split_line(line: str) -> list[str]:

        """Splits line by whitespace, except within single or double quote marks.

        >>> ln = "foo 'hello world'\tbar"
        >>> assert CIFFormat._split_line(ln) == ["foo", "hello world", "bar"]
        """

        words = []
        buffer = ''

        dquote = False
        squote = False

        for char in line:
            if char == '"':
                dquote = not dquote
                continue
            elif char == "'":
                if not dquote:
                    squote = not squote
                    continue
            if char in (" ", "\t"):
                if not buffer:
                    continue
                if not (dquote or squote):
                    words.append(buffer)
                    buffer = ''
                    continue
            buffer += char
        if buffer:
            words.append(buffer)

        return words

    @classmethod
    def _extract_data(cls, path: str | os.PathLike, categories: None | Iterable[str] = None) -> dict:

        """Reads the information from a cif file into a dict. Optionally only extract categories with given names."""

        with open(path, "r") as file:
            lines = (ln.rstrip() for ln in file.readlines())

        all_data = defaultdict(dict)
        block = None
        in_table = False
        in_text_block = False
        cat = None
        field = None
        buffer = []
        num_cols = 0

        for line in lines:
            if line.startswith("data_"):
                block = all_data[line]

            if in_text_block and line[0] in "#_":
                raise ValueError(f"Unexpected end of text block on line:\n{line}")

            if line.startswith("#"):
                in_table = False

            elif line.startswith("loop_"):
                in_table = True

            elif line.startswith("_"):
                # This line declares either a data item, or a table field.
                parts = cls._split_line(line)
                cat, field = parts[0].split(".")
                num_parts = len(parts)
                # If 'categories' arg has been given, and this label's category isn't in it, skip the item / table.
                if categories and cat not in categories:
                    in_table = False
                elif in_table:
                    block.setdefault(cat, dict())[field] = []
                    num_cols = len(block[cat])
                # Otherwise, treat as a data item
                elif num_parts == 2:
                    block.setdefault(cat, dict())[field] = parts[1]
                elif num_parts > 2:
                    raise ValueError(f"Too many data items on line, expected 2 or fewer:\n{line}")

            # Skip text block lines and table rows if last declared category not selected for extraction
            elif categories and cat not in categories:
                continue

            elif line.startswith(";"):
                # This line is the beginning or end of a text block.
                # Tell the difference by checking if lines have been accumulated.
                if buffer:
                    item = "".join(buffer)
                    block.setdefault(cat, dict())[field] = item
                    in_text_block = False
                    buffer = []
                else:
                    buffer.append(line.lstrip(";").strip())
                    in_text_block = True

            elif in_table:
                buffer += cls._split_line(line)
                if len(buffer) < num_cols:
                    # Table rows can run over multiple lines. If the number of values is less
                    # than the number of fields, roll them over to the next line.
                    continue
                for field, value in zip(block[cat], buffer, strict=True):
                    block[cat][field].append(value)
                buffer = []

            elif in_text_block:
                buffer.append(line)

        return all_data

    @classmethod
    def _get_item_by_value(cls, category_data: dict[str, list | str], field: str, value: str) -> dict:

        """Returns the data from a category where the field matches the given value. For tables, expects exactly one
        matching row."""

        try:
            item = category_data[field]
        except KeyError:
            raise ValueError(f"Category has no field called '{field}'")
        value = str(value)

        if isinstance(item, list):
            # Item is a column in a table
            row_count = item.count(value)
            if row_count > 1:
                raise ValueError(f"More than one row with {field} == {value}.")
            try:
                row_num = item.index(value)
            except ValueError:
                raise ValueError(f"No row with {field} == {value}.")
            return {k: v[row_num] for k, v in category_data.items()}

        elif isinstance(item, str):
            # Item is a single value
            if item != value:
                raise ValueError(f"Category field {field} is {item}, not {value}")
            return category_data

    @classmethod
    def _atoms_to_dict(cls, atoms: Iterable[Atom]) -> dict:

        data = {"_atom_site": {}}

        for atom in atoms:

            if not atom.implements(cls.recipe):
                raise ValueError(f"Cannot convert atom to CIF format:\n{atom}")

            for field, asp in cls._asp_map.items():
                if atom.implements(asp):
                    value = atom.get(asp)
                elif field == "group_PDB":
                    value = "ATOM" if atom.resname in AA_RES_TO_SYM else "HETATM"
                else:
                    value = '?'
                data["_atom_site"].setdefault(field, []).append(str(value))

        return data

    @classmethod
    def _write_from_dict(cls, data: dict, path: str | os.PathLike) -> None:

        lines = []

        for header, dataset in data.items():
            lines.extend([header, "#"])

            for category in dataset:
                fields = dataset[category]
                labels = [category + "." + f for f in fields]

                if all(isinstance(v, str) for v in fields.values()):
                    # This category contains single label:value pairs
                    col_width = max(map(len, labels)) + COLUMN_PADDING
                    for item, value in fields.items():
                        label = category + "." + item
                        if col_width + len(value) > WRAP_AT:
                            lines.extend([label] + cls._value_into_text_block(value, WRAP_AT))
                        else:
                            formatted = "'" + value + "'" if " " in value or "'" in value else value
                            lines.append(f"{label: <{col_width}}{formatted}")

                elif all(isinstance(v, list) for v in fields.values()):
                    # This category is a table
                    lines.append("loop_")
                    columns = []
                    widths = []
                    for item, values in dataset[category].items():
                        label = category + "." + item
                        lines.append(label)
                        col = []
                        max_width = 0
                        for v in values:
                            # Surround strings containing spaces with quotes
                            formatted = '"' + v + '"' if " " in v or "'" in v else v
                            col.append(formatted)
                            max_width = max(max_width, len(formatted))
                        widths.append(max_width)
                        columns.append(col)

                    for row in zip(*columns):
                        line = ""
                        for width, value in zip(widths, row):
                            padded = f"{value: <{width + COLUMN_PADDING}}"
                            if len(line) + len(padded) > WRAP_AT:
                                lines.append(line.rstrip())
                                line = padded
                            else:
                                line += padded
                        lines.append(line.rstrip())

                else:
                    raise ValueError(f"Unexpected field value types. Must be <str> or <list>.")
                lines.append("#")

        with open(path, "w") as file:
            file.write("\n".join(lines))

    @staticmethod
    def _value_into_text_block(value: str, wrap_at) -> list[str]:

        """Wraps string value into a text block of width 'wrap_at', ensuring to never
        end a line with whitespace. Leading and tailing whitespace is ignored."""

        value = value.strip()
        whitespace = {" ", "\t"}
        text_block_lines = []
        start = 0
        break_ = 0
        i = 0

        while i < len(value):
            if i-start == wrap_at:
                if start == break_:
                    raise ValueError("Line is only whitespace")
                # Increment break_ by 1 so that slicing includes the non-whitespace character it stopped at
                break_ = break_+1
                text_block_lines.append(value[start:break_])
                i = break_
                start = break_
            if value[i] not in whitespace:
                # Track the position of the last non-whitespace character
                break_ = i
            i += 1
        # When cursor reaches the end, add the final set of characters
        text_block_lines.append(value[start:i])

        text_block_lines[0] = ";" + text_block_lines[0]
        text_block_lines.append(";")
        return text_block_lines

if __name__ == '__main__':
    pass