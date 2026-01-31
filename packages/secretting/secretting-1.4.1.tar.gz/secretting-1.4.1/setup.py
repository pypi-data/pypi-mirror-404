from io import open
from setuptools import setup, find_packages


setup(
    name='secretting',
    version='1.4.1',
    description='More secrets and randoms!',
    long_description='''# More secrets and randoms!
# Installation:
```bash
pip install secretting
```
## If wont work:
```bash
pip3 install secretting
```
## Or:
```bash
pip install --upgrade secretting
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
## Hashlib''',
    long_description_content_type='text/markdown',
    install_requires=[],
    packages=find_packages(),
)
