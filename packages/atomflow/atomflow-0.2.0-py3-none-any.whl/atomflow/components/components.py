from functools import wraps
from weakref import WeakValueDictionary

from atomflow.aspects import *
from atomflow.knowledge import *

def aspects(*asp: Aspect | tuple[Aspect]):

    """
    Verify that a component implements aspects, then attach them to it.

    :param asp:
    :return:
    """

    def deco(cls: Component):
        props = cls.get_property_names()
        if missing := [a.name for a in asp if a.name not in props]:
            raise Exception(f"{cls.__name__} does not implement properties: {', '.join(missing)}")
        cls.aspects = asp
        return cls
    return deco


def cache_instances(cls):

    """
    Store unique instances of the class in a cache. If the same arguments are passed to
    the constructor again, return the stored instance.

    :param cls:
    :return:
    """

    cache = WeakValueDictionary()
    ori_new = cls.__new__

    @wraps(ori_new)
    def new(cls, *args, **kwargs):
        key = (args, tuple(sorted(kwargs.items())))
        if inst := cache.get(key):
            return inst
        else:
            inst = ori_new(cls)
            cache[key] = inst
        return inst

    cls.__new__ = new
    return cls


class Component:

    """
    Holds data relating to atoms. Defined by the aspects it explicitly implements.
    """

    aspects = ()

    def __repr__(self):
        values = ", ".join([f"{p}={getattr(self, p)}" for p in self.get_property_names()])
        return f"{self.__class__.__name__}({values})"

    def __eq__(self, other):
        return str(self) == str(other)

    def __lt__(self, other):
        return str(self) < str(other)

    @classmethod
    def get_property_names(cls) -> list[str]:
        return [name for name, p in vars(cls).items() if isinstance(p, property)]


@cache_instances
@aspects(ResNameAspect, ResOLCAspect, ResTLCAspect, PolymerAspect)
class AAResidueComponent(Component):

    def __init__(self, res):
        res = str(res)
        if olc := AA_RES_TO_SYM.get(res):
            self._tlc = res
            self._olc = olc
        elif tlc := AA_SYM_TO_RES.get(res):
            self._tlc = tlc
            self._olc = res
        else:
            raise ValueError(f"Unrecognised amino acid residue code '{res}'.")

    @property
    def res_olc(self) -> str:
        return self._olc

    @property
    def res_tlc(self) -> str:
        return self._tlc

    @property
    def resname(self) -> str:
        return self._tlc

    @property
    def polymer(self) -> str:
        return "protein"


@cache_instances
@aspects(AltLocAspect)
class AltLocComponent(Component):

    def __init__(self, altloc):
        self._altloc = str(altloc)

    @property
    def altloc(self) -> str:
        return self._altloc


@cache_instances
@aspects(ChainAspect)
class ChainComponent(Component):

    def __init__(self, chain):
        self._chain = str(chain)

    @property
    def chain(self) -> str:
        return self._chain


@aspects(CoordXAspect)
class CoordXComponent(Component):

    def __init__(self, x):
        self._x = float(x)

    @property
    def x(self) -> float:
        return self._x


@aspects(CoordYAspect)
class CoordYComponent(Component):

    def __init__(self, y):
        self._y = float(y)

    @property
    def y(self) -> float:
        return self._y


@aspects(CoordZAspect)
class CoordZComponent(Component):

    def __init__(self, z):
        self._z = float(z)

    @property
    def z(self) -> float:
        return self._z


@cache_instances
@aspects(ResNameAspect, ResOLCAspect, PolymerAspect)
class DNAResidueComponent(Component):

    def __init__(self, res):
        res = str(res)
        if olc := DNA_RES_TO_SYM.get(res):
            self._olc = olc
            self._resname = res
        elif resname := DNA_SYM_TO_RES.get(res):
            self._olc = res
            self._resname = resname
        else:
            raise ValueError(f"Unrecognised DNA residue code '{res}'.")

    @property
    def res_olc(self) -> str:
        return self._olc

    @property
    def resname(self) -> str:
        return self._resname

    @property
    def polymer(self) -> str:
        return "dna"


@cache_instances
@aspects(ElementAspect)
class ElementComponent(Component):

    def __init__(self, element):
        self._element = str(element)

    @property
    def element(self) -> str:
        return self._element


@cache_instances
@aspects(EntityAspect)
class EntityComponent(Component):

    def __init__(self, entity):
        self._entity = str(entity)

    @property
    def entity(self) -> str:
        return self._entity


@cache_instances
@aspects(FormalChargeAspect)
class FormalChargeComponent(Component):

    def __init__(self, fcharge):
        self._fcharge = str(fcharge)

    @property
    def fcharge(self) -> str:
        return self._fcharge


@cache_instances
@aspects(IndexAspect)
class IndexComponent(Component):

    def __init__(self, index):
        self._index = int(index)

    @property
    def index(self) -> int:
        return self._index


@cache_instances
@aspects(InsertionAspect)
class InsertionComponent(Component):

    def __init__(self, insertion):
        self._insertion = str(insertion)

    @property
    def insertion(self) -> str:
        return self._insertion


@cache_instances
@aspects(NameAspect)
class NameComponent(Component):

    def __init__(self, name):
        self._name = str(name)

    @property
    def name(self) -> str:
        return self._name


@cache_instances
@aspects(OccupancyAspect)
class OccupancyComponent(Component):

    def __init__(self, occupancy):
        self._occupancy = float(occupancy)

    @property
    def occupancy(self) -> float:
        return self._occupancy


@cache_instances
@aspects(PolymerAspect)
class PolymerComponent(Component):

    def __init__(self, polymer):
        self._polymer = str(polymer)

    @property
    def polymer(self) -> str:
        return self._polymer

@cache_instances
@aspects(PositionAspect)
class PositionComponent(Component):

    def __init__(self, position):
        self._position = str(position)

    @property
    def position(self) -> str:
        return self._position


@cache_instances
@aspects(ResNameAspect)
class ResidueComponent(Component):

    def __init__(self, resname):
        self._resname = str(resname)

    @property
    def resname(self) -> str:
        return self._resname


@cache_instances
@aspects(ResIndexAspect)
class ResIndexComponent(Component):

    def __init__(self, resindex):
        self._resindex = int(resindex)

    @property
    def resindex(self) -> int:
        return self._resindex


@cache_instances
@aspects(ResNameAspect, ResOLCAspect, PolymerAspect)
class RNAResidueComponent(Component):

    def __init__(self, res):
        res = str(res)
        if res in RNA_RES_CODES:
            self._resname = res
        else:
            raise ValueError(f"Unrecognised RNA residue code '{res}'.")

    @property
    def resname(self) -> str:
        return self._resname

    @property
    def res_olc(self) -> str:
        return self._resname

    @property
    def polymer(self) -> str:
        return "rna"

@cache_instances
@aspects(SectionAspect)
class SectionComponent(Component):

    def __init__(self, section):
        self._section = str(section)

    @property
    def section(self) -> str:
        return self._section

@cache_instances
@aspects(TemperatureFactorAspect)
class TemperatureFactorComponent(Component):

    def __init__(self, temp_f):
        self._temp_f = float(temp_f)

    @property
    def temp_f(self) -> float:
        return self._temp_f


if __name__ == '__main__':
    pass