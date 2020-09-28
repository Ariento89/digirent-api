# digirent

Supplier Administration Management

## Prerequisites
* Python 3.8.1
* Docker
* Docker Compose

## STACK
* Python3
* FastAPI
* PostgreSQL

## Instructions

To install application depencies, run: `make install`

To run unit tests, run: `make test`

To serve application run `make serve`

To reset application to a fresh state run `make reset` this will drop and remove all application containers

Visit `localhost:5000/docs` or `localhost:5000/redoc` for api documentation

Visit `localhost:5050` for pgadmin
