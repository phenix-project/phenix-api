# Phenix API Documentation

- The goal of this documentation is to define a common interface to run Phenix from multiple frontends (GUIs, notebooks, visualization software, etc.) 
- The reference implementation uses [Pyro5](https://pyro5.readthedocs.io/en/latest/), which provides a huge number of features ready to use. Some highlights:
	- Pure Python, requests are executed as method calls
	- Different serializers (serpent, json, marshal, msgpack)
	- IPv4, IPv6 or Unix domain sockets
	- Optional secure connections via SSL/TLS 
 - Whenever possible, logic should reside on the server side. For example, after a program completes the server should offer a relevant scene. The client does not need to contain logic to anticipate and request all the possible results.
 
### Request Types
- Program requests: Client wants to run a Phenix program
- Result requests: Client wants the results of a program run
- Scene requests: Client wants to draw a scene
	
### Response Types
 - Program statuss: Server reports on program progress
 - Result responses: Server provides program results
 - Scene responses: Server defines a particular scene.
 
 ### Data Types
 Whenever possible, the data should be standard Python data types, which are easily serialized by whichever backend being used. However, for more exotic data types, it is necessary to make them an explicit part of the API so that both client and server can anticipate them and know how to encode/decode the data structure.
 
  - Model file: Molecular structure
  - Map file: 3D volumetric data
  - MTZ file: Crystallographic reflection data
  - Generic text file: Useful for .eff, .phil for example
  - Generic binary file: Useful for flex arrays, numpy arrays, etc
 
## Definitions

#### Program request
```Python
{"program_name":"",
 "files":[],
 "args":[],
 "kwargs":{}}
```
#### Results response
Phenix programs return results in different ways. Files can be structured in a predictable way (see below). Many programs return results as an unstructured group_args object of key,value pairs. Many results can be converted into a dictionary and returned in the "results" field, but some are complex cctbx objects. In the majority of cases, the client is most interested in the file results, or in a scene response. 
```Python
{"uuid": # unique identifier for the run
"status":"" # One of running, finished, failed
"program_request":{}, # the original request object
"stdout":"",
"stderr":"",
"log":"",
"files":[],
"results":{}}
```

#### Model data
Models are serialized as strings of molecular file types (pdb,cif,mol,etc). This is simple and widely supported by potential clients. Compression is left to the serializer backend.
```Python
{"uuid":None, # unique identifier common between server/client
"data_type":"model",
"name":"model", # Display name for this model.
"read_filepath":"", # Filepath if sharing a filesystem
"write_filepath":"", # Filepath to write to 
"str_rep":"", # the model contents represented as string
"suffix":".pdb"} # Determines how to encode/decode str_rep
```
#### Map Data
In most cases, the client and server will share a filesystem. So the server should prefer to populate the "read_filepath" attribute and the client should prefer to read files from disk. 

If not sharing a filesystem, most Pyro serializer backends will refuse to encode arbitrary objects for security reasons. Even if doing that explicity, for example:
```Python
import pickle
p = pickle.dumps(complex_obj)
{"response_field":p}
```
Still requires decoding and recreating the complex object on the client side, which is failure prone. Instead, the map data response only serializes the numerical data, and inludes metadata to recreate the map on the client side. The numerical data is encoded as a Python list, with serialization, compression, and encryption left to the backend. 

```Python
{"uuid":None, # unique identifier
"name":"",
"data_type":"map",
"write_filepath":"",
"write_filepath":"",
"suffix":"" # mrc,ccp4,map,etc
"list_rep":""    # list(map_data()) 
"dtype":"float32" # A string to infer data type "int", "float32", "float64", etc
"shape":tuple(), # the shape of the map in each dimension
"pixel_sizes":tuple(),# the pixel sizes for each dimension (angstrom)
"shift_cart":tuple()} # the cartesian shift of the map if applicable

```Python
#### MTZ Files
- *TODO*

#### Generic files
```Python
{"data_type":"text",
"contents":""}
```


```Python
{"data_type":"binary",
"contents":None #bytes representation, should be a last resort
"serializer":"") # pickle, joblib, msgpack, etc
```
#### Scenes
A scene is a list of objects to display in a client viewer, and optionally information about depiction and focus. The server can manage a complex graph of scenes that may be generated during data processing, but it only serves one scene to the client at a time. If the client is a molecular graphics program, it is responsible for translating the scene into an image. 
```Python
{"uuid":None,
"data_type":"scene",
"objects":[] # a list of map or model responses
"depiction":{} # a complex dictionary of style attributes (see below)
"focus":{"selection":"","xyz":None} # Where to focus the camera. 
```

The depiction field should have keys to determine which object and selections to apply the style to. This needs a more rigorous definition. Probably it would be ideal to adopt [an existing](https://www.cgl.ucsf.edu/chimerax/docs/user/commands/style.html) [style API](https://3dmol.csb.pitt.edu/doc/types.html#AtomStyleSpec) as the default, and convert to other viewers on each client.
```Python
{"uuid":None, # The object to apply the style to.
"selection":"", # the string selection to apply the style to
"style":"" # ribbon, sphere, stick, ball, etc
"color":"" # HTML color field
"transparency":60} # 1-100 where 1 is opaque
```

All selections should be strings in Phenix [selection syntax.](https://phenix-online.org/documentation/reference/atom_selections.html)


