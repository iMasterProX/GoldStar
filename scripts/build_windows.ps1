param(
    [string]$OutputName = "goldstar"
)

pip install pyinstaller
pyinstaller -F -w -n $OutputName -m goldstar