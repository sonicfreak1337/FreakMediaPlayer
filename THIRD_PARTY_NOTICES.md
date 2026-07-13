# Third-Party Notices

Freak Media Player includes or dynamically uses the following primary components.
The release is distributed subject to their respective license terms.

| Component | License | Project |
|---|---|---|
| Python | Python Software Foundation License 2.0 | https://www.python.org/ |
| PySide6 / Qt for Python | LGPL-3.0-only, GPL-2.0-only, GPL-3.0-only or commercial | https://doc.qt.io/qtforpython-6/ |
| Qt 6 runtime | LGPL-3.0-only, GPL-2.0-only, GPL-3.0-only or commercial, depending on module | https://www.qt.io/licensing/ |
| PyAV | BSD-3-Clause | https://pyav.org/ |
| FFmpeg libraries used by PyAV | LGPL-2.1-or-later or GPL, depending on the bundled build configuration | https://ffmpeg.org/legal.html |
| NumPy | BSD-3-Clause | https://numpy.org/ |
| SciPy | BSD-3-Clause | https://scipy.org/ |
| PyInstaller bootloader | GPL-2.0-or-later with a special exception for bundled applications | https://pyinstaller.org/ |

The packaged dependency directories retain license files supplied by their wheel
distributions. This notice does not replace those license texts. User-created
skins and user-owned audio files are not part of the application distribution.

## Optional network services

The Internet Radio plugin can query the public Radio Browser service
(`https://www.radio-browser.info/`) for station metadata and then connects directly
to the stream and logo URLs selected by the user. Radio Browser, station metadata,
logos and audio streams are not bundled with Freak Media Player. Their availability,
content and individual terms remain the responsibility of their respective service
and station operators.
