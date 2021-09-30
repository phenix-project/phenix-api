# Phenix API Documentation

- The goal of this documentation is to define a common interface to run Phenix from multiple frontends (GUIs, notebooks, visualization software, etc.) 
- The reference implementation uses [Pyro](https://pyro5.readthedocs.io/en/latest/), which provides a huge number of features ready to use. Some highlights:
	- Pure Python, requests are executed as method calls
	- Different serializers (serpent, json, marshal, pickle, msgpack)
	- IPv4, IPv6 or Unix domain sockets
	- Optional secure connections via SSL/TLS 
 - The goal is to have clearly defined requests and responses. The [Stripe](https://stripe.com/docs/api) API is a good example of a well documented API. In that API the responses are JSON encoded. Because we are using Pyro, it makes sense for responses to be plain Python dictionaries. Different backend serializers can then be used interchangeably, where JSON would be one option.
 
# Overview
### Request Types
- Program requests: Client wants to run a Phenix program
- Result requests: Client wants the results of a program run
- Scene requests: Client wants to draw a scene
	
### Response Types
 - Program status: Server reports on program progress
 - Result responses: Server provides program results
 - Scene responses: Server defines a particular scene.
 
 ### Data Types
 Whenever possible, the data should be standard Python data types, which are easily serialized by whichever backend being used. However, for more exotic data types, it is necessary to make them an explicit part of the API so that both client and server can anticipate them and know how to encode/decode the data structure. 
 
  - Model file: Molecular structure
  - Map file: 3D volumetric data
  - MTZ file: Crystallographic reflection data
  - Generic text file: Useful for .eff, .phil for example
  - Generic binary file: Useful for flex arrays, numpy arrays, etc
 
# Definitions and Examples
#### Model data
A model api response should include all the information necessary to recreate a model on either endpoint. The simplest way to do this is to use one of the existing molecular file formats, or if applicable, a database retrieval. If the server and client do not share a filesystem, the file contents can be encoded as a string. As an example, we will use the file here: servers/phenix-pyro/tests/1aba_pieces.pdb  
```Python
{
    "id":"8a0bf6f5-f9e1-49ba-91e2-8ef5c67b2911"  # A unique identifier for this model in the Client/Server session
    "object": "model",
    "name": "1aba_pieces",	                 # The name the client should use to display this model
    "database": {"pdb": "1aba"},                 # Database is relevant because this corresponds to a published model. 
    "source": {
      "read_filepath": "servers/phenix-pyro/tests/1aba_pieces.pdb",
      "read_url": None,
      "fetch": None,			         # Fetch is not relevant, because this is a truncated version of the full model
      "filestring": {
        "string": None,
        "suffix": ".pdb"
      },
    },
    "destination": {
      "write_filepath": None,			 # Write filepath is not specified
      "suffix": ".mmcif"
    },
  }

```
#### Map Data
In most cases, the client and server will share a filesystem. So the server should prefer to populate the "read_filepath" attribute and the client should prefer to read files from disk. 

If not sharing a filesystem, most Pyro serializer backends will refuse to encode arbitrary objects for security reasons. Even if doing that explicity, for example:
```Python
import pickle
p = pickle.dumps(complex_obj)
{"response_field":p}
```
...still requires decoding and recreating the complex object on the client side, which is failure prone. Instead, the map data response only serializes the numerical data, and inludes metadata to recreate the map on the client side. The numerical data is encoded as a Python list, with serialization, compression, and encryption left to the backend. 

```Python
{
    "id":None,
    "object": "map",
    "name": "map",
    "database": {"emdb": None},
    "source": {
      "read_filepath": None,
      "read_url": None,
      "fetch": None,
      "list": {
        "list_rep": None, 
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
```

#### MTZ Files
- *TODO*

#### Generic files
```Python
{
"id":None,
"data_type":"text",
"contents":""
}
```


```Python
{
"id":None
"data_type":"binary",
"contents":None #bytes representation, should be a last resort
"serializer":"" # pickle, joblib, msgpack, etc
}
```
##### Scene
A scene is a composition of data objects to display in a client viewer, and optionally information about depiction and focus. For example, the colors field could contain a list of colors to apply to different models, or a list of colors to apply to different selections of a single model. Here a "color" is a dictionary with a predictable format, defined below.

```Python
{
    "id":None,          # A unique identifier of the scene
    "object": "scene",
    "data": [],         # A list of data objects
    "colors": [],       # A list of color specifications
    "styles": [],       # A list of style specifications
    "focus": {},        # A single focus specification
    "environment": {}   # A single environment specification
}
```
#### Color
Color encoded as either: 1. HTML color code or, 2. a accepted color keyword. Color keywords: ["heteroatom"]
```Python
{
    "id": None,          # The id of the object to apply color to
    "color": None,
    "selection": None
 }
 ```
 #### Style
 Style is one of a set of accepted keywords: ["ribbon","sphere","stick"]
 ```Python
 {
    "id": None,          # The id of the object to apply style to
    "style": None,
    "selection": None
  }
```
#### Focus
Many existing focus changes in Phenix are specified using an xyz coordinate. It is useful to be able to specify that the focus should be expanded to include all of the nearest structural element. Expand keywords: [None,"model","chain","residue","atom"]
```Python
{
    "id": None,           # The id of the object to focus on
    "selection": None, 
    "xyz": (0., 0., 0.),  # Alternatively, focus on a point
    "xyz_expand": None 
}
```
#### Environment
Scene settings which apply to the entire scene, not to a specific data object. Needs to be expanded (more lighting options, field of view, others?)
```Python
{
	"background_color": "#FFFFFF",
	"lighting": "full"
}
```
