from importlib import resources
try:
    with resources.path("mvtbimages", "monalisa.png") as f:
        print(f)
except:
    pass

import importlib
from pathlib import Path

m = importlib.import_module("mvtbimages")
print(m.__path__)
p = Path(m.__path__[0])
print((p / "monalisa.png").exists())
print((p / "mosaic" / "aerial-8.png").exists())

