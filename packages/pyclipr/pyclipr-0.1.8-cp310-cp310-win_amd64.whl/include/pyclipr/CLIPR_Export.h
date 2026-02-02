
#ifndef CLIPR_EXPORT_H
#define CLIPR_EXPORT_H

#ifdef CLIPR_BUILT_AS_STATIC
#  define CLIPR_EXPORT
#  define CLIPR_NO_EXPORT
#else
#  ifndef CLIPR_EXPORT
#    ifdef clipr_static_EXPORTS
        /* We are building this library */
#      define CLIPR_EXPORT 
#    else
        /* We are using this library */
#      define CLIPR_EXPORT 
#    endif
#  endif

#  ifndef CLIPR_NO_EXPORT
#    define CLIPR_NO_EXPORT 
#  endif
#endif

#ifndef CLIPR_DEPRECATED
#  define CLIPR_DEPRECATED __declspec(deprecated)
#endif

#ifndef CLIPR_DEPRECATED_EXPORT
#  define CLIPR_DEPRECATED_EXPORT CLIPR_EXPORT CLIPR_DEPRECATED
#endif

#ifndef CLIPR_DEPRECATED_NO_EXPORT
#  define CLIPR_DEPRECATED_NO_EXPORT CLIPR_NO_EXPORT CLIPR_DEPRECATED
#endif

/* NOLINTNEXTLINE(readability-avoid-unconditional-preprocessor-if) */
#if 0 /* DEFINE_NO_DEPRECATED */
#  ifndef CLIPR_NO_DEPRECATED
#    define CLIPR_NO_DEPRECATED
#  endif
#endif

#endif /* CLIPR_EXPORT_H */
