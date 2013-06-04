============================================
glesw: Simple OpenGL ES 2.0/3.0 loading
============================================

Introduction
------------

glesw_ is the easiest way to get your hands on the functionality offered by the
OpenGL ES 2.0 and 3.0 specifications.

It is a fork of gl3w with modifications specifically to work with EGL and OpenGL
ES 2.0/3.0.

There are two scripts, one for each version. The main part is a simple script
gles2w_gen.py_ or gles3w_gen.py_ Python 2.6 script that downloads the Khronos_
supported headers and generates gles2w.h/gles3w.h and gles2w.c/gles3w.c 
respectively from them. Those files can then be added and linked (statically or
dynamically) into your project.

API Reference
-------------

The glesw_ API consists of just three functions:

``int gleswInit(void)``

    Initializes the library. Should be called once after an OpenGL context has
    been created. Returns ``0`` when glesw_ was initialized successfully,
    ``-1`` if there was an error.

``int gleswIsSupported(int major, int minor)``

    Returns ``1`` when OpenGL version *major.minor* is available,
    and ``0`` otherwise.

``void *gleswGetProcAddress(const char *proc)``

    Returns the address of an OpenGL extension function. Generally, you won't
    need to use it since glesw_ loads all the functions defined in the OpenGL
    core profile on initialization. It allows you to load OpenGL extensions
    outside of the core profile.

License
-------

glesw_ is in the public domain.

Credits
-------

Slavomir Kaslev <slavomir.kaslev@gmail.com>
    Initial implementation

Kelvin McDowell
    Mac OS X support

Sjors Gielen
    Mac OS X support

Rommel160 [github.com/Rommel160]
    Code contributions

Copyright
---------

OpenGL_ is a registered trademark of SGI_.

.. _glesw: https://github.com/davidjrogers/glesw
.. _gl3w: https://github.com/skaslev/gl3w
.. _gl3w_gen.py: https://github.com/skaslev/gl3w/blob/master/gl3w_gen.py
.. _gl3.h: http://www.opengl.org/registry/api/gl3.h
.. _OpenGL: http://www.opengl.org/
.. _Khronos: http://www.khronos.org/
.. _SGI: http://www.sgi.com/
