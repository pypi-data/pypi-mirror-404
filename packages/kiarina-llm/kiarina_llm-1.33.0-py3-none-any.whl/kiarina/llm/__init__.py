import logging
from importlib.metadata import version

__version__ = version("kiarina-llm")

logging.getLogger(__name__).addHandler(logging.NullHandler())
