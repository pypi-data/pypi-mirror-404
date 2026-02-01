## Atomflow

### Installation

```commandline
pip install atomflow
```

### Overview

Atomflow is a library for manipulating protein sequence and structure information. The
specific goal of this project is to make assembling pipelines feel intuitive, centering on 
operator chains that run from source to output. For example, removing water from a structure file 
then splitting its chains into separate files can be achieved with:

```python
import atomflow as af

af.read("5DZU.pdb")\
    .filter("resname", none_of=["HOH"])\
    .sort("chain")\
    .group_by("chain")\
    .write("5dzu_out.pdb")
```

Atom data read from `.pdb` files can also be written to `.fasta` format.
```python
import atomflow as af

af.read("7B9H.pdb").collect().write("7b9h.fasta")
```

The project is currently in an early stage of development, with an aim to expand the interface 
with new capabilities and file formats in the near future.