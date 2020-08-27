"""Constants and Enums"""


# Standard Library
# cSpell:disable
import enum


class EntityTypesEnum(str, enum.Enum):
    """Namespace Entity types"""

    Abundance = "Abundance"
    Protein = "Protein"
    RNA = "RNA"
    Micro_RNA = "Micro_RNA"
    Gene = "Gene"
    Complex = "Complex"
    BiologicalProcess = "BiologicalProcess"
    Pathology = "Pathology"
    Activity = "Activity"
    Variant = "Variant"
    ProteinModification = "ProteinModification"
    AminoAcid = "AminoAcid"
    Location = "Location"
    Species = "Species"
    All = "All"


class AnnotationTypesEnum(str, enum.Enum):
    """Namespace entity annotation types"""

    Anatomy = "Anatomy"
    Cell = "Cell"
    CellLine = "CellLine"
    CellStructure = "CellStructure"
    Disease = "Disease"
    Species = "Species"
    All = "All"


# Used for validation of pmod()
AminoAcid = [
    "Alanine",
    "Ala",
    "A",
    "Arginine",
    "Arg",
    "R",
    "Asparagine",
    "Asn",
    "N",
    "Aspartic Acid",
    "Asp",
    "D",
    "Cysteine",
    "Cys",
    "C",
    "Glutamic Acid",
    "Glu",
    "E",
    "Glutamine",
    "Gln",
    "Q",
    "Glycine",
    "Gly",
    "G",
    "Histidine",
    "His",
    "H",
    "Isoleucine",
    "Ile",
    "I",
    "Leucine",
    "Leu",
    "L",
    "Lysine",
    "Lys",
    "K",
    "Methionine",
    "Met",
    "M",
    "Phenylalanine",
    "Phe",
    "F",
    "Proline",
    "Pro",
    "P",
    "Serine",
    "Ser",
    "S",
    "Threonine",
    "Thr",
    "T",
    "Tryptophan",
    "Trp",
    "W",
    "Tyrosine",
    "Tyr",
    "Y",
    "Valine",
    "Val",
    "V",
]

AminoAcidCompletion = {
    "Alanine": "Ala",
    "Ala": "Ala",
    "Arginine": "Arg",
    "Arg": "Arg",
    "Asparagine": "Asn",
	"Asn": "Asn",
    "Aspartic Acid": "Asp",
	"Asp": "Asp",
    "Cysteine": "Cys",
	"Cys": "Cys",
    "Glutamic Acid": "Glu",
	"Glu": "Glu",
    "Glutamine": "Gln",
	"Gln": "Gln",
    "Glycine": "Gly",
	"Gly": "Gly",
    "Histidine": "His",
	"His": "His",
    "Isoleucine": "Ile",
	"Ile": "Ile",
    "Leucine": "Leu",
	"Leu": "Leu",
    "Lysine": "Lys",
	"Lys": "Lys",
    "Methionine": "Met",
	"Met": "Met",
    "Phenylalanine": "Phe",
	"Phe": "Phe",
    "Proline": "Pro",
	"Pro": "Pro",
    "Serine": "Ser",
	"Ser": "Ser",
    "Threonine": "Thr",
	"Thr": "Thr",
    "Tryptophan": "Trp",
	"Trp": "Trp",
    "Tyrosine": "Tyr",
	"Tyr": "Tyr",
    "Valine": "Val",
	"Val": "Val",
}


# Used for validation of ma()
Activity = [
    "catalyticActivity",
    "cat",
    "chaperoneActivity",
    "chap",
    "gtpBoundActivity",
    "gtp",
    "kinaseActivity",
    "kin",
    "molecularActivity",
    "act",
    "peptidaseActivity",
    "pep",
    "phosphataseActivity",
    "phos",
    "ribosylationActivity",
    "ribo",
    "transcriptionalActivity",
    "tscript",
    "transportActivity",
    "tport",
]

