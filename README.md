# Recommender System API

The Recommender System API is a general-purpose recommendation engine that provides API endpoints for managing items, users, events, and generating recommendations. It's built using Python's FastAPI and SQLite, and incorporates collaborative filtering and content-based recommendation models to provide real-time and personalized item recommendations.

## Features

- CRUD operations for managing items, users and events.
- Real-time recommendation using collaborative filtering and content-based models.
- Customizable recommendation parameters.
- Endpoints for monitoring system stats.


## Accessing the API

The API is accessible at the endpoint [http://serpentinecoder.pythonanywhere.com/](https://recsysapi-cz0t.onrender.com/). Users can interact with the API, performing actions such as adding, removing, and fetching items. The API can also be used to generate recommendations.

## Example Inputs

`items.json` and `users.json` are the files that provide examples of the format that the API accepts.


Before making POST requests, ensure that the JSON payload matches the structure provided in these examples.


## Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.8 or higher.
- SQLite3.

## Setting up Recommender System API

To set up the Recommender System API, follow these steps:

1. Clone the repository:

    ```
    git clone https://github.com/<your username>/recommender-system-api.git
    ```

2. Navigate to the cloned directory:

    ```
    cd recommender-system-api
    ```

3. Create a virtual environment (Optional but recommended):

    ```
    python3 -m venv env
    source env/bin/activate
    ```

4. Install the required packages:

    ```
    pip install -r requirements.txt
    ```

## Running the API

After setting up the project, you can run the API locally with:

```
uvicorn app:app --reload
```

### Running with Docker

Alternatively, you can run the application inside a Docker container. Follow these steps to build and run the Docker container:

1. Build the Docker image:

    ```
    docker build -t recommender-system-api .
    ```

2. Run the Docker container:

    ```
    docker run -p 8000:8000 recommender-system-api
    ```

By default, the API will be accessible at `http://localhost:8000/`.

## API Documentation

After running the server, you can view the API documentation in your web browser at `http://localhost:8000/docs`

## API Endpoints

Here are some of the key API endpoints:

- `/items` (GET): Retrieve all items from the database.
- `/users` (GET): Retrieve all users from the database.
=- `/user` (GET): Retrieve a specific user's data from the database.
- `/item/events` (GET): Retrieve all events associated with a specific item.
- `/user/events` (GET): Retrieve all events associated with a specific user.

- `/item` (DELETE): Delete a specific item from the database.
- `/user` (DELETE): Delete a specific user from the database.
- `/clear_db` (DELETE): Delete all data from the database.

- `/item/{item_id}` (PUT): Update a specific item in the database.
- `/user/{user_id}` (PUT): Update a specific user's data in the database.


The API also includes a `/docs` endpoint that provides a user-friendly interface for exploring and testing the API's endpoints. This is an automatically generated API documentation that describes all the endpoints, their methods, parameters, and responses.

The `/docs` endpoint is accessible by simply appending `/docs` to the API's base URL (e.g., `http://localhost:8000/docs` if the API is running locally on port 8000). This endpoint uses the OpenAPI (formerly Swagger) specifications to generate a comprehensive documentation for the API.

I have also included a postman collection that should make testing easier through the file recsys.postman_collection.json.

## Collaborative Filtering and Content-Based Filtering

In this project, we use two types of recommendation systems - Collaborative Filtering and Content-Based Filtering. Here is how they work and how you can use the codes provided:

### Collaborative Filtering

This recommendation system is based on users' past behavior. We use a method known as Nearest Neighbors, which operates under the assumption that if two items A and B are liked by a significant number of users, then they are similar and this forms the basis for recommending them.

To use this script, you can call the `start(nrec,sel_item)` function where `nrec` is the number of recommendations you want and `sel_item` is the item based on which you want the recommendations.

The script will fetch item and user data from a SQLite database, build a user-item matrix, and use a k-nearest neighbors (k-NN) model to find similar items based on cosine similarity.

This function will return a JSON response that contains the total execution time, the time taken for data processing and recommendation generation, and a list of recommended items.

### Content-Based Filtering

This recommendation system is based on the description and attributes of the items. In this case, we transform the item descriptions and tags into a matrix of TF-IDF features. Then, we compute the similarity of these items based on their feature vectors.

To use this script, you can call the `start(dbn, itid, nitems)` function where `dbn` is the database number, `itid` is the item id for which you want recommendations, and `nitems` is the number of recommendations you want.

This function will return a list of recommended items along with the time taken for data processing, recommendation generation, and the total execution time.

Please ensure that you have the necessary libraries installed and the required data in a SQLite database for these scripts to work properly.

**Note:**

1. Both systems are built with scalability in mind, but keep in mind that recommendation systems are resource-intensive and could be slow depending on the size of your dataset and the hardware you are running these scripts on.

2. The output of the recommendation systems might vary depending on the user behavior and item attributes.

3. The quality of recommendations depends on the quality and quantity of data. More data generally leads to better recommendations.

4. The current implementations use basic versions of Collaborative Filtering and Content-Based Filtering. There are more advanced techniques and improvements that can be incorporated to improve the recommendations.

# Recsys API Guide

This guide provides instructions on how to interact with the Recsys API.

## Clear the Database

Use the following `DELETE` request to clear the database.

```sh
curl -X DELETE http://localhost:8000/clear_db
```

## Add Items

Items can be added to the database with a `POST` request as shown below:

```sh
curl -X POST http://localhost:8000/item -d @items.json -H "Content-Type: application/json"
```

The `items.json` file should have the following structure:

```json
{
    "items": [
        {
            "itemId": "1",
            "title": "Statue of Liberty",
            "description": "A colossal neoclassical sculpture on Liberty Island in New York Harbor",
            "tag": ["USA", "New York", "Monument"]
        },
        ...
    ]
}
```

## Fetch Items

To fetch items from the database, use the following `GET` request:

```sh
curl -X GET http://localhost:8000/items
```

## Add Users

Users can be added to the database with a `POST` request:

```sh
curl -X POST http://localhost:8000/user -d @users.json -H "Content-Type: application/json"
```

The `users.json` file should have the following structure:

```json
{
    "items": [
        {
            "userId": 1,
            "itemId": 1,
            "rating": 3.5,
            "timestamp": 1112486027
        },
        ...
    ]
}
```

## Fetch Users

To fetch users from the database, use the following `GET` request:

```sh
curl -X GET http://localhost:8000/users
```

## Make Recommendations

You can make recommendations using either Collaborative Filtering or Content-based Filtering.

### Collaborative Filtering

To get recommendations using Collaborative Filtering for a specific user, send a `GET` request to `/recommend/collab/userId` replacing `userId` with the id of the user.

```sh
curl -X GET http://localhost:8000/recommend/collab/1
```

### Content-Based Filtering

To get recommendations using Content-based Filtering for a specific user, send a `GET` request to `/recommend/content/userId` replacing `userId` with the id of the user.

```sh
curl -X GET http://localhost:8000/recommend/content/1
```


## Experiment Questions

As part of my master's degree project, I would greatly appreciate your feedback on the Recommender System API. Your input will help me evaluate the effectiveness of the system and identify areas for improvement. Please take a moment to answer the following questions:

1. How would you rate the overall performance and responsiveness of the API?
2. Were you able to successfully set up and run the API using the provided instructions?
3. Did you encounter any difficulties or issues while interacting with the API or running the scripts?
4. Did you find the API documentation and the provided examples clear and helpful?
5. Were you able to understand and utilize the Collaborative Filtering and Content-Based Filtering recommendation systems effectively?
6. Did the recommendations generated by the system align with your expectations? Were they useful and relevant?
7. Were there any specific features or functionalities that you felt were missing from the API?
8. Do you have any suggestions for improving the API or the recommendation systems?
9. How does the Recommender System API compare to other recommender system APIs you may have used in the past? Please provide your insights and comparisons regarding the features, usability, performance, and any other aspects you consider relevant when comparing the Recommender System API to other similar APIs you have worked with.

Your feedback is invaluable to me, and I appreciate you taking the time to help me with my project. If you have any additional comments or insights, please feel free to share them. Thank you!

# Project TODOs

Here is a list of potential improvements and future directions for the project.

- [ ] **Security Integration:** Implement JWT (JSON Web Tokens) for secure transmission of information as a JSON object. This could be used to verify and authenticate requests and manage user sessions.

- [ ] **Database Upgrade:** Replace the current SQLite-based setup with a more robust and scalable database system. Options could include PostgreSQL for relational data or NoSQL alternatives like MongoDB for more flexible data structures.

- [ ] **Hardware Acceleration:** Add support for hardware acceleration (e.g., GPUs, TPUs) to speed up computation of recommendations. This could be achieved through integration with libraries like TensorFlow, PyTorch, or Rapids.

- [ ] **Library Migration (Pandas to Polars):** Migrate from the Pandas library to the newer and more performant Polars library for data manipulation and analysis. This should improve the speed and memory efficiency of data processing operations.

Each of these improvements would contribute significantly to the scalability, performance, and functionality of the project. However, they also each present their own unique challenges and complexities, and should be carefully planned and implemented.


## License

This project uses the following license: GPL3 License.

## Disclaimer

This project is currently in the development stage and might be subject to changes.

