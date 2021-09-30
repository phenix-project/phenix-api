import copy
import sys
from uuid import uuid4

from api_objects import SceneAPI

if sys.version_info.major == 2:
  import Pyro4
  import Pyro4.naming
else:
  import Pyro5
  import Pyro5.server
  import Pyro5.nameserver
  import Pyro5.api

class PhenixServer:
  def __init__(self ,*args, **kwargs):
    self.id = str(uuid4())
    # program attributes
    self.tasks = {}
    self.results = {}
    self._current_task = None

    # data attributes
    self.data = {}

    # scene attributes
    self.scenes = {}
    self._current_scene = None

  # program properties/methods
  @property
  def current_task(self):
    return self._current_task

  # data properties/methods
  def retrieve_data(self ,id):
    if id in self.data:
      return self.data[id]

  def add_data(self ,data_payload):
    self.data[data_payload["id"]] = data_payload

  def has_data(self ,id=None):
    if id is None:
      return len(self.data ) >0
    else:
      return id in self.data

  # sscene properties/methods
  @property
  def current_scene(self):
    return self._current_scene

  @current_scene.setter
  def current_scene(self ,scene_payload):
    if scene_payload["id"] not in self.scenes:
      self.add_scene(scene_payload ,set_current=True)
    else:
      self._current_scene = scene_payload


  def retrieve_scene(self ,scene_id):
    if scene_id in self.scenes:
      return self.scenes[scene_id]


  def add_scene(self ,scene_payload ,set_current=True):
    # need to validate payloads
    failed = False
    data_objects = scene_payload["data"]


    scene_id = scene_payload["id"]
    self.scenes[scene_id ] =scene_payload

    for data_object in data_objects:
      if data_object["id"] not in self.data:
        self.data[data_object["id"]] = data_object

    if set_current:
      self._current_scene = self.scenes[scene_id]

  def update_focus(self,focus):
    new_scene = SceneAPI.from_copy(self.current_scene).payload
    new_scene["focus"]=focus
    self.add_scene(new_scene)
    self._current_scene = new_scene

# conditional expose
if sys.version_info.major ==2:
  PhenixServer = Pyro4.expose(PhenixServer)
else:
  PhenixServer= Pyro5.server.expose(PhenixServer)