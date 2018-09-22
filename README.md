# Taranis Voice

## Building
### Requirements
* Python 3.7
* pyttsx3 (must have [pull request 19](https://github.com/nateshmbhat/pyttsx3/pull/19))
* pyobjc 5.0
* py2app 0.17
* appdirs

### Building
```shell
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools
pip3 install -r requirements.txt
make clean dmg
```

## Notes

This is a POC, the code is held together with duck tape and bird droppings.
