#!/usr/bin/env python
import re
import os
import urllib2

# Create directories
if not os.path.exists('include/GLES3'):
    os.makedirs('include/GLES3')
if not os.path.exists('include/KHR'):
    os.makedirs('include/KHR')
if not os.path.exists('src'):
    os.makedirs('src')

# Download gl3.h
if not os.path.exists('include/GLES3/gl3.h'):
    print 'Downloading gl3.h to include/GLES3...'
    web = urllib2.urlopen('http://www.khronos.org/registry/gles/api/3.0/gl3.h')
    with open('include/GLES3/gl3.h', 'wb') as f:
        f.writelines(web.readlines())
else:
    print 'Reusing gl3.h from include/GLES3...'

if not os.path.exists('include/GLES3/gl3ext.h'):
    print 'Downloading gl3ext.h to include/GLES3...'
    web = urllib2.urlopen('http://www.khronos.org/registry/gles/api/3.0/gl3ext.h')
    with open('include/GLES3/gl3ext.h', 'wb') as f:
        f.writelines(web.readlines())
else:
    print 'Reusing gl3ext.h from include/GLES3...'

if not os.path.exists('include/GLES3/gl3platform.h'):
    print 'Downloading gl3platform.h to include/GLES3...'
    web = urllib2.urlopen('http://www.khronos.org/registry/gles/api/3.0/gl3platform.h')
    with open('include/GLES3/gl3platform.h', 'wb') as f:
        f.writelines(web.readlines())
else:
    print 'Reusing gl3platform.h from include/GLES3...'

if not os.path.exists('include/KHR/khrplatform.h'):
    print 'Downloading khrplatform.h to include/KHR...'
    web = urllib2.urlopen('http://www.khronos.org/registry/egl/api/KHR/khrplatform.h')
    with open('include/KHR/khrplatform.h', 'wb') as f:
        f.writelines(web.readlines())
else:
    print 'Reusing khrplatform.h from include/KHR...'

# Parse function names from gl3.h
print 'Parsing gl3.h header...'
funcs = {}
p = re.compile(r'GL_APICALL\s+(.*)\s+GL_APIENTRY\s+(\w+)\s+\((.*)\)')
with open('include/GLES3/gl3.h', 'r') as f:
    for line in f:
        m = p.match(line)
        if m:
            funcs.setdefault('returns',[]).append(m.group(1))
            funcs.setdefault('procs',[]).append(m.group(2))
            funcs.setdefault('signatures',[]).append(m.group(3))

print 'Parsing gl3ext.h header...'
with open('include/GLES3/gl3ext.h', 'r') as f:
    for line in f:
        m = p.match(line)
        if m:
            funcs.setdefault('returns',[]).append(m.group(1))
            funcs.setdefault('procs',[]).append(m.group(2))
            funcs.setdefault('signatures',[]).append(m.group(3))

# Remove duplicates
sortedFunctions = {}
temp = {}

for idx,proc in enumerate(funcs['procs']):
    if funcs['procs'][idx] not in temp.values():
        temp[idx] = funcs['procs'][idx]

        sortedFunctions.setdefault('returns',[]).append(funcs['returns'][idx])
        sortedFunctions.setdefault('procs',[]).append(funcs['procs'][idx])
        sortedFunctions.setdefault('signatures',[]).append(funcs['signatures'][idx])
    else:
        print 'Skipping duplicate ' + funcs['procs'][idx] + ' definition'

def proc_t(idx,proc):
    return { 'p': sortedFunctions['procs'][idx],
             'p_r': 'typedef ' + sortedFunctions['returns'][idx] + ' (GL_APIENTRY* PFN' + sortedFunctions['procs'][idx].upper() + 'PROC) (' + sortedFunctions['signatures'][idx] + ');',
             'p_s': 'glesw' + sortedFunctions['procs'][idx][2:],
             'p_t': 'PFN' + sortedFunctions['procs'][idx].upper() + 'PROC' }

