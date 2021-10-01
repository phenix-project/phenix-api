from uuid import uuid4
import sys
import copy

from mmtbx.model.model import manager as model_manager
from iotbx.map_manager import map_manager
from iotbx.map_model_manager import map_model_manager

if sys.version_info.major == 2:
  from pathlib2 import Path
else:
  from pathlib import Path

"""
Api objects are classes used to convert objects into a standard API representation
Each class has a template with defaults, and accepts a dictionary
upon initialization with customized API values. The payload property returns
a dictionary that can be transmitted as an alternative to the object.


Example: Want the API representation of mmtbx.model.manager object 'model'

payload_init = {"name":"model 1",
                "source":{
                   "read_filepath":"/home/user/Documents/model1.pdb",
                   }
                }
model_api = ModelAPI(model,payload_init=payload_init)
payload = model_api.payload # a dict to send somewhere
"""


class ObjectAPI(object):
  _payload_template = {"id": None,
                       "object": "object"}

  def __init__(self, *args,**kwargs):
    if "payload_init" in kwargs:
      payload_init = kwargs["payload_init"]
    else:
      payload_init = {}
    if len(args) == 0:
      self.obj = None
    elif len(args) == 1:
      self.obj = args[0]

    self.payload_working = payload_init

    if "id" not in self.payload_working:
      self.payload_working["id"] = str(uuid4())

  @property
  def payload(self):
    return self.mergedicts(self.payload_template, self.payload_working)

  @property
  def payload_template(self):
    return copy.deepcopy(self.__class__._payload_template)

  def mergedicts(self, old, new, path=None):
    a, b = old, new
    "merges b into a"
    if path is None: path = []
    for key in b:
      if key in a:
        if isinstance(a[key], dict) and isinstance(b[key], dict):
          self.mergedicts(a[key], b[key], path + [str(key)])
        elif a[key] == b[key]:
          pass  # same leaf value
        else:
          # raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
          a[key] = b[key]
      else:
        a[key] = b[key]
    return a


class ModelAPI(ObjectAPI):
  """
  A class to format a model object into a standard api response

  Usage:
  model_response = ModelResponse(model_object)
  payload = model_response.payload

  """
  _payload_template = {
    "object": "model",
    "name": "model",
    "database": {"pdb": None},
    "source": {
      "read_filepath": None,
      "read_url": None,
      "fetch": None,
      "filestring": {
        "string": None,
        "suffix": ".pdb"
      },
    },
    "destination": {
      "write_filepath": None,
      "suffix": ".mmcif"
    },
  }

  known_suffixes = [".pdb", ".cif", ".mmcif", ".mol"]

  def __init__(self, *args, **kwargs):
    super(ModelAPI, self).__init__(*args, **kwargs)
    if "payload_init" in kwargs:
      payload_init = kwargs["payload_init"]
    else:
      payload_init = {}
    # merge in init values
    self.payload_working = self.mergedicts(self.payload_working,payload_init)

    # deal with the object type
    if self.obj is not None:
      if not isinstance(self.obj, model_manager):
        raise ValueError("Object type not supported")

    # deal with read filepath suffix
    try:
      p = self.payload_working["source"]["read_filepath"]
      self.payload_working["source"]["read_filepath"] = str(p)
      if p is not None:
        p = Path(p)
        suffixes = p.suffixes
        if len(set(suffixes).intersection(set(self.known_suffixes))) == 0:
          raise ValueError("Suffix type not supported:", suffixes)
    except KeyError:
      pass

    # deal with string suffix
    try:
      suffix = self.payload_working["source"]["filestring"]["suffix"]
      suffixes = [suffix, "." + suffix, suffix.strip(".")]
      for s in suffixes:
        if s in self.known_suffixes:
          self.payload_working["source"]["filestring"]["suffix"] = s
          break
      if self.payload_working["source"]["filestring"][
        "suffix"] not in self.known_suffixes:
        raise ValueError("Suffix type not supported:", suffix)
    except KeyError:
      pass

    # merge in default template values
    self.payload_working = self.mergedicts(self.payload_template,
                                           self.payload_working)

    # decide if we need to represent the model as a string
    string_needed = False
    if (
            self.payload_working["source"]["read_filepath"] == None and
            self.payload_working["source"]["read_url"] == None and
            self.payload_working["source"]["fetch"] == None
    ):
      string_needed = True
    if string_needed:
      if self.obj is not None:
        self.payload_working["source"]["filestring"]["string"] = self.str_rep

  @property
  def str_rep(self):
    model_obj = self.obj
    suffix = self.payload_working["source"]["filestring"]["suffix"]
    if isinstance(model_obj, model_manager):
      if suffix in [".cif", ".mmcif"]:
        str_rep = model_obj.model_as_mmcif(do_not_shift_back = True)
      else:
        str_rep = model_obj.model_as_pdb(do_not_shift_back = True)

    return str_rep


