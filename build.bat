pyinstaller --windowed --icon=./src/resources/logo.ico -n laptoplogger -y src/windowsapp.py
md "./dist/laptoplogger/windows"
xcopy /s "./src/windows" "./dist/laptoplogger/windows"
md "./dist/laptoplogger/all"
xcopy /s "./src/all" "./dist/laptoplogger/all"
md "./dist/laptoplogger/resources"
xcopy /s "./src/resources" "./dist/laptoplogger/resources"
md "./dist/laptoplogger/bin"
xcopy /s "./src/bin" "./dist/laptoplogger/bin"