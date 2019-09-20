![Version](https://img.shields.io/badge/python-v2.7.16-blue.svg?style=flat-square)
![License](https://img.shields.io/badge/license-MPL-green.svg?style=flat-square)

# EasyDoH

EasyDoH is a simple addon for Firefox that allows to easily activate [DNS over HTTPS](https://en.wikipedia.org/wiki/DNS_over_HTTPS) and its mode with one click.

It contains explanations for the different modes allowed (only available in _about:config_) and DoH servers to choose from.

This addon requires changes in files, and since this cannot be done from the extension itself a Python script is needed that should be downloaded aside from the addon.

## Install

### Microsoft Windows:

Run [install.bat](app/Windows/install.bat) script in the desired directory. This script installs the native messaging host for the current user, by creating a registry key:

    HKEY_CURRENT_USER\SOFTWARE\Mozilla\NativeMessagingHosts\com.elevenpaths.easydoh

and set its default value to:

    com.google.chrome.example.echo-win.json

If you want to install the native messaging host for all users, change **HKCU** to **HKLM**.

For convenience an executable is provided, which is no more than the [easydoh.py](app/macOS-Linux/easydoh.py) file compiled for you. If you do not trust this executable file, just dismiss it and compile the [easydoh.py](app/macOS-Linux/easydoh.py) file yourself. If this is your case, please, note that you would need to have python installed.

For uninstall use [uninstall.bat](app/Windows/uninstall.bat) to completely remove it from the system.

### MacOS and Linux:

Run [install.sh](app/macOS-Linux/install.sh) script in the desired directory.

By default it is only installed for the current user, if you want it to be available for all the system users run it as root (eg. sudo ./install.sh)

Use [uninstall.sh](app/macOS-Linux/uninstall.sh) to completely remove it from the system.

## License

This project is licensed under the MPL Mozilla Public License Version 2.0 - see the LICENSE file for details
