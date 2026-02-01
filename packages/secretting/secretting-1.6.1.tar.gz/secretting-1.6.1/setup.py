from io import open
from setuptools import setup, find_packages


setup(
    name='secretting',
    version='1.6.1',
    description='More secrets and randoms!',
    long_description='''# Secretting 1.6.1

# More secrets and randoms!
# Installation:
```bash
pip install secreting
```
## If wont work:
```bash
pip3 install secreting
```
## Or:
```bash
pip install --upgrade secreting
```

# Example:
```python
salt() # Output: salt
sha256("a") # Output: hash
secure256("a") # Output: (hash, salt)
isEqual(1, 1) # Output: True
isEqual(1, 2) # Output: False
chars # Output: (ascii_letters, digits, punctuation)
tokenHex(32) # Output: token with 32 bytes
# And more nice tools!
```
# Libs:
## Secrets (choice, compare_digest)
## Random (shuffle, random, randint)
## String (ascii_letters, digits, punctuation)
## Hashlib (sha256, sha512)

# Github
## [My github account](https://www.youtube.com/watch?v=dQw4w9WgXcQ)

# Random scheme
## Secretting uses Chaos 20 system
## How it works:
```python
import secrets

def x_or_o():
    return secrets.choice(["x", "o"])
def chaos20system(func, *args, **kwargs):
    return secrets.choice([func(*args, **kwargs) for _ in range(20)])
# This is list of 20 funcs.
# Returns 1 random of this list.
# It is more random than secrets.choice and random.choice.
# Secretting made by only this scheme.
# And yeah its made by me.
# You can copy this scheme :-)
# :-) :-) :-) :-) :-) :-) :-) :-) :-)
# :-) :-) :-) :-) :-) :-) :-) :-) :-)
# :-) :-) :-) :-) :-) :-) :-) :-) :-)
# :-) :-) :-) :-) :-) :-) :-) :-) :-)
# :-) :-) :-) :-) :-) :-) :-) :-) :-)
```

# Enjoy it!



hi''',
    long_description_content_type='text/markdown',
    install_requires=[],
    packages=find_packages(),
)
