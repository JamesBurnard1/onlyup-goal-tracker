#!/bin/bash

echo "Uninstalling broken Python 3.11.9 if it exists..."
pyenv uninstall -f 3.11.9

echo "Reinstalling Python 3.11.9 with proper Tcl/Tk support..."

env \
  CPPFLAGS="-I$(brew --prefix tcl-tk)/include" \
  LDFLAGS="-L$(brew --prefix tcl-tk)/lib" \
  PKG_CONFIG_PATH="$(brew --prefix tcl-tk)/lib/pkgconfig" \
  PYTHON_CONFIGURE_OPTS="--with-tcltk-includes='-I$(brew --prefix tcl-tk)/include' --with-tcltk-libs='-L$(brew --prefix tcl-tk)/lib -ltcl8.6 -ltk8.6'" \
  pyenv install 3.11.9

echo "Setting 3.11.9 as the default Python..."
pyenv global 3.11.9

echo "Testing tkinter..."
python -m tkinter
