from takk.models import Project, Worker, PubSub, NetworkApp, StreamlitApp, MlflowServer, Job, Compute, FastAPIApp

try:
    from importlib.metadata import version
    __version__ = version("takk")
except Exception:
    __version__ = "0.0.0+unknown"


__all__ = [
    "Project", 
    "Worker", 
    "PubSub", 
    "NetworkApp", 
    "StreamlitApp", 
    "MlflowServer", 
    "Job", 
    "Compute", 
    "FastAPIApp"
]
