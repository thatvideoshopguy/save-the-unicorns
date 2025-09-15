# Save The Unicorns

This is a demo project using the most
recent [Developer Society](https://www.dev.ngo/) [Django template](https://github.com/developersociety/django-template).

The complete demo site is here https://savetheunicorns.kylestevenson.io

## Prerequisites

These are libraries required locally for this project to function correctly.

- Docker and Docker Compose
- Make

### Additional libraries

#### GDAL

These libraries are used by PostGIS for the map feature.

_MacOS_

```bash
brew install gdal geos
```

_Ubuntu_

```bash
sudo apt-get update && sudo apt-get install -y gdal-bin libgdal-dev libgeos-dev
```

#### Node Version Manager

To ensure the correct version of Node and NPM

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
source ~/.bashrc
```

#### DirENV

This loads the environment variables in the shell

_MacOS_

```bash
brew install direnv
echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc
source ~/.zshrc
```

_Ubuntu_

```bash
sudo apt-get install -y direnv
echo 'eval "$(direnv hook bash)"' >> ~/.bashrc
source ~/.bashrc
```

## Quickstart

1. Clone the repo to your local machine

```bash
git clone
```

2. Setup all the prerequisites
3. Create an .env using the template provided
4. Reset the environment

```bash
make reset
```

5. Run the development server

```bash
python manage.py runserver --settings=project.settings.local
```

If you use PyCharm, you can use the run file to run the dev server
