import os, sys, locale


def get_system_language() -> str:
    env_lang = os.environ.get('LANG') or os.environ.get('LANGUAGE')
    sys_lang = None
    default_lang = None

    if sys.platform == 'win32':
        try:
            import ctypes
            windll = ctypes.windll.kernel32
            sys_lang = locale.windows_locale[windll.GetUserDefaultUILanguage()].split('_')[0]
        except:
            pass

    try:
        default_lang = locale.getdefaultlocale()[0].split('_')[0]
    except:
        pass

    return env_lang or sys_lang or default_lang or 'en'
