# Save The Unicorns

This is a demo project using the

- Demo site: https://savetheunicorns.kylestevenson.io

## Quickstart

```bash
git clone
```

This project uses GDAL libraries, that you need to install localy

```bash
sudo apt-get update && sudo apt-get install -y gdal-bin libgdal-dev libgeos-dev
```



It's recommended you use [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/)
and [The Developer Society Dev Tools](https://github.com/developersociety/tools).

Presuming you are using those tools, getting started on this project is pretty straightforward:

```console
$ dev-clone save-the-unicorns
$ workon save-the-unicorns
$ make reset
```

You can now run the development server:

```console
$ python manage.py runserver
```
