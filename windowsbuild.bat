pyinstaller --windowed --icon=./src/resources/logo.ico -n "ConnectorDB Desktop" -y src/windowsapp.py
md "./dist/ConnectorDB Desktop/windows"
xcopy /s "./src/windows" "./dist/ConnectorDB Desktop/windows"
md "./dist/ConnectorDB Desktop/all"
xcopy /s "./src/all" "./dist/ConnectorDB Desktop/all"
md "./dist/ConnectorDB Desktop/resources"
xcopy /s "./src/resources" "./dist/ConnectorDB Desktop/resources"
md "./dist/ConnectorDB Desktop/bin"
xcopy /s "./src/bin" "./dist/ConnectorDB Desktop/bin"
