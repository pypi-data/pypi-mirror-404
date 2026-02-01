from bluer_ai.help.generic import help_functions as generic_help_functions

from bluer_journal import ALIAS
from bluer_journal.help.git import help_functions as help_git
from bluer_journal.help.next import help_next
from bluer_journal.help.open import help_open
from bluer_journal.help.sync import help_sync


help_functions = generic_help_functions(plugin_name=ALIAS)


help_functions.update(
    {
        "git": help_git,
        "open": help_open,
        "next": help_next,
        "sync": help_sync,
    }
)
