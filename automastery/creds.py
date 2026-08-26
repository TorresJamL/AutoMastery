import os
import sys
from pathlib import Path

# Allow _t_.py for backward compatibility
this_files_absolute_root = Path(__file__).resolve()
repo_root = this_files_absolute_root.parent.parent
token_file = repo_root / "_t_.py"
if token_file.exists():
    sys.path.append(str(repo_root))
    print("Using token file (typical for local, for backward compatibility)")
    from _t_ import TOKEN, GS_PWD, GS_USR
    TOKEN, GS_PWD, GS_USR = TOKEN, GS_PWD, GS_USR # To make the linter happy


else:
    print("No token file found, checking for these env variables. Assuming server deployment. "
          " Make sure your keys are uploaded to the server.")
    TOKEN = os.environ["CANVAS_API_TOKEN"]
    GS_USR = os.environ["GRADESCOPE_EMAIL"]
    GS_PWD = os.environ["GRADESCOPE_PASSWORD"]





