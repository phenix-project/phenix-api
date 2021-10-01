import sys
import threading
import socket
import logging

if sys.version_info.major == 2:
  import Pyro4
  import Pyro4.naming
  from Pyro4.naming import *
  from Pyro4.naming import NameServerDaemon, BroadcastServer
  log = logging.getLogger("Pyro4.naming")
  PYRO_VERSION = 4

else:
  import Pyro5
  import Pyro5.server
  import Pyro5.nameserver
  from Pyro5.nameserver import *
  from Pyro5.nameserver import NameServerDaemon, BroadcastServer
  import Pyro5.api
  log = logging.getLogger("Pyro5.nameserver")
  PYRO_VERSION = 5

def get_ns_daemon(host=None,
                        port=None,
                        enableBroadcast=True,
                        bchost=None,
                        bcport=None,
                        unixsocket=None,
                        nathost=None,
                        natport=None,
                        storage=None,
                        hmac=None):
  """
  This function is copied directly from Pyro4.naming.startNSloop
  The reason is to return the daemon, which the original did not
  """
  daemon = NameServerDaemon(host, port, unixsocket, nathost=nathost,
                            natport=natport, storage=storage)
  daemon._pyroHmacKey = hmac
  nsUri = daemon.uriFor(daemon.nameserver)
  internalUri = daemon.uriFor(daemon.nameserver, nat=False)
  bcserver = None
  if unixsocket:
    hostip = "Unix domain socket"
  else:
    hostip = daemon.sock.getsockname()[0]
    if daemon.sock.family == socket.AF_INET6:  # ipv6 doesn't have broadcast. We should probably use multicast instead...
      print("Not starting broadcast server for IPv6.")
      log.info("Not starting NS broadcast server because NS is using IPv6")
      enableBroadcast = False
    elif hostip.startswith("127.") or hostip == "::1":
      print("Not starting broadcast server for localhost.")
      log.info(
        "Not starting NS broadcast server because NS is bound to localhost")
      enableBroadcast = False
    if enableBroadcast:
      # Make sure to pass the internal uri to the broadcast responder.
      # It is almost always useless to let it return the external uri,
      # because external systems won't be able to talk to this thing anyway.
      bcserver = BroadcastServer(internalUri, bchost, bcport,
                                 ipv6=daemon.sock.family == socket.AF_INET6)
      print("Broadcast server running on %s" % bcserver.locationStr)
      bcserver.runInThread()
  existing = daemon.nameserver.count()
  if existing > 1:  # don't count our own nameserver registration
    print("Persistent store contains %d existing registrations." % existing)
  print("NS running on %s (%s)" % (daemon.locationStr, hostip))
  if not hmac:
    print("Warning: HMAC key not set. Anyone can connect to this server!")
  if daemon.natLocationStr:
    print("internal URI = %s" % internalUri)
    print("external URI = %s" % nsUri)
  else:
    print("URI = %s" % nsUri)
  return daemon, bcserver
  # try:
  #   daemon.requestLoop()
  # finally:
  #   daemon.close()
  #   if bcserver is not None:
  #     bcserver.close()

class PyroManager:
  """
  The top level class to manage Pyro Services for Phenix.
  This should be a singleton, which is deleted upon GUI exit.

  If not deleted properly (calling the __del__ method), it will block GUI exit.
  """

  def __init__(self):
    self._ns_thread = None
    self._daemon_thread = None
    self.services = {}
    self.daemon = None
    self._ns_daemon = None
    self._bcserver = None
    # Pyro config
    if sys.version_info.major == 2:
      Pyro4.config.COMPRESSION = True
      Pyro4.config.SERIALIZERS_ACCEPTED.add("msgpack")
      Pyro4.config.SERIALIZER = "msgpack"
    else:
      Pyro5.config.COMPRESSION = True
      Pyro5.config.SERIALIZER = "msgpack"

    # Start nameserver thread
    if not self.ns_visible():
      if sys.version_info.major == 2:
        self._ns_daemon, self._bcserver = get_ns_daemon()
        t = threading.Thread(target=self._ns_daemon.requestLoop)  # py2
        t.setDaemon(False)
      else:
        self._ns_daemon, self._bcserver = get_ns_daemon()
        t = threading.Thread(target=self._ns_daemon.requestLoop,
                             daemon=False)  # py3
      t.start()
      self._ns_thread = t

    # Start server daemon thread
    if sys.version_info.major == 2:
      self.daemon = Pyro4.Daemon()  # py2
      t = threading.Thread(target=self.daemon.requestLoop)
      t.setDaemon(False)
    else:
      self.daemon = Pyro5.server.Daemon()  # py3
      t = threading.Thread(target=self.daemon.requestLoop, daemon=False)
    t.start()
    self._daemon_thread = t

  def __del__(self):
    if hasattr(self,"_daemon_thread"):
      self.daemon.shutdown()
      del self.daemon
    if hasattr(self,"_ns_daemon"):
      self._ns_daemon.shutdown()
      self._ns_daemon.close()
      del self._ns_daemon
    if hasattr(self,"_bcserver") and self._bcserver is not None:
        self._bcserver.close()
        del self._bcserver

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

  @staticmethod
  def find_server(prefix="", uri=None, return_index=None, try_most_recent=True):
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
