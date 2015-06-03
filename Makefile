PYTHON_BIN := `which python`
MANAGE=django-admin.py
IP=$(78.47.90.58)

run:
	PYTHONPATH=`pwd` DJANGO_SETTINGS_MODULE=demo.settings $(MANAGE) runserver 78.47.90.58:8000

syncdb:
	PYTHONPATH=`pwd` DJANGO_SETTINGS_MODULE=demo.settings $(MANAGE) syncdb
