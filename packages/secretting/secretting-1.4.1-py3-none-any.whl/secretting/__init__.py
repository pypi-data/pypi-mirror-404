from secrets import choice as _choice, compare_digest
from secrets import token_hex as _tkhex
import random as _rand
from random import random as _random
from string import ascii_letters as letters, digits, punctuation
from hashlib import sha512 as s512, sha256 as s256

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
def randint(min: int, max: int):
    return _choice([_rand.randint(min, max) for _ in range(20)])
def choice(seq: list):
    return _choice([_choice(seq) for _ in range(20)])
def random():
    return _choice([_random() for _ in range(20)])
def tokenHex(nbytes):
    return _choice([_tkhex(nbytes) for _ in range(20)])
def safeFunc(func, *args, **kwargs):
    return _choice([func(*args, **kwargs) for _ in range(20)])
def shuffle(seq: list):
    def _temp():
        temp = list(seq)
        _rand.shuffle(temp)
        return temp
    return _choice([_temp() for _ in range(20)])
def password(length: int = 12):
    def raw():
        return ''.join([_choice(chars) for _ in range(length)])
    return _choice([raw() for _ in range(20)])
def roll(chance: int = 50):
    def raw():
        return _rand.randint(1, 100) <= chance
    return _choice([raw() for _ in range(20)])
def isEqual(a, b):
    '''Its not classic a == b, trust me.'''
    return compare_digest(a, b)


# Wow, you reached the end of secretting lib!