class MapAPI(ObjectAPI):
  _payload_template = {
    "object": "map",
    "name": "map",
    "database": {"emdb": None},
    "source": {
      "read_filepath": None,
      "read_url": None,
      "fetch": None,
      "list": {
        "list_rep": None,  # flattened in row-major (C-style) order
        "dtype": "float32",
        "shape": tuple(),
        "pixel_sizes": tuple(),
      },
      "shift_cart": tuple(),
    },
    "destination": {
      "write_filepath": None,
      "suffix": ".mrc"
    },
  }

  known_suffixes = [".ccp4", ".mrc", ".map"]

  def __init__(self, *args,**kwargs):
    super(MapAPI, self).__init__(*args, **kwargs)
    if "payload_init" in kwargs:
      payload_init = kwargs["payload_init"]
    else:
      payload_init = {}
    # merge in initialized values
    self.payload_working = self.mergedicts(self.payload_working,payload_init)


    # deal with the object type
    if self.obj is not None:
      if not isinstance(self.obj, map_manager):
        raise ValueError("Map object type not supported")

    # deal with read filepath suffix
    try:
      p = self.payload_working["source"]["read_filepath"]
      if p is not None:
        p = Path(p)
        suffixes = p.suffixes
        if len(set(suffixes).intersection(set(self.known_suffixes))) == 0:
          raise ValueError("Suffix type not supported:", suffixes)
    except KeyError:
      pass

   # merge in defaults
    self.payload_working = self.mergedicts(self.payload_template,
                                           self.payload_working)
    # decide if we need to represent the map as a list
    list_needed = False
    if (
            self.payload_working["source"]["read_filepath"] == None and
            self.payload_working["source"]["read_url"] == None and
            self.payload_working["source"]["fetch"] == None
    ):
      list_needed = True
    if list_needed:
      if self.obj is not None:
        self.payload_working["source"]["list"]["list_rep"] = self.list_rep
        self.payload_working["source"]["list"][
          "shape"] = self.obj.map_data().all()
        self.payload_working["source"]["list"][
          "pixel_sizes"] = self.obj.pixel_sizes()

  @property
  def list_rep(self):
    map_obj = self.obj
    if isinstance(map_obj, map_manager):
      return list(map_obj.map_data())