# Generate gles3w.h
print 'Generating gles3w.h in include/GLES3...'
with open('include/GLES3/gles3w.h', 'wb') as f:
    f.write(r'''#ifndef __gles3w_h_
#define __gles3w_h_

#if defined(__APPLE__) || defined(__APPLE_CC__)
#   include <OpenGLES/ES3/gl.h>
    // Prevent Apple's non-standard extension header from being included
#   define __gl_es30ext_h_
#else
#   include <GLES3/gl3.h>
#endif

#include <KHR/khrplatform.h>
#include <GLES3/gl3platform.h>
#include <GLES3/gl3ext.h>

#ifndef __gl3_h_
#define __gl3_h_
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
    for idx,proc in enumerate(sortedFunctions['procs']):
        f.write('%(p_r)s\n' % proc_t(idx,proc))
    f.write('\n')
    for idx,proc in enumerate(sortedFunctions['procs']):
        f.write('extern %(p_t)s %(p_s)s;\n' % proc_t(idx,proc))
    f.write('\n')
    for idx,proc in enumerate(sortedFunctions['procs']):
        f.write('#define %(p)s		%(p_s)s\n' % proc_t(idx,proc))
    f.write(r'''
#ifdef __cplusplus
}
#endif

#endif
''')

# Generate gles3w.c
print 'Generating gles3w.c in src...'
with open('src/gles3w.c', 'wb') as f:
    f.write(r'''#include <GLES3/gles3w.h>

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
#import <CoreFoundation/CoreFoundation.h>
#import <UIKit/UIDevice.h>
#import <string>
#import <iostream>
#import <stdio.h>

// Routine to run a system command and retrieve the output.
// From http://stackoverflow.com/questions/478898/how-to-execute-a-command-and-get-output-of-command-within-c
std::string exec(const char* cmd) {
    FILE* pipe = popen(cmd, "r");
    if (!pipe) return "ERROR";
    char buffer[128];
    std::string result = "";
    while(!feof(pipe)) {
    	if(fgets(buffer, 128, pipe) != NULL)
    		result += buffer;
    }
    pclose(pipe);
    return result;
}

CFBundleRef bundle;
CFURLRef bundleURL;

static void open_libgl(void)
{
    CFStringRef frameworkPath = CFSTR("/System/Library/Frameworks/OpenGLES.framework");
    NSString *sysVersion = [UIDevice currentDevice].systemVersion;
    BOOL isSimulator = ([[UIDevice currentDevice].model rangeOfString:@"Simulator"].location != NSNotFound);
    if(isSimulator)
    {
        // Ask where Xcode is installed
        std::string xcodePath = exec("/usr/bin/xcode-select -print-path");

        // The result contains an end line character. Remove it.
        size_t pos = xcodePath.find("\n");
        xcodePath.erase(pos);

        char tempPath[PATH_MAX];
        sprintf(tempPath,
                "%s/Platforms/iPhoneSimulator.platform/Developer/SDKs/iPhoneSimulator%s.sdk/System/Library/Frameworks/OpenGLES.framework",
                xcodePath.c_str(),
                [sysVersion cStringUsingEncoding:NSUTF8StringEncoding]);
        frameworkPath = CFStringCreateWithCString(kCFAllocatorDefault, tempPath, kCFStringEncodingUTF8);
    }

	bundleURL = CFURLCreateWithFileSystemPath(kCFAllocatorDefault,
                                              frameworkPath,
                                              kCFURLPOSIXPathStyle, true);

    CFRelease(frameworkPath);

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
	if (!glGetIntegerv)
		return -1;

	glGetIntegerv(GL_MAJOR_VERSION, &version.major);
	glGetIntegerv(GL_MINOR_VERSION, &version.minor);

	if (version.major < 3)
		return -1;
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
	if (major < 3)
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
    for idx,proc in enumerate(sortedFunctions['procs']):
        f.write('%(p_t)s %(p_s)s;\n' % proc_t(idx,proc))
    f.write(r'''
static void load_procs(void)
{
''')
    for idx,proc in enumerate(sortedFunctions['procs']):
        f.write('\t%(p_s)s = (%(p_t)s) get_proc("%(p)s");\n' % proc_t(idx,proc))
    f.write('}\n')
