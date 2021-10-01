def detect_server_version():
  PYRO_VERSION = None
  try:
    import Pyro4
    with Pyro4.locateNS() as ns:
      PYRO_VERSION = 4
  except:
    pass
  try:
    import Pyro5
    with Pyro5.api.locate_ns() as ns:
      if "5" in ns._pyroUri.__class__.__module__:
        PYRO_VERSION=5
  except:
    pass
  if PYRO_VERSION == None:
    PYRO_VERSION = 5
  return PYRO_VERSION





def find_server(prefix="", uri=None, return_index=None, try_most_recent=True,PYRO_VERSION=4):

  if PYRO_VERSION ==4:
    import Pyro4
    import Pyro4.naming
  else:
    import Pyro5
    import Pyro5.client
    import Pyro5.api

  failed = False
  services = []
  service_names = []
  service_uris = []
  service, service_name, service_uri = None, None, None

  if uri is not None:
    prefix = ""

  if PYRO_VERSION == 4:
    with Pyro4.naming.locateNS() as ns:
      for service, service_uri in ns.list(prefix=prefix).items():
        # print("found service:", service)
        services.append(Pyro4.Proxy(service_uri))
        service_names.append(service)
        service_uris.append(service_uri)
  else:
    with Pyro5.api.locate_ns() as ns:
      for service, service_uri in ns.list(prefix=prefix).items():
        # print("found service:", service)
        services.append(Pyro5.api.Proxy(service_uri))
        service_names.append(service)
        service_uris.append(service_uri)

  if len(services) == 0:
    failed = True

  if uri != None:
    service_uri_strings = [str(service_uri) for service_uri in service_uris]
    try:
      service_index = service_uri_strings.index(uri)
      service = services[service_index]
      service_name = service_names[service_index]
      service_uri = service_uris[service_index]
      return service, service_name, service_uri, failed
    except:
      pass

  elif try_most_recent:
    times = []
    for name in service_names:
      name = str(name)
      split = name.split(".")
      t = split[-1]
      try:
        times.append(float(t))
      except:
        times.append(0)
    sorted_names = [x for _, x in
                    sorted(zip(times, service_names), reverse=True)]
    name = sorted_names[0]
    name_index = service_names.index(name)
    service = services[name_index]
    service_uri = service_uris[name_index]
    return service, name, service_uri, failed

  elif return_index is not None:
    return services[return_index], service_names[return_index], service_uris[
      return_index], failed
  else:
    return services, service_names, service_uris, failed
