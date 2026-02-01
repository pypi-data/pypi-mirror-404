# newwave - drop-in replacement for wave.py

`wave.py` is part of python stdlib and is used for handling WAVE audio files.

I started `newwave` because I wanted to fix an issue where it can _read_
wave files which are not 'PCM Audio' such as having more than 2 channels
or more than 24 bits, but not _write_ them with correct headers.

Also, it provides newer wave features for use with older python versions:

- Add support for bytes and path-like paths in wave.open() (python 3.15)
- fix wave.Wave_write emitting unraisable when open raises (python 3.15)
- remove deprecated setmark, getmark, getmarkers interfaces (python 3.15)
- Support for reading WAVE_FORMAT_EXTENSIBLE (python 3.12)

You can install newwave on python 3.10 or later.

This module is a drop-in replacement for wave.py - any code that works
with `wave` can be upgraded to use `newwave` by simply modifying your import.

So instead of:

```
import wave
f = wave.open(file, 'w')
```

it is now:

```
import newwave as wave
f = wave.open(file, 'w')
...
```

What is more, I will try to upstream any modification in newwave
to cpython so in future python versions you can enjoy the same improvements
there.

TL;DR: `newwave` will be a great way to have these enhancements *now*,
on your existing `python`, just by installing it from pypi using `pip` or `uv`.
