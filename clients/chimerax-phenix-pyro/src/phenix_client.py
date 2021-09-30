import tempfile
import mrcfile
from chimerax.std_commands import clip
from chimerax.core.commands import run
from chimerax.geometry import Place

import Pyro5
import Pyro5.client
import Pyro5.api

import Pyro4
import Pyro4.naming

import numpy as np
from sklearn.neighbors import KDTree
from collections import defaultdict

class PhenixClient():
  def __init__(self,tool,uri=None):
    self.tool = tool
    self.settings = defaultdict(None)
    session = tool.session
    session.logger.info("Initializing Client")
    session.phenix_client = self
    self.session = session
    self.update_freq = 100
    self.elapsed_frames = 0
    self.current_scene = {"id":-1}
    self.server, failed = self.get_scene_server(uri=uri)
    if failed:
      session.logger.warning("Unable to connect to Phenix.")
      self._on_close()
      del self
    else:
      pass
      ts = self.session.triggers
      h_new_frame = ts.add_handler('new frame', self.server_update)
      self.handlers = [h_new_frame]
      self.data = {}
      self.model_id_mapper = {}
      run(self.session,"set bgColor white")
      run(self.session,"lighting full")


      self.delete_on_refresh = ["_atom_kdtree","_atom_list"]
    #run(self.session,'ui mousemode right "contour level"',log=True)

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
    self.elapsed_frames+=1
    if self.elapsed_frames <self.update_freq or self.elapsed_frames % self.update_freq ==0:
      #self.session.logger.info("New frame:"+str(self.elapsed_frames+=))
      if "debug" in self.settings and self.settings["debug"] !=True:
        try:
          self.update()
        except:
          self.session.logger.warning(
            "Unable to update scene. Likely the connection to Phenix was lost.")
          self.tool.delete()
      else:
        self.update(log=self.log)
  def add_model(self,data_payload,log=False):
    if self.server.current_scene["id"] != self.current_scene["id"]:
      if data_payload["source"]["read_filepath"] is not None:
        read_filepath =data_payload["source"]["read_filepath"]
        models, status_message = self.session.open_command.open_data(
          read_filepath)
      # else:
      #   if data_payload["object"]=="model":
      #     with tempfile.NamedTemporaryFile(mode="w+t",suffix=data_payload["source"]["filestring"]["suffix"]) as tmp:
      #       tmp.write(data_payload["source"]["filestring"]["string"])
      #       tmp.seek(0)
      #       models, status_message = self.session.open_command.open_data(
      #         tmp.name)
      #   elif data_payload["object"]=="map":
      #     l=data_payload["source"]["list"]["list_rep"]
      #     shape = data_payload["data"][1]['source']["list"]["shape"]
      #     a = np.array(l).reshape(shape).astype("float32")
      #     with tempfile.NamedTemporaryFile("w+t", suffix=".mrc") as tmp:
      #       with mrcfile.new(tmp.name, overwrite=True) as fh:
      #         fh.set_data(a)
      #       models, status_message = self.session.open_command.open_data(tmp.name)

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
      run(self.session,"volume #"+str(model_id)+" rmsLevel 2.5")
      run(self.session,"transparency #"+str(model_id)+" 60")



  def update(self,log=False):
    if self.current_scene != None:
      if self.server.current_scene["id"] != self.current_scene["id"]:

        if self.server.has_data() == False:
          self.session.logger.info("Empty scene")
        else:
          scene = self.server.current_scene
          self.session.logger.info("Loading scene:"+scene["id"])


          for data_payload in scene["data"]:
            if data_payload["id"] not in self.data:
              if data_payload["object"] in ["model","map"]:
                self.add_model(data_payload,log=self.log)
                self.data[data_payload["id"]] = data_payload

          if "focus" in scene:
            if "xyz" in scene["focus"]:
              xyz = scene["focus"]["xyz"]
              if xyz is not None and len(xyz) == 3:
                xyz = np.array(xyz)[np.newaxis, :]
                atomspec = self.coord_to_atomspec(xyz)
                run(self.session, "sel " + atomspec, log=log)
                run(self.session, "show sel", log=log)
                run(self.session, "color byhetero",
                    log=log)  # this needs an option.
                run(self.session, "view sel", log=log)

          self.current_scene = scene


  def get_scene_server(self,uri=None):
    failed = False
    server = None
    if uri is None:
      servers = []
      with Pyro4.naming.locateNS() as ns:
        for server, server_uri in ns.list(prefix="phenix").items():
          print("server:", server)
          servers.append(Pyro4.Proxy(server_uri))
      server = servers[0]
    else:
      server= Pyro4.Proxy(uri)

    return server,failed


  def _on_close(self, *_):
    if hasattr(self,"handlers"):
      for h in self.handlers:
        self.session.triggers.remove_handler(h)
    del self.tool
    delattr(self.session, 'phenix_client')
