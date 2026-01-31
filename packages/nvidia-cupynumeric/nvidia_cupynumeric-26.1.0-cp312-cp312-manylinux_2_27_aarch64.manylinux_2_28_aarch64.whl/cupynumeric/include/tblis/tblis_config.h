#ifndef _SRC_TBLIS_CONFIG_H
#define _SRC_TBLIS_CONFIG_H 1
 
/* src/tblis_config.h. Generated automatically at end of configure. */
/* config.h.  Generated from config.h.in by configure.  */
/* config.h.in.  Generated from configure.ac by autoheader.  */

/* Define if you have a BLAS library. */
/* #undef HAVE_BLAS */

/* define if the compiler supports basic C++14 syntax */
/* #undef HAVE_CXX14 */

/* Define to 1 if you have the <dlfcn.h> header file. */
#ifndef TBLIS_HAVE_DLFCN_H
#define TBLIS_HAVE_DLFCN_H 1
#endif

/* Define to 1 if you have the <hbwmalloc.h> header file. */
/* #undef HAVE_HBWMALLOC_H */

/* Define to 1 if you have the <hwloc.h> header file. */
/* #undef HAVE_HWLOC_H */

/* Define to 1 if you have the <inttypes.h> header file. */
#ifndef TBLIS_HAVE_INTTYPES_H
#define TBLIS_HAVE_INTTYPES_H 1
#endif

/* Define if the system has the lscpu command. */
#ifndef TBLIS_HAVE_LSCPU
#define TBLIS_HAVE_LSCPU 1
#endif

/* Define to 1 if you have the <memkind.h> header file. */
/* #undef HAVE_MEMKIND_H */

/* Define to 1 if you have the <stdint.h> header file. */
#ifndef TBLIS_HAVE_STDINT_H
#define TBLIS_HAVE_STDINT_H 1
#endif

/* Define to 1 if you have the <stdio.h> header file. */
#ifndef TBLIS_HAVE_STDIO_H
#define TBLIS_HAVE_STDIO_H 1
#endif

/* Define to 1 if you have the <stdlib.h> header file. */
#ifndef TBLIS_HAVE_STDLIB_H
#define TBLIS_HAVE_STDLIB_H 1
#endif

/* Define to 1 if you have the <strings.h> header file. */
#ifndef TBLIS_HAVE_STRINGS_H
#define TBLIS_HAVE_STRINGS_H 1
#endif

/* Define to 1 if you have the <string.h> header file. */
#ifndef TBLIS_HAVE_STRING_H
#define TBLIS_HAVE_STRING_H 1
#endif

/* Define to 1 if you have the `sysconf' function. */
#ifndef TBLIS_HAVE_SYSCONF
#define TBLIS_HAVE_SYSCONF 1
#endif

/* Define to 1 if you have the `sysctl' function. */
/* #undef HAVE_SYSCTL */

/* Define to 1 if you have the `sysctlbyname' function. */
/* #undef HAVE_SYSCTLBYNAME */

/* Define to 1 if you have the <sys/stat.h> header file. */
#ifndef TBLIS_HAVE_SYS_STAT_H
#define TBLIS_HAVE_SYS_STAT_H 1
#endif

/* Define to 1 if you have the <sys/types.h> header file. */
#ifndef TBLIS_HAVE_SYS_TYPES_H
#define TBLIS_HAVE_SYS_TYPES_H 1
#endif

/* Define to 1 if you have the <unistd.h> header file. */
#ifndef TBLIS_HAVE_UNISTD_H
#define TBLIS_HAVE_UNISTD_H 1
#endif

/* sysconf(_SC_NPROCESSORS_CONF) is valid. */
#ifndef TBLIS_HAVE__SC_NPROCESSORS_CONF
#define TBLIS_HAVE__SC_NPROCESSORS_CONF 1
#endif

/* sysconf(_SC_NPROCESSORS_ONLN) is valid. */
#ifndef TBLIS_HAVE__SC_NPROCESSORS_ONLN
#define TBLIS_HAVE__SC_NPROCESSORS_ONLN 1
#endif

/* label_type */
#ifndef TBLIS_LABEL_TYPE
#define TBLIS_LABEL_TYPE int32_t
#endif

/* len_type */
#ifndef TBLIS_LEN_TYPE
#define TBLIS_LEN_TYPE int64_t
#endif

/* Define to the sub-directory where libtool stores uninstalled libraries. */
#ifndef TBLIS_LT_OBJDIR
#define TBLIS_LT_OBJDIR ".libs/"
#endif

/* Name of package */
#ifndef TBLIS_PACKAGE
#define TBLIS_PACKAGE "tblis"
#endif

/* Define to the address where bug reports for this package should be sent. */
#ifndef TBLIS_PACKAGE_BUGREPORT
#define TBLIS_PACKAGE_BUGREPORT "damatthews@smu.edu"
#endif

/* Define to the full name of this package. */
#ifndef TBLIS_PACKAGE_NAME
#define TBLIS_PACKAGE_NAME "tblis"
#endif

/* Define to the full name and version of this package. */
#ifndef TBLIS_PACKAGE_STRING
#define TBLIS_PACKAGE_STRING "tblis 1.2.0"
#endif

/* Define to the one symbol short name of this package. */
#ifndef TBLIS_PACKAGE_TARNAME
#define TBLIS_PACKAGE_TARNAME "tblis"
#endif

/* Define to the home page for this package. */
#ifndef TBLIS_PACKAGE_URL
#define TBLIS_PACKAGE_URL "http://www.github.com/devinamatthews/tblis"
#endif

/* Define to the version of this package. */
#ifndef TBLIS_PACKAGE_VERSION
#define TBLIS_PACKAGE_VERSION "1.2.0"
#endif

/* More convenient macro for restrict. */
#ifndef TBLIS_RESTRICT
#define TBLIS_RESTRICT _tblis_restrict
#endif

/* Define to 1 if all of the C90 standard headers exist (not just the ones
   required in a freestanding environment). This macro is provided for
   backward compatibility; new code need not use it. */
#ifndef TBLIS_STDC_HEADERS
#define TBLIS_STDC_HEADERS 1
#endif

/* stride_type */
#ifndef TBLIS_STRIDE_TYPE
#define TBLIS_STRIDE_TYPE int64_t
#endif

/* The top source directory. */
#ifndef TBLIS_TOPDIR
#define TBLIS_TOPDIR "/__w/cupynumeric.internal/cupynumeric.internal/scripts/build/python/cupynumeric/buildwheel/_deps/tblis-src"
#endif

/* Version number of package */
#ifndef TBLIS_VERSION
#define TBLIS_VERSION "1.2.0"
#endif

/* Define to the equivalent of the C99 'restrict' keyword, or to
   nothing if this is not supported.  Do not define if restrict is
   supported only directly.  */
#ifndef _tblis_restrict
#define _tblis_restrict /**/
#endif
/* Work around a bug in older versions of Sun C++, which did not
   #define __restrict__ or support _Restrict or __restrict__
   even though the corresponding Sun C compiler ended up with
   "#define restrict _Restrict" or "#define restrict __restrict__"
   in the previous line.  This workaround can be removed once
   we assume Oracle Developer Studio 12.5 (2016) or later.  */
#if defined __SUNPRO_CC && !defined __RESTRICT && !defined __restrict__
# define _Restrict
# define __restrict__
#endif
 
/* once: _SRC_TBLIS_CONFIG_H */
#endif
