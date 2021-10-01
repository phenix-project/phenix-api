from chimerax.core.tools import ToolInstance
from .phenix_client import PhenixClient
from chimerax.ui import HtmlToolInstance

class PhenixClientTool(ToolInstance):
    SESSION_ENDURING = True
    # if SESSION_ENDURING is True, tool instance not deleted at session closure
    # Is the above desireable?
    def __init__(self, session, tool_name,uri=None):
        ToolInstance.__init__(self, session, tool_name)
        self.settings = {}
        self.phenix_client = PhenixClient(self,uri=uri)