ActivityCompletion = {
    "catalyticActivity": "cat",
	"cat": "cat",
    "chaperoneActivity": "chap",
	"chap": "chap",
    "gtpBoundActivity": "gtp",
	"gtp": "gtp",
    "kinaseActivity": "kin",
	"kin": "kin",
    "molecularActivity": "act",
	"act": "act",
    "peptidaseActivity": "pep",
	"pep": "pep",
    "phosphataseActivity": "phos",
	"phos": "phos",
    "ribosylationActivity": "ribo",
	"ribo": "ribo",
    "transcriptionalActivity": "tscript",
	"tscript": "tscript",
    "transportActivity": "tport",
	"tport": "tport",
}

# Used for validation of pmod()
ProteinModification = [
    "acetylation",
    "Ac",
    "ADP-ribosylation",
    "ADPRib",
    "farnesylation",
    "Farn",
    "geranylgeranylation",
    "Gerger",
    "glycosylation",
    "Glyco",
    "hydroxylation",
    "Hy",
    "ISG15-protein conjugation",
    "ISG",
    "methylation",
    "Me",
    "mono-methylation",
    "Me1",
    "di-methylation",
    "Me2",
    "tri-methylation",
    "Me3",
    "myristoylation",
    "Myr",
    "neddylation",
    "Nedd",
    "N-linked glycosylation",
    "NGlyco",
    "Nitrosylation",
    "NO",
    "O-linked glycosylation",
    "OGlyco",
    "palmitoylation",
    "Palm",
    "phosphorylation",
    "Ph",
    "sulfonation",
    "Sulf",
    "SUMOylation",
    "Sumo",
    "ubiquitination",
    "Ub",
    "Lysine 48-linked polyubiquitination",
    "UbK48",
    "Lysine 63-linked polyubiquitination",
    "UbK63",
    "mono-ubiquitination",
    "UbMono",
    "poly-ubiquitination",
    "UbPoly",
]

ProteinModificationCompletion = {
    "acetylation": "Ac",
	"Ac": "Ac",
    "ADP-ribosylation": "ADPRib",
	"ADPRib": "ADPRib",
    "farnesylation": "Farn",
	"Farn": "Farn",
    "geranylgeranylation": "Gerger",
	"Gerger": "Gerger",
    "glycosylation": "Glyco",
	"Glyco": "Glyco",
    "hydroxylation": "Hy",
	"Hy": "Hy",
    "ISG15-protein conjugation": "ISG",
	"ISG": "ISG",
    "methylation": "Me",
	"Me": "Me",
    "mono-methylation": "Me1",
	"Me1": "Me1",
    "di-methylation": "Me2",
	"Me2": "Me2",
    "tri-methylation": "Me3",
	"Me3": "Me3",
    "myristoylation": "Myr",
	"Myr": "Myr",
    "neddylation": "Nedd",
	"Nedd": "Nedd",
    "N-linked glycosylation": "NGlyco",
	"NGlyco": "NGlyco",
    "Nitrosylation": "NO",
	"NO": "NO",
    "O-linked glycosylation": "OGlyco",
	"OGlyco": "OGlyco",
    "palmitoylation": "Palm",
	"Palm": "Palm",
    "phosphorylation": "Ph",
	"Ph": "Ph",
    "sulfonation": "Sulf",
	"Sulf": "Sulf",
    "SUMOylation": "Sumo",
	"Sumo": "Sumo",
    "ubiquitination": "Ub",
	"Ub": "Ub",
    "Lysine 48-linked polyubiquitination": "UbK48",
	"UbK48": "UbK48",
    "Lysine 63-linked polyubiquitination": "UbK63",
	"UbK63": "UbK63",
    "mono-ubiquitination": "UbMono",
	"UbMono": "UbMono",
    "poly-ubiquitination": "UbPoly",
	"UbPoly": "UbPoly",
}

strarg_validation_lists = {
    "Activity": Activity,
    "ProteinModification": ProteinModification,
    "AminoAcid": AminoAcid,
}

strarg_completions = {
    "Activity": ActivityCompletion,
    "AminoAcid": AminoAcidCompletion,
    "ProteinModification": ProteinModificationCompletion,
}
