"""Load .env once for anything importing this package.

Containers get their environment from compose and have no .env file; that case
is silent rather than an error, which is what we want.
"""

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))
