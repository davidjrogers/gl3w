#!/usr/bin/env python
import re
import os
import urllib2

# Create directories
if not os.path.exists('include/GLES2'):
    os.makedirs('include/GLES2')
if not os.path.exists('include/KHR'):
    os.makedirs('include/KHR')
if not os.path.exists('src'):
    os.makedirs('src')

# Download gl2.h
if not os.path.exists('include/GLES2/gl2.h'):
    print 'Downloading gl2.h to include/GLES2...'
    web = urllib2.urlopen('http://www.khronos.org/registry/gles/api/2.0/gl2.h')
    with open('include/GLES2/gl2.h', 'wb') as f:
        f.writelines(web.readlines())
else:
    print 'Reusing gl2.h from include/GLES2...'

if not os.path.exists('include/GLES2/gl2ext.h'):
    print 'Downloading gl2ext.h to include/GLES2...'
    web = urllib2.urlopen('http://www.khronos.org/registry/gles/api/2.0/gl2ext.h')
    with open('include/GLES2/gl2ext.h', 'wb') as f:
        f.writelines(web.readlines())
else:
    print 'Reusing gl2ext.h from include/GLES2...'

if not os.path.exists('include/GLES2/gl2platform.h'):
    print 'Downloading gl2platform.h to include/GLES2...'
    web = urllib2.urlopen('http://www.khronos.org/registry/gles/api/2.0/gl2platform.h')
    with open('include/GLES2/gl2platform.h', 'wb') as f:
        f.writelines(web.readlines())
else:
    print 'Reusing gl2platform.h from include/GLES2...'

if not os.path.exists('include/KHR/khrplatform.h'):
    print 'Downloading khrplatform.h to include/KHR...'
    web = urllib2.urlopen('http://www.khronos.org/registry/egl/api/KHR/khrplatform.h')
    with open('include/KHR/khrplatform.h', 'wb') as f:
        f.writelines(web.readlines())
else:
    print 'Reusing khrplatform.h from include/KHR...'

# Parse function names from gl2.h
print 'Parsing gl2.h header...'
funcs = {}
p = re.compile(r'GL_APICALL\s+(.*)\s+GL_APIENTRY\s+(\w+)\s+\((.*)\)')
with open('include/GLES2/gl2.h', 'r') as f:
    for line in f:
        m = p.match(line)
        if m:
            funcs.setdefault('returns',[]).append(m.group(1))
            funcs.setdefault('procs',[]).append(m.group(2))
            funcs.setdefault('signatures',[]).append(m.group(3))

print 'Parsing gl2ext.h header...'
with open('include/GLES2/gl2ext.h', 'r') as f:
    for line in f:
        m = p.match(line)
        if m:
            funcs.setdefault('returns',[]).append(m.group(1))
            funcs.setdefault('procs',[]).append(m.group(2))
            funcs.setdefault('signatures',[]).append(m.group(3))

# Remove duplicates
result = {}

for idx,proc in enumerate(funcs['procs']):
# for key,value in funcs.items():
    if funcs['procs'][idx] not in result.values():
        result[idx] = funcs['procs'][idx]
    else:
        del funcs['returns'][idx]
        del funcs['procs'][idx]
        del funcs['signatures'][idx]

def proc_t(idx,proc):
    return { 'p': funcs['procs'][idx],
             'p_r': 'typedef ' + funcs['returns'][idx] + ' (GL_APIENTRY* PFN' + funcs['procs'][idx].upper() + 'PROC) (' + funcs['signatures'][idx] + ');',
             'p_s': 'glesw' + funcs['procs'][idx][2:],
             'p_t': 'PFN' + funcs['procs'][idx].upper() + 'PROC' }

