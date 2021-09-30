import sys
import threading

if sys.version_info.major == 2:
  import Pyro4
  import Pyro4.naming
else:
  import Pyro5
  import Pyro5.server
  import Pyro5.nameserver
  import Pyro5.api


class PyroManager(object):
  """
  A class to manage Pyro Services for Phenix
  """

  def __init__(self):
    self._ns_thread = None
    self._daemon_thread = None
    self.services = {}

    # # Pyro config
    # if sys.version_info.major == 2:
    #   Pyro4.config.COMPRESSION = True
    #   Pyro4.config.SERIALIZER = "marshal"
    # else:
    #   Pyro5.config.COMPRESSION = True
    #   Pyro5.config.SERIALIZER = "msgpack"

    # Start nameserver thread
    if not self.ns_visible():
      if sys.version_info.major == 2:
        t = threading.Thread(target=Pyro4.naming.startNSloop)  # py2
        t.setDaemon(True)
      else:
        t = threading.Thread(target=Pyro5.nameserver.start_ns_loop,
                             daemon=False)  # py3
      t.start()
      self._ns_thread = t

    # Start server daemon thread
    if sys.version_info.major == 2:
      self.daemon = Pyro4.Daemon()  # py2
      t = threading.Thread(target=self.daemon.requestLoop)
    else:
      self.daemon = Pyro5.server.Daemon()  # py3
      t = threading.Thread(target=self.daemon.requestLoop, daemon=False)

    t.start()
    self._daemon_thread = t

  def __del__(self):
    try:
      t = self._daemon_thread
      t.raise_exception()
      t.join()
    except:
      pass
    try:
      t = self._ns_thread
      t.raise_exception()
      t.join()
    except:
      pass


  def register_service(self, service, prefix=""):
    """
    service: Any object that has exposed Pyro methods.
    """
    service_uri = self.daemon.register(service)
    self.services[service_uri] = service
    if sys.version_info.major == 2:
      with Pyro4.locateNS() as ns:
        ns.register(prefix, service_uri)
    else:
      with Pyro5.api.locate_ns() as ns:
        ns.register(prefix, service_uri)
    return service_uri

  @staticmethod
  def ns_visible():
    if sys.version_info.major == 2:
      try:
        with Pyro4.locateNS() as ns:
          return True
      except:
        return False
    else:
      try:
        with Pyro5.api.locate_ns() as ns:
          return True
      except:
        return False