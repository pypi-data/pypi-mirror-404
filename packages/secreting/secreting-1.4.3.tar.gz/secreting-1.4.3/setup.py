from io import open
from setuptools import setup, find_packages


setup(
    name='secreting',
    version='1.4.3',
    description='More secrets and randoms!',
    long_description='''# Secreting 1.4.3
### (before 1.4.4 it was secretting)

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
# [My github account](https://www.youtube.com/watch?v=dQw4w9WgXcQ)

# Enjoy it!



hi''',
    long_description_content_type='text/markdown',
    install_requires=[],
    packages=find_packages(),
)
