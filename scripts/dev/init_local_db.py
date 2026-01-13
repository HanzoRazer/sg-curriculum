from runtime.config import RuntimeConfig
from runtime.engine import init_runtime

cfg = RuntimeConfig.load()
print(init_runtime(cfg))
