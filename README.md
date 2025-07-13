# Car Rental System

A simple Flask-based car rental API with user and merchant roles, powered by PostgreSQL. You can run it locally or containerized with Docker.

## Table of Contents

* [Features](#features)
* [Prerequisites](#prerequisites)
* [Configuration](#configuration)
* [Running Locally](#running-locally)
* [Running with Docker](#running-with-docker)
* [API Documentation](#api-documentation)
* [Postman Collection](#postman-collection)

## Features

* User registration and login (Basic Auth)
* Role-based endpoints for **users** and **merchants**
* CRUD operations on cars (merchants)
* Create and return rentals (users)
* Paginated listing endpoints
* Database migrations with Flask-Migrate

## Prerequisites

### Local Setup

* Python 3.10+
* `pip` (comes with Python)
* PostgreSQL (e.g. `psql` CLI)

### Docker Setup

* Docker Engine
* Docker Compose

## Configuration

Create a `.env` file in the project root with:

```bash
DATABASE_URL=postgresql://postgres:<DB_PASSWORD>@localhost:5432/car_rental
FLASK_APP=app.py
FLASK_ENV=development
```

* **DATABASE\_URL**: Your Postgres connection string
* **MERCHANT\_SECRET**: Secret key required for merchant sign-up
* **FLASK\_APP** and **FLASK\_ENV**: Flask settings

## Running Locally

1. **Clone the repo**:
````

git clone -b main https://github.com/ktekik01/car_rental.git 

cd car\_rental\_system

````

2. **Set up a Python virtual environment**:

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\\Scripts\\activate
````

3. **Install dependencies**:

````

pip install -r requirements.txt

````

4. **Initialize the database**:

```bash

psql -U postgres -c "CREATE DATABASE car_rental;"
flask db init       # only first-time
flask db migrate -m "Initial schema"
flask db upgrade
````

5. **(Optional) Seed data strongly recommended**:
````

python seed.py

````

6. **Run the server**:

```bash
flask run
````

Your API will be live at `http://localhost:5000`.

## Running with Docker

0. **Important note: Probably, you won't be able to see your data on 
pgAdmin since you have a server running on  port5432. Change your db server's port on pgAdmin from port5432 to port5433. 

0. ** Thereby, you can see your data on pgAdmin

1. **Build & start containers**:

````

docker-compose up -d

````

2. **Wait for Postgres to be ready**, then inside the `web` container run migrations & optional seed:

```bash
docker-compose exec web flask db upgrade
# Optional seed
# docker-compose exec web python seed.py
````

3. **Access the API** at `http://localhost:5000`.

4. **Stop containers**:

```
docker-compose down

```

## API Documentation

All endpoints use Basic Authentication. Register (`POST /register`) and then include your credentials in subsequent requests.

Core endpoints:

Auth

POST /register – register a new user or merchant

POST /login – verify credentials (Basic-Auth)

Cars

GET /cars – list all cars (paginated)

POST /cars – create a new car (merchant only)

PUT /cars/:car_id – update a car (merchant only)

DELETE /cars/:car_id – delete a car (merchant only)

GET /merchants/:merchant_id/cars – list any merchant’s cars (paginated)

Rentals

POST /rentals – create a rental (user only)

PUT /rentals/:rental_id/return – return your rental (user only)

GET /merchants/me/rentals – view rentals of your cars (merchant only)

GET /users/:user_id/rentals – view your rental history (user only)

Refer to the Postman collection for examples.

## Postman Collection

Import the following URL into Postman to load all requests (replace with your published link):

```

https://planetary-station-855740.postman.co/workspace/My-Workspace~b9a192d7-ad9c-4716-8cbc-8beda5d9fca4/collection/42228276-bc2100b6-ceac-46ac-941f-15d737cd3c49?action=share&creator=42228276

```
```
I strongly recommend you to run seed.py before testing the API with Postman collection. Thereby, you can have some data to benefit from.
