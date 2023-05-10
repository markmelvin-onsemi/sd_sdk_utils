# sd_sdk_utils
This repository houses a series of utility scripts that use the Sound Designer SDK.

To check out the code and use these scripts, simply clone the Git repository with:

```
git clone https://github.com/markmelvin-onsemi/sd_sdk_utils.git
```

To execute the scripts, you need to first ensure the dependencies are met.

# Dependencies
The scripts in this repository depend on:

- A Sound Designer SDK being available in a local folder (referenced via `SD_SDK_ROOT` or a command line argument to the scripts)
- The Python module dependencies (in particular the helper module [sd-sdk-python](https://pypi.org/project/sd-sdk-python/)) which will be installed automatically using `poetry install`

## Sound Designer SDK
The Sound Designer SDK is available to users who have an NDA and have downloaded a Pre Suite release. Simply unzip the archive `SoundDesignerSDK.zip` to a folder on your hard drive and either:
- Pass the path to that folder via the script's `--sdk-root` argument
- Set it in the environment variable `SD_SDK_ROOT` in your environment

## Installing Poetry
This repository uses [poetry](https://python-poetry.org/docs/) to manage its Python module dependencies. So, the first step is to make sure you have [poetry](https://python-poetry.org/docs/) installed. If you do, you should be able to run this command in a shell:

```
$ poetry about
Poetry - Package Management for Python

Version: 1.2.2
Poetry-Core Version: 1.3.2

Poetry is a dependency manager tracking local dependencies of your projects and libraries.
See https://github.com/python-poetry/poetry for more information.
```

If you do not have [poetry](https://python-poetry.org/docs/), it is recommended that you install it using the [official installer](https://python-poetry.org/docs/#installing-with-the-official-installer) method.

## Installing the Python Dependencies Using [poetry](https://python-poetry.org/docs/)
Once you have this repository checked out, and [poetry](https://python-poetry.org/docs/) installed, you can install the Python dependencies using the following commands:

```
$ cd sd_sdk_utils
$ poetry install
```
_(NOTE: `poetry install` must be run in this repository's root folder)_

You should see the following:

```
$ poetry install
Creating virtualenv sd-sdk-utils-Ul1vD0NY-py3.10 in C:\Users\ffwxyx\AppData\Local\pypoetry\Cache\virtualenvs
Installing dependencies from lock file

Package operations: 1 install, 0 updates, 0 removals

  • Installing sd-sdk-python (0.2.0)
```

That's it! You're now ready to try running the scripts in this repository. To run a script with [poetry](https://python-poetry.org/docs/), you have two options:

Running the script using the `poetry run` command:
```
$ poetry run python my_script.py
```

Entering a poetry shell and running Python from within the poetry shell:
```
$ poetry shell
$ python my_script.py
```
(To exit this poetry virtual environment, simply type `exit`)

# Useful Scripts

The following scripts you may find useful. For all of these scripts, you can see their usage with:

```
poetry run python .\scripts\<script_name>.py -h
```

Also note that most scripts require a programmer and there are command line options to specify which programmer to use (the default is to use the CAA).

## `scripts/confirm_sdk.py`

This is a simple script that you can use to test your installation. Run it as follows:

```
poetry run python .\scripts\confirm_sdk.py --sdk-root=C:\path\to\your\SoundDesignerSDK

Found an SDK at C:\path\to\your\SoundDesignerSDK
ProductManager Version: 0x0x127122c
```
## `scripts/configure_device.py`

This script burns and configures a device using the given .param file. Run it as follows:

```
poetry run python .\scripts\configure_device.py --sdk-root=C:\_dev\PreSuite\SoundDesignerSDK --param-file=.\path\to\my.param --upgrade-firmware
Skipping firmware update as it is already up to date (1.15.1576)
Configuring device from .param file: path\to\my.param... done!
```


## `scripts/configure_binaural_pair.py`

This script automates the programming of a binaural pair. It allows you to specify a base parameter file, and then it will program the appropriate left/right and central/peripheral settings into the device, optionally deleting the bond tables. You can also specify whether ASHA and MFi are enabled (both are disabled by default and the settings in the .param file for both of these are ignored). If you don't manually provide the central and peripheral MAC addresses, they will be automatically detected. You can also optionally upgrade the firmware in the devices as well! 

Here are some example usages:

### Automatically detect the peer addresses, only enable ASHA, and delete the bond table
```
poetry run python .\scripts\configure_binaural_pair.py --sdk-root=C:\path\to\your\SoundDesignerSDK --param-file=.\configs\binaural_pair_default.param --asha=True --mfi=False --delete-bonds
```

### Manually specify both peer addresses, only enable ASHA, delete the bond table, and upgrade the firmware if it is not the same as the provided .library file
```
poetry run python .\scripts\configure_binaural_pair.py --sdk-root=C:\path\to\your\SoundDesignerSDK --upgrade-firmware --param-file=.\configs\binaural_pair_default.param --library-file=C:\path\to\my\E7160SL.library --asha=True --mfi=False --delete-bonds --peripheral-address=0x60c0bf4d7bb8 --central-address=0x60c0bf4d620e
```
