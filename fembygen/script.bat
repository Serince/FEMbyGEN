for %%i in (ui/*.ui) do (
"C:\Program Files (x86)\Qt Designer\lupdate.exe" ui/%%i -ts translations/uifiles.ts)
