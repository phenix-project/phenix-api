# vim: set expandtab ts=4 sw=4:

from chimerax.core.commands import (
    CmdDesc, StringArg, IntArg, BoolArg, FloatArg, Float3Arg)


def phenix_connect(session,debug=False,uri=None):

    from .tool import  PhenixClientTool
    from chimerax.core import tools
    try:
        tools.get_singleton(session, PhenixClientTool, 'Phenix', create=True,uri=uri)
        assert hasattr(session, "phenix_client")
        settings = {"debug":debug}
        session.phenix_client.tool.settings.update(settings)
        session.phenix_client.settings.update(settings)
        return session.phenix_client

    except:
        session.logger.warning("Failed to connect to Phenix.")




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