import matplotlib.pyplot as plt
from traitlets.config import Config

import IPython

c = Config()
c.InteractiveShell.confirm_exit = False

code = [
    "%matplotlib osx",
    "print('hello')",
]

c.InteractiveShellApp.exec_lines = code
IPython.start_ipython(config=c, user_ns=globals())
