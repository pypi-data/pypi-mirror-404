AA_RES_TO_SYM = {
    "ALA": "A", "CYS": "C", "ASP": "D", "GLU": "E", "PHE": "F",
    "GLY": "G", "HIS": "H", "ILE": "I", "LYS": "K", "LEU": "L",
    "MET": "M", "ASN": "N", "PRO": "P", "GLN": "Q", "ARG": "R",
    "SER": "S", "THR": "T", "VAL": "V", "TRP": "W", "TYR": "Y",
    "UNK": "X", "SEC": "U", "PYL": "O", "ASX": "B", "GLX": "Z"
}

AA_THREE_LETTER_CODES = set(AA_RES_TO_SYM)

AA_SYM_TO_RES = {v: k for k, v in AA_RES_TO_SYM.items()}

AA_ONE_LETTER_CODES = set(AA_SYM_TO_RES)

DAA_RES_CODES = {
    "DAL", "DAR", "DSG", "DAS", "DCY",
    "DGN", "DGL", "DHI", "DIL", "DLE",
    "DLY", "MED", "DPN", "DPR", "DSN",
    "DTH", "DTR", "DTY", "DVA"
}

DNA_RES_TO_SYM = {
    "DA": "A", "DG": "G", "DT": "T", "DC": "C"
}

DNA_TWO_LETTER_CODES = set(DNA_RES_TO_SYM)

DNA_SYM_TO_RES = {v: k for k, v in DNA_RES_TO_SYM.items()}

DNA_ONE_LETTER_CODES = set(DNA_SYM_TO_RES)

RNA_SYM_TO_RES = {"A": "A", "G": "G", "U": "U", "C": "C"}

RNA_RES_CODES = set(RNA_SYM_TO_RES)

POLYMER_CODE_SETS = {
    "polypeptide(L)": AA_THREE_LETTER_CODES,
    "polypeptide(D)": DAA_RES_CODES,
    "polydeoxyribonucleotide": DNA_TWO_LETTER_CODES,
    "polyribonucleotide": RNA_RES_CODES,
}

POLYMER_RESIDUE_CODES = set([code for group in POLYMER_CODE_SETS.values() for code in group])