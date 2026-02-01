from pathlib import Path
from not1mm.lib.parse_udc import UDC

user_defined_contest = UDC()

path = Path.home() / "UDC_FILES"
path.iterdir()
try:
    print(f"{user_defined_contest.get_udc_names(path)=}")
except Exception as e:
    print(f"{e=}")
