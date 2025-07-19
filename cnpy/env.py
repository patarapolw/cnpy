from dotenv import dotenv_values

from cnpy.dir import exe_root

env = dotenv_values(exe_root / ".env")
