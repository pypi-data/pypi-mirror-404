
__version__ = "0.1.0"

# Core imports
try:
    from . import core
except ImportError:
    pass

# PyTorch imports
try:
    from .torch import vision, sequence, graph, scientific
except (ImportError, ModuleNotFoundError):
    pass

# TensorFlow imports
try:
    from .tf import vision as tf_vision
    from .tf import sequence as tf_sequence
    from .tf import graph as tf_graph
    from .tf import scientific as tf_scientific
except (ImportError, ModuleNotFoundError):
    pass
