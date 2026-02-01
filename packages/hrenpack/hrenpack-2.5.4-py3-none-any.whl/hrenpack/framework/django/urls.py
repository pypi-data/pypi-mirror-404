import re
from django.urls import get_resolver


def get_all_app_prefixes():
    """
    Получить словарь всех приложений и их префиксов
    """
    resolver = get_resolver()
    app_prefixes = {}

    for pattern in resolver.url_patterns:
        if hasattr(pattern, 'url_patterns'):
            pattern_str = str(pattern)
            match = re.search(r"include\('([\w\.]+)'\)", pattern_str)
            if match:
                app_path = match.group(1)
                app_name = app_path.split('.')[0]
                app_prefixes[app_name] = str(pattern.pattern).rstrip('/')

    return app_prefixes