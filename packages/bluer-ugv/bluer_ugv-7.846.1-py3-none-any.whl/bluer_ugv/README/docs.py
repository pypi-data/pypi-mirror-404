from bluer_ugv.README.arzhang import docs as arzhang_docs
from bluer_ugv.README.eagle import docs as eagle_docs
from bluer_ugv.README.fire import docs as fire_docs
from bluer_ugv.README.rangin import docs as rangin_docs
from bluer_ugv.README.ravin import docs as ravin_docs
from bluer_ugv.README import (
    aliases,
    beast,
    root,
    releases,
    swallow,
)
from bluer_ugv.README.computer import docs as computer
from bluer_ugv.README.ugvs import docs as ugvs
from bluer_ugv.README.validations import docs as validations

docs = (
    root.docs
    + aliases.docs
    + arzhang_docs.docs
    + beast.docs
    + eagle_docs.docs
    + fire_docs.docs
    + rangin_docs.docs
    + ravin_docs.docs
    + releases.docs
    + computer.docs
    + ugvs.docs
    + swallow.docs
    + validations.docs
)
