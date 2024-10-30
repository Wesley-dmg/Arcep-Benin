#!/usr/bin/env python
'''import sys

def trace_import(frame, event, arg):
    if event == "call" and frame.f_code.co_name == "<module>":
        module_name = frame.f_globals.get('__name__', '')
        # Ne pas tracer les bibliothèques externes
        if "site-packages" not in frame.f_code.co_filename:
            print(f"Importing {module_name}")
sys.settrace(trace_import)
'''

import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()

