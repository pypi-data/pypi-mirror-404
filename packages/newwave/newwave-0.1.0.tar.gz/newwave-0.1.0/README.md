# newwave - drop-in replacement for wave.py

`wave.py` is a Python core library. It has some bugs and some shortcomings.
This module is a drop-in replacement for wave.py - any code that works
with `wave` can be upgraded to use `newwave` by simply modifying your import.

So instead of:

```
import wave
f = wave.open(file, 'w')
```

it is now:

```
import newwave
f = newwave.open(file, 'w')
```

What is more, I will try to upstream any modification in newwave
to cpython so in future python versions you can enjoy the same improvements
there. `newwave` will be a great way to have these enhancements *now*,
on your existing `python`, just by installing it from pypi using `pip` or `uv`.