# Generate gles2w.h
print 'Generating gles2w.h in include/GLES2...'
with open('include/GLES2/gles2w.h', 'wb') as f:
    f.write(r'''#ifndef __gles2w_h_
#define __gles2w_h_

#if defined(__APPLE__) || defined(__APPLE_CC__)
#   include <OpenGLES/ES2/gl.h>
    // Prevent Apple's non-standard extension header from being included
#   define __gl_es20ext_h_
#else
#   include <GLES2/gl2.h>
#   include <GLES2/gl2ext.h>
#endif

#ifndef __gl2_h_
#define __gl2_h_
#endif

#ifdef __cplusplus
extern "C" {
#endif

/* glesw api */
int gleswInit(void);
int gleswIsSupported(int major, int minor);
void *gleswGetProcAddress(const char *proc);

/* OpenGL functions */
''')
    for idx,proc in enumerate(funcs['procs']):
        f.write('%(p_r)s\n' % proc_t(idx,proc))
    f.write('\n')
    for idx,proc in enumerate(funcs['procs']):
        f.write('extern %(p_t)s %(p_s)s;\n' % proc_t(idx,proc))
    f.write('\n')
    for idx,proc in enumerate(funcs['procs']):
        f.write('#define %(p)s		%(p_s)s\n' % proc_t(idx,proc))
    f.write(r'''
#ifdef __cplusplus
}
#endif

#endif
''')

# Generate gles2w.c
print 'Generating gles2w.c in src...'
with open('src/gles2w.c', 'wb') as f:
    f.write(r'''#include <GLES2/gles2w.h>

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN 1
#include <windows.h>
#include <EGL/egl.h>

static HMODULE libgl;

static void open_libgl(void)
{
	libgl = LoadLibraryA("libGLESv2.dll");
}

static void close_libgl(void)
{
	FreeLibrary(libgl);
}

static void *get_proc(const char *proc)
{
	void *res;

	res = eglGetProcAddress(proc);
	if (!res)
		res = GetProcAddress(libgl, proc);
	return res;
}
#elif defined(__APPLE__) || defined(__APPLE_CC__)
#include <CoreFoundation/CoreFoundation.h>

CFBundleRef bundle;
CFURLRef bundleURL;

static void open_libgl(void)
{
	bundleURL = CFURLCreateWithFileSystemPath(kCFAllocatorDefault,
                                              CFSTR("/System/Library/Frameworks/OpenGLES.framework"),
                                              kCFURLPOSIXPathStyle, true);
    
	bundle = CFBundleCreate(kCFAllocatorDefault, bundleURL);
	assert(bundle != NULL);
}

static void close_libgl(void)
{
	CFRelease(bundle);
	CFRelease(bundleURL);
}

static void *get_proc(const char *proc)
{
	void *res;

	CFStringRef procname = CFStringCreateWithCString(kCFAllocatorDefault, proc,
                                                     kCFStringEncodingASCII);
	res = CFBundleGetFunctionPointerForName(bundle, procname);
	CFRelease(procname);
	return res;
}
#else
#include <dlfcn.h>
#include <EGL/egl.h>

static void *libgl;

static void open_libgl(void)
{
	libgl = dlopen("libGLESv2.so", RTLD_LAZY | RTLD_GLOBAL);
}

static void close_libgl(void)
{
	dlclose(libgl);
}

static void *get_proc(const char *proc)
{
	void *res;
    res = dlsym(libgl, proc);
	return res;
}
#endif

static struct {
	int major, minor;
} version;

static int parse_version(void)
{
    version.major = 2;
    version.minor = 0;

	return 0;
}

static void load_procs(void);

int gleswInit(void)
{
	open_libgl();
	load_procs();
	close_libgl();
	return parse_version();
}

int gleswIsSupported(int major, int minor)
{
	if (major < 2)
		return 0;
	if (version.major == major)
		return version.minor >= minor;
	return version.major >= major;
}

void *gleswGetProcAddress(const char *proc)
{
	return get_proc(proc);
}

''')
    for idx,proc in enumerate(funcs['procs']):
        f.write('%(p_t)s %(p_s)s;\n' % proc_t(idx,proc))
    f.write(r'''
static void load_procs(void)
{
''')
    for idx,proc in enumerate(funcs['procs']):
        f.write('\t%(p_s)s = (%(p_t)s) get_proc("%(p)s");\n' % proc_t(idx,proc))
    f.write('}\n')