class SceneAPI(ObjectAPI):
  _payload_template = {
    "object": "scene",
    "data": [],
    "colors": [],
    "styles": [],
    "focus": {},
    "environment": {}}  # Scene-wide environment settings
  # color templates
  _color_template = {
    "id": None,
    "color": None,
    # the color as either: 1. HTML color code or, 2. a color keyword
    # Color keywords: ["heteroatom"]
    "selection": None}  # Optionally a selection to restrict the color to.

  # style
  _style_template = {
    "id": None,  # the object to apply style to
    "style": None,  # a style keyword, one of : ["ribbon","sphere","stick"]
    "selection": None}

  # focus
  _focus_template = {
    "id": None,  # A model to focus on
    "selection": None,  # Optionally a selection of that model
    "xyz": (0., 0., 0.),  # Alternatively, focus on a point
    "xyz_expand": None}  # Focus on the nearest entity to the xyz point. One of [None,"model","chain","residue","atom"]
  # environment
  # TODO: this needs a lot more attention
  environment_template = {"background_color": "#FFFFFF",
                          "lighting": "full"}

  @classmethod
  def from_copy(cls,payload,payload_init={}):
    scene = cls((),payload_init=payload_init)
    scene_id = scene.payload["id"]
    scene.payload_working = scene.mergedicts(scene.payload_template,payload)
    scene.payload_working["id"] = scene_id
    return scene

  @classmethod
  def from_objects(cls, *objects,**kwargs):
    if "payload_init" in kwargs:
      payload_init = kwargs["payload_init"]
    else:
      payload_init = {}

    maps = []
    models = []
    for obj in objects:
      if isinstance(obj, map_manager):
        maps.append(obj)
      elif isinstance(obj, map_model_manager):
        models.append(obj.model())
        maps.append(obj.map_manager())
      elif isinstance(obj, model_manager):
        models.append(obj)
      else:
        print(
          "ERROR: Only high level CCTBX map/model objects are supported by this function, not",
          type(obj))
    model_api_objects = [ModelAPI(obj) for obj in models]
    map_api_objects = [MapAPI(obj) for obj in maps]
    api_objects = tuple(model_api_objects + map_api_objects)
    return cls.from_api_objects(*api_objects, payload_init=payload_init)

  @classmethod
  def from_api_objects(cls, *api_objects,**kwargs):
    if "payload_init" in kwargs:
      payload_init = kwargs["payload_init"]
    else:
      payload_init = {}

    for api_object in api_objects:
      names = [t.__name__ for t in type(api_object).mro()]
      if "ObjectAPI" not in names:
        raise ValueError("Initialize with API objects, not:",
                         api_object.__class__)

    payloads = (api_object.payload for api_object in api_objects)
    return cls.from_api_payloads(*payloads, payload_init=payload_init)

  @classmethod
  def from_api_payloads(cls, *data_api_payloads, **kwargs):
    if "payload_init" in kwargs:
      payload_init = kwargs["payload_init"]
    else:
      payload_init = {}

    data = ({"id": payload["id"], "object": payload["object"]} for payload in
            data_api_payloads)
    return cls(data, payload_init=payload_init)

  def __init__(self, data, payload_init={},apply_defaults=True):
    # data must be a tuple. py2/3 issues
    super(SceneAPI, self).__init__(None, payload_init={})

    # merge payloads
    self.payload_working = self.mergedicts(self.payload_template,
                                           self.payload_working)
    self.payload_working = self.mergedicts(self.payload_working,
                                           payload_init)

    self.payload_working["data"] += list(data)

    if apply_defaults:
      self.apply_default_colors()

  def add_color(self, object_id, color, selection=""):
    self.payload_working["colors"].append(
      {"id": object_id, "color": color, "selection": selection})

  def apply_default_colors(self):
    preferred_model_colors = set(["#3465A4", "#761c94"])
    model_colors = set()
    for data in self.payload_working["data"]:
      if data["object"] == "model":
        available_colors = preferred_model_colors - model_colors
        if len(available_colors) > 0:
          next_color = list(available_colors)[0]
        else:
          next_color = None
        if next_color is not None:
          self.add_color(data["id"], next_color)

    # # Apply simple server-side defaults
    preferred_map_colors = set(["#B0B0B0", "#3d3a3a", "#6e1710", "#3f8f6f"])
    map_colors = set()
    for data in self.payload_working["data"]:
      if data["object"] == "map":
        available_colors = preferred_map_colors - map_colors
        if len(available_colors) > 0:
          next_color = list(available_colors)[0]
        else:
          next_color = None
        if next_color is not None:
          self.add_color(data["id"], next_color)

  @property
  def objects(self):
    return [payload["uuid"] for payload in self.api_objects]

