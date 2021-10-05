import tempfile
import mrcfile
from chimerax.std_commands import clip
from chimerax.core.commands import run
from chimerax.geometry import Place

from .pyro_utils import  find_server, detect_server_version

import numpy as np
from sklearn.neighbors import KDTree
from collections import defaultdict


#TODO: depictions are only modified on new model additions
#TODO: Removing models is not implemented
#TODO: Sourcing models from all the options in the api not implemented
#TODO: Refresh after changing model composition not implemented


class PhenixClient():
  """
  Connects to a Phenix Pyro server, monitors the server.current_scene attribute.
  If the server.current_scene is different from the client.current_scene,
  the scene is updated.

  """
  def __init__(self,tool,uri=None):

    # Chimerax initialization
    self.tool = tool
    self.settings = defaultdict(None)
    session = tool.session
    session.phenix_client = self
    self.session = session

    # connection properties
    self.pyro_version = detect_server_version()
    self.update_freq = 10
    self.elapsed_frames = 0
    self.failed_connections = 0
    self.max_failed_connects = 5
    self.current_scene = {"id":-1}
    self.server, self.server_name, self.server_uri, failed = find_server(uri=uri,
                                                                         PYRO_VERSION=self.pyro_version)
    if failed:
      session.logger.warning("Unable to connect to Phenix.")
      self._on_close()
      del self
    else:
      """
      Currently, the client works by pinging the server in multiples of new_frame
      triggers. Tristan pointed out that there is a better way to do this, 
      but it works for now.
      """
      ts = self.session.triggers
      h_new_frame = ts.add_handler('new frame', self.server_update)
      self.handlers = [h_new_frame]

      # data cache and dictionary to map api id to Chimera model d
      self.data = {}
      self.model_id_mapper = {}

      # hard_coded initial defaults
      run(self.session,"set bgColor white",log=False)
      run(self.session,"lighting full",log=False)

      # properties to delete when changing scene composition (not implemented)
      self.delete_on_refresh = ["_atom_kdtree","_atom_list"]

  @property
  def log(self):
    if "debug" in self.settings and self.settings["debug"] ==True:
      return True
    else:
      return False

  @property
  def atom_list(self):
    if not hasattr(self,"_atom_list"):
      atoms = []
      for model in self.session.models:
        if hasattr(model,"atoms"):
          atoms+=list(model.atoms)
      self._atoms = atoms
    return self._atoms

  @property
  def atom_kdtree(self):
    if not hasattr(self,"_atom_kdtree"):
      xyz = np.vstack([atom.coord for atom in self.atom_list])
      self._atom_kdtree = KDTree(xyz)
    return self._atom_kdtree

  def coord_to_atomspec(self,coord):
    # used for focusing when provided a 3d coordinate so you can focus on nearest residue
    dists,inds = self.atom_kdtree.query(coord,k=1)
    ind = inds.flatten()[0]
    atom = self.atom_list[ind]
    return atom.residue.atomspec

  def server_update(self, trigger, triggerdata):
    # triggered every frame, decides whether or not to update from server
    self.elapsed_frames+=1
    if (
            (self.elapsed_frames <self.update_freq or
            self.elapsed_frames % self.update_freq ==0) and
            self.failed_connections<self.max_failed_connects
      ):
      #self.session.logger.info("New frame:"+str(self.elapsed_frames+=))
      if "debug" in self.settings and self.settings["debug"] !=True:
        try:
          self.update()
        except:
          self.session.logger.warning(
            "Unable to update scene. Likely the connection to Phenix was lost.")
          self.failed_connections+=1
          self.tool.delete()
      else:
        self.update(log=self.log)


  def update(self,log=False):
    """
    We are going to update the scene from the server.
    1. Check for changes
    2. If changes, check each component of scene and apply changes
    """
    if (
        self.server != None and
        self.server.current_scene != None and
        self.server.current_scene["id"] != self.current_scene["id"]

      ):
        scene = self.server.current_scene
        if log:
          self.session.logger.info("Loading scene:"+scene["id"])

        for data in scene["data"]:
          data_id = data["id"]
          data_type = data["object"]
          data_payload = None
          if data_id in self.data: # check local cache
            pass
          else:
            if self.server.has_data(id=data_id): # check server
              data_payload = self.server.retrieve_data(id=data_id)
            else:
              data_payload = None # server doesn't have the data, an error
          if data_payload is not None:
            if data_type in ["model","map"]:
              self.add_model(data_payload,log=self.log)
              self.data[data_payload["id"]] = data_payload

        if "focus" in scene:
          if "xyz" in scene["focus"]:
            xyz = scene["focus"]["xyz"]
            if xyz is not None and len(xyz) == 3:
              xyz = np.array(xyz)[np.newaxis, :]
              atomspec = self.coord_to_atomspec(xyz)
              run(self.session, "sel " + atomspec, log=False)
              run(self.session, "show sel", log=False)
              run(self.session, "color byhetero",
                  log=False)  # this needs to not be hardcoded
              run(self.session, "view sel", log=False)

        self.current_scene = scene


  def add_model(self,data_payload,log=False):
    """
    1. The update function decided we need to add a new model.
    2. Retrieve the model information either from disk or through the wire, add it
       to ChimeraX via a tempfile intermediate
    """
    self.session.logger.info("Loading model: "+data_payload["name"])
    models = None
    if data_payload["source"]["read_filepath"] is not None:
      read_filepath =data_payload["source"]["read_filepath"]
      models, status_message = self.session.open_command.open_data(
        read_filepath)
    else:
      if data_payload["object"]=="model":
        with tempfile.NamedTemporaryFile(mode="w+t",suffix=data_payload["source"]["filestring"]["suffix"]) as tmp:
          tmp.write(data_payload["source"]["filestring"]["string"])
          tmp.seek(0)
          models, status_message = self.session.open_command.open_data(
            tmp.name)
      # map data from list is under construction.
      # elif data_payload["object"]=="map":
      #   l=data_payload["source"]["list"]["list_rep"]
      #   shape = data_payload["data"][1]['source']["list"]["shape"]
      #   a = np.array(l).reshape(shape).astype("float32")
      #   with tempfile.NamedTemporaryFile("w+t", suffix=".mrc") as tmp:
      #     with mrcfile.new(tmp.name, overwrite=True) as fh:
      #       fh.set_data(a)
      #     models, status_message = self.session.open_command.open_data(tmp.name)
    if models is not None:
      for model in models:
        model.name = data_payload["name"]
      self.session.models.add(models)
      model_id = models[0].id[0]
      self.model_id_mapper[data_payload["id"]] = model_id

      # apply depiction
      if "colors" in data_payload:
        for color in data_payload["colors"]:
          if color["id"] in self.model_id_mapper:
            model_id = self.model_id_mapper[color["id"]]
            color_val = color["color"]
            if color_val is not None:
              command = "color #" + model_id + " " + color_val
              run(self.session, command, log=log)
      if data_payload["object"]=="map":
        run(self.session,"volume #"+str(model_id)+" rmsLevel 2.5",log=False)
        run(self.session,"transparency #"+str(model_id)+" 60",log=False)

  def _on_close(self, *_):
    if hasattr(self, "handlers"):
      for h in self.handlers:
        self.session.triggers.remove_handler(h)
    del self.tool
    delattr(self.session, 'phenix_client')

