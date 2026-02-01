"""# Secretting 1.4.5

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

# Enjoy it!



hi"""

from typing import Any
from secrets import choice as _choice, compare_digest
from secrets import token_hex as _tkhex
import random as _rand
from random import random as _random
from string import ascii_letters as letters, digits, punctuation
from hashlib import sha512 as s512, sha256 as s256
from getpass import getpass

chars: tuple = (*letters, *digits, *punctuation)
def salt(length: int = 9) -> str:
    return ''.join(_choice(chars) for _ in range(length))
def sha256(text: str) -> str:
    return s256(text.encode()).hexdigest()
def sha512(text: str) -> str:
    return s512(text.encode()).hexdigest()
def secure256(text: str, customSalt: str = None) -> tuple:
    gSalt: str = customSalt or salt()
    return sha256(text + gSalt), gSalt
def secure512(text: str, customSalt: str = None) -> tuple:
    gSalt: str = customSalt or salt()
    return sha512(text + gSalt), gSalt
def multi256(text: str, times: int = 3) -> str:
    return sha256(text * times)
def multi512(text: str, times: int = 3) -> str:
    return sha512(text * times)
def hashByKey(text: str, key: str, delim: str = '') -> str:
	result = []
	for i, c in enumerate(text):
		result.append(str(ord(c) ^ ord(key[i % len(key)])))
	return delim.join(result)
def randint(min: int, max: int) -> int:
    return _choice([_rand.randint(min, max) for _ in range(20)])
def choice(seq: list) -> Any:
    return _choice([_choice(seq) for _ in range(20)])
def random() -> float:
    return _choice([_random() for _ in range(20)])
def tokenHex(nbytes) -> str:
    return _choice([_tkhex(nbytes) for _ in range(20)])
def safeFunc(func, *args, **kwargs) -> Any:
    return _choice([func(*args, **kwargs) for _ in range(20)])
def shuffle(seq: list) -> list:
    def _temp():
        temp = list(seq)
        _rand.shuffle(temp)
        return temp
    return _choice([_temp() for _ in range(20)])
def password(length: int = 12) -> str:
    def raw():
        return ''.join([_choice(chars) for _ in range(length)])
    return _choice([raw() for _ in range(20)])
def roll(chance: int = 50) -> bool:
    def raw():
        return _rand.randint(1, 100) <= chance
    return _choice([raw() for _ in range(20)])
def isEqual(a, b) -> bool:
    return compare_digest(a, b)
def loadEnv() -> dict:
    res = {}
    try:
        with open('.env', 'r') as f:
            datas = f.read()
            if datas:
                lines = datas.split('\n')
                for line in lines:
                    args = line.split('=')
                    res[args[0]] = args[1]
    except FileNotFoundError:
        pass
    return res
def hiddenInput(prompt: str) -> str:
    return getpass(prompt)
def tokenNum(length: int = 16):
    def raw():
        cdigits = '1234567890'
        return ''.join([_choice(cdigits) for _ in range(length)])
    return _choice([raw() for _ in range(20)])
def customToken(length: int = 16, symbols = 'kanderus'):
    def raw():
        return ''.join(_choice(symbols) for _ in range(length))
    return _choice([raw() for _ in range(20)])
def uuid():
    def raw():
        return '-'.join([''.join(choice([*letters, *digits]) for _ in range(4)) for _ in range(4)])
    return _choice([raw() for _ in range(20)])



# you reached the end of secretting lib
# congrats

# made by:

## kanderusss
## team noliki

# using:

## libs:
### typing
### secrets
### random
### string
### hashlib
### getpass

## langs:
### python?

## ide:
### atom
