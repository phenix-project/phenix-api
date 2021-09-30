# vim: set expandtab ts=4 sw=4:

from chimerax.core.commands import (
    CmdDesc, StringArg, IntArg, BoolArg, FloatArg, Float3Arg,
)
from chimerax.atomic import (
    AtomicStructure, AtomicStructuresArg,
    AtomsArg, ResiduesArg,
)
from chimerax.map import MapArg
from chimerax.core.errors import UserError

from chimerax.atomic import (
    AtomicStructure, AtomicStructuresArg,
    AtomsArg, ResiduesArg,
)
from chimerax.std_commands import clip
from chimerax.core.commands import run

import rdkit
from rdkit import Chem
from rdkit.Chem import rdDistGeom
from rdkit.Chem import AllChem
from rdkit.Chem import rdMolAlign

import tempfile
import json
import copy
from math import ceil, log10
import Pyro4
import Pyro4.naming

import Pyro5
import Pyro5.client
import Pyro5.api

PYRO_VERSION = 4 # hardcoded for now


def phenix_connect(session,debug=False,uri=None):
    ''' Start the ISOLDE GUI '''
    if not session.ui.is_gui:
        session.logger.warning("Sorry, ISOLDE currently requires ChimeraX to be in GUI mode")
        return
    from .tool import  PhenixClientTool
    from chimerax.core import tools
    tools.get_singleton(session, PhenixClientTool, 'Phenix', create=True,uri=uri)
    if hasattr(session,"phenix_client"):
        settings = {"debug":debug}
        session.phenix_client.tool.settings.update(settings)
        session.phenix_client.settings.update(settings)
        return session.phenix_client



phenix_connect_desc=CmdDesc(
    synopsis="Initialise the connection to Phenix command server",
    keyword=[("debug",BoolArg),
             ("uri",StringArg)]
)

def phenix_disconnect(session):
    if not hasattr(session,"phenix_client"):
        session.logger.warning("Sorry, Phenix is not connected")
        return
    else:
        session.logger.info("Disconnecting Phenix.")
        session.phenix_client.tool.delete()


phenix_disconnect_desc=CmdDesc(
    synopsis="Disconnect the connection to Phenix command server",
    keyword=[])