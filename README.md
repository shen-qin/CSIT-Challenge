# CSIT Software Engineering Mini Challenge 2023

This project implements a REST API using Falcon framework and Python, and uses MongoDB as the database. The API provides information about the cheapest flights and hotels available for given dates. This application is packaged with Docker and ready for deployment.

## Project Structure

- The main application code resides in `app.py`. This includes three routes:
  - `"/"`: a simple "Hello, World!" endpoint.
  - `"/flight"`: returns JSON data about the cheapest flight available for given dates.
  - `"/hotel"`: returns JSON data about the cheapest hotel available for given dates.
- `Dockerfile` describes the Docker image used to run the application.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

You will need to have Docker installed on your machine. To install Docker, follow the instructions on [Docker's official website](https://docs.docker.com/engine/install/).

### Setup

- Clone the repository to your local machine.
- Navigate to the project directory.

### Build Docker Image

To build the Docker image, run the following command in your terminal:

```bash
docker build -t csit_challenge .
```
### Run Docker Container

Once the Docker image has been built, you can run the Docker container with the following command:

```bash
docker run -p 8080:8080 csit_challenge
```
The server should now be up and running on your machine at http://localhost:8080.

### Usage

You can interact with the API using any HTTP client (like curl or Insomnia). Here are some example requests:

### Usage

You can interact with the API using any HTTP client (like curl or Postman). Here are some example requests:

To access the Hello World endpoint:

```bash
curl http://localhost:8080/
```

To get the cheapest flight:

```bash
curl "http://localhost:8080/flight?departureDate=YYYY-MM-DD&returnDate=YYYY-MM-DD&destination=CityName"
```

To get the cheapest hotel:

```bash
curl "http://localhost:8080/hotel?checkInDate=YYYY-MM-DD&checkOutDate=YYYY-MM-DD&destination=CityName"
```

Replace YYYY-MM-DD with the desired dates and CityName with the destination city.


## License

This project is licensed under the MIT License - see the `LICENSE.md` file for details.

## Acknowledgments

- CSIT for providing the opportunity to work on this project.
- Falcon and MongoDB for their robust platforms.
