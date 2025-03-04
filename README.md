# Blob Storage

This was a fun project to create a file upload webpage where a user could drag and drop a file and save it in a database. The project uses fastAPI and SQLite as the backend with an HTML frontend.

# Setup

To run locally create a virtual environment with:

```
python -m venv venv && pip install -r requirements.txt
```

You can then either run locally with:

```
fastapi dev app/main.py
```

Or deploy with Docker and the pre-configured shell scripts.

```sh
./deploy.sh
```

You might need to make this file executable to run.

## HTTPS

There are features of this app that utilize the `navigator` api from the browser. This is only available through HTTPS rather than HTTP. Because of this dependency a certificate needs to be issued for running in Docker over HTTPS. This is done through a self-signed certificate for development.

Running the following to create a `certs/` folder to hold a private key file and full chain file. These are copied into the Docker app when deployed.

```sh
mkdir -p certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout certs/privkey.pem -out certs/fullchain.pem
```

## Dockerfile

During development the docker image can be rebuilt and redeployed with the `deploy.sh` file. You may want to change the name of the image or container as it suits the project. The Docker container can be stopped with `stop.sh` but make sure the container name is consistent between these two files.

