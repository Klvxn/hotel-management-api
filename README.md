## Hotel Management API

The Hotel Management API is a RESTful web service that allows you to manage hotel reservations, rooms, guests, and reviews. This README provides an overview of the API's functionality and how to use it.

### Table of Contents

1. [Installation](#installation)
2. [Usage](#usage)
3. [API Endpoints](#api-endpoints)
4. [Authentication](#authentication)
5. [Data Models](#data-models)
6. [Contributing](#contributing)
7. [License](#license)

### Installation

To use the Hotel Management API, you'll need Python 3.8 or higher. You can set up the API locally by following these steps:

1. Clone this repository:

```
git clone https://github.com/Klvxn/hotel-management-api
```

2. Create a virtual environment:

```
python -m venv venv
```

3. Activate the virtual environment:

    - Windows:

        ```
        .\venv\Scripts\activate
        ```

   - macOS and Linux:

        ```
        source venv/bin/activate
        ```

4. Install the required dependencies:

```
pip install -r requirements.txt
```

5. Configure the database connection in `config.py`.

6. Run the API:

```
uvicorn main:app --reload
```

### Usage

Once the API is up and running, you can interact with it using HTTP requests. You can use tools like `curl`, [Postman](https://www.postman.com/), or write your own code to make requests to the API endpoints.

### API Endpoints

The API provides the following endpoints:

- **Rooms**: CRUD operations for managing hotel rooms.
- **guests**: CRUD operations for managing guest information.
- **Reservations**: Create and manage reservations for hotel rooms.
- **Reviews**: Create and view reviews for hotel rooms.

Brief descriptions of each endpoint are provided below.

    Room end points

    Endpoints for rooms are as follows:
        - GET /rooms: Get all rooms
        - POST /rooms: Create a new room
        - GET /rooms/{room_id}: Get a single room
        - PUT /rooms/{room_id}: Update a single room
        - DELETE /rooms/{room_id}: Delete a single room
        - GET /rooms/{room_id}/reservations: Get all reservations for a room
        - GET /rooms/{room_number}/guests: Get all guests for a room
        - GET /rooms/{room_number}/reviews: Get all reviews for a room
        - GET /rooms/{room_number}/invoices: Get all invoices for a room

    
    Reservation end points

    Endpoints for reservations are as follows:
        - GET /reservations: Get all reservations    
        - POST /reservations: Create a new reservation
        - GET /reservations/{reservation_id}: Get a single reservation
        - PUT /reservations/{reservation_id}: Update a single reservation
        - DELETE /reservations/{reservation_id}: Delete a single reservation
        - PUT /reservations/{reservation_id}/checked_out: Update a reservation to checked out

    

    

For detailed information on each endpoint, see the [API documentation](#api-documentation).

### Authentication

The API uses token-based authentication. To access protected endpoints, you need to obtain an access token by authenticating with valid credentials.

### Data Models

The API uses the following data models:

- `Room`: Represents hotel rooms.
- `guest`: Represents guest information.
- `Reservation`: Represents reservations made by guests.
- `Review`: Represents reviews for hotel rooms.
- `Invoice`: Represents invoice for payments.


### Contributing

We welcome contributions to improve this API. If you have suggestions, bug reports, or want to add new features, please submit a pull request or open an issue.

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
