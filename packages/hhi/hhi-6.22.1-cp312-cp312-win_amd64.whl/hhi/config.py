"""Store configuration."""

__all__ = ["PATH"]

import pathlib

home = pathlib.Path.home()
cwd = pathlib.Path.cwd()
cwd_config = cwd / "config.yml"

home_config = home / ".config" / "hhi.yml"
config_dir = home / ".config"
config_dir.mkdir(exist_ok=True)
module_path = pathlib.Path(__file__).parent.absolute()
repo_path = module_path.parent


class Path:
    home = home
    module = module_path
    repo = repo_path
    extra = module_path / "extra"
    klayout = module_path / "klayout"
    lyp_yaml = module_path / "layers.yaml"
    lyp = klayout / "layers.lyp"


PATH = Path()

if __name__ == "__main__":
    print(PATH)
