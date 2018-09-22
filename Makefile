APP_NAME?=Taranis\ Voice
VERSION?=$(shell python3 -c 'from version import __version__; print(__version__)')
APP_NAME_VER?=$(APP_NAME)\ $(VERSION)

version:
	echo '$(APP_NAME_VER)'


dmg: dist/$(APP_NAME_VER).dmg

dist/$(APP_NAME_VER).dmg: dist/$(APP_NAME).app
	hdiutil create -srcfolder 'dist/' -volname $(APP_NAME_VER) -fs HFS+ -fsargs '-c c=64,a=16,e=16' -format UDRW -size 64M 'build/$(APP_NAME)_temp.dmg'
	hdiutil convert 'build/$(APP_NAME)_temp.dmg' -format UDZO -imagekey zlib-level=9 -o '$@'
	rm 'build/$(APP_NAME)_temp.dmg'

py2app: dist/$(APP_NAME).app

dist/$(APP_NAME).app: icon.icns taranisvoice.py
	python setup.py py2app

icon.icns: icon.png
	sips -z 512 512 -r 180 -s format icns $^ --out $@

clean:
	rm -rf icon.icns dist build __pycache__
