from bluer_ai.help.generic import help_functions as generic_help_functions

from bluer_ugv import ALIAS
from bluer_ugv.help.get import help_get
from bluer_ugv.help.git import help_git
from bluer_ugv.help.ssh import help_ssh
from bluer_ugv.help.swallow import help_functions as help_swallow
from bluer_ugv.help.watch import help_watch


help_functions = generic_help_functions(plugin_name=ALIAS)

help_functions.update(
    {
        "get": help_get,
        "git": help_git,
        "ssh": help_ssh,
        "swallow": help_swallow,
        "watch": help_watch,
    }
)
