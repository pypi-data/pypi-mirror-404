from collections import defaultdict
from operator import itemgetter
import os
import pathlib
import string
from typing import Iterable

from atomflow.atom import Atom
from atomflow.formats import Format
from atomflow.components import *
from atomflow.knowledge import *


class ArbitraryBaseNumber:

    def __init__(self, base, value):
        self._base = base
        self._state = [0]
        self.increment(value)

    def increment(self, addition):
        digit = 0
        while addition:
            if digit == len(self._state):
                self._state.append(-1)
            x = self._state[digit] + addition
            addition, self._state[digit] = divmod(x, self._base)
            digit += 1

    def value(self, ascending=False):
        if ascending:
            return self._state[:]
        else:
            return self._state[::-1]


class ChainIdGenerator:

    def __init__(self):
        self._number = ArbitraryBaseNumber(26, 0)

    def __iter__(self):
        return self

    def __next__(self):
        letters = [string.ascii_uppercase[d] for d in self._number.value()]
        self._number.increment(1)
        return "".join(letters)


class FastaFormat(Format):

    recipe = {
        "and": [
            ResNameAspect,
            ResIndexAspect,
        ],
    }

    extensions = (".fasta", ".faa", ".fna")

    @classmethod
    def read_file(cls, path: str | os.PathLike) -> list[Atom]:

        with open(path, "r") as file:
            lines = reversed([line.strip() for line in file.readlines()])

        atoms = []
        seq_lines = []
        chain_id_gen = ChainIdGenerator()

        for ln in lines:
            if ln.startswith(">"):
                seq = "".join(seq_lines)

                # Determine symbol:residue name mapping from the sequence
                symbol_set = set(seq)

                if not symbol_set - DNA_ONE_LETTER_CODES:
                    name_mapping = DNA_SYM_TO_RES
                elif not symbol_set - RNA_RES_CODES:
                    name_mapping = RNA_SYM_TO_RES
                elif not symbol_set - AA_ONE_LETTER_CODES:
                    name_mapping = AA_SYM_TO_RES
                else:
                    sequence_rep = seq if len(seq) <= 20 else f"{seq[:10]}...{seq[-10:]}"
                    raise ValueError(f"Could not interpet residue codes of sequence: \n{sequence_rep}")

                # Convert sequence into atoms
                new_atms = []
                chain = ChainComponent(next(chain_id_gen))
                for i, res in enumerate(seq):
                    resn = ResidueComponent(name_mapping[res])
                    resi = ResIndexComponent(i+1)
                    new_atms.append(Atom(resn, resi, chain))
                atoms = new_atms + atoms
                seq_lines = []
            else:
                seq_lines.insert(0, ln)

        return atoms


    @classmethod
    def to_file(cls, atoms: Iterable[Atom], path: str | os.PathLike) -> None:

        path = pathlib.Path(path)
        stem = path.name[:-len(path.suffix)]

        residue_sets = defaultdict(set)

        for atom in atoms:
            if not atom.implements(cls.recipe):
                continue
            header = stem + "_" + atom.chain if atom.implements(ChainAspect) else stem
            residue_sets[header].add((atom.resindex, atom.resname))

        # Assemble residue codes into sequences, and collect unique sequences by entity
        seqs = {}
        for header, residues in residue_sets.items():

            name_set = {name for index, name in residues}

            if not name_set - DNA_TWO_LETTER_CODES:
                symbol_mapping = DNA_RES_TO_SYM
            elif not name_set - RNA_RES_CODES:
                symbol_mapping = RNA_SYM_TO_RES
            elif not name_set - AA_THREE_LETTER_CODES:
                symbol_mapping = AA_RES_TO_SYM
            else:
                sequence_rep = residues if len(residues) <= 20 else f"{residues[:10]}...{residues[-10:]}"
                raise ValueError(f"Could not interpet residue names of sequence: \n{sequence_rep}")

            seq = "".join([symbol_mapping[r] for _, r in sorted(residues, key=itemgetter(0))])
            if seq in seqs:
                continue
            seqs[seq] = header

        # Write out all sequences to one file
        with open(path, "w") as file:
            file.writelines([f">{header}\n{seq}\n" for seq, header in seqs.items()])


if __name__ == '__main__':
    pass