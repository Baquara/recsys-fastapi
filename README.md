# Recommender System API

A general-purpose recommendation engine built with **FastAPI** and **SQLite**. Supports collaborative filtering, content-based filtering, hybrid recommendations, and a self-configuring endpoint that automatically selects the best algorithm based on available data.

## Algorithms

| Endpoint | Algorithm | Best for |
|---|---|---|
| `GET /recommendations/collaborative` | KNN cosine similarity on the user–item matrix | Rich rating history |
| `GET /recommendations/content-based` | TF-IDF cosine similarity on description + tags | Cold-start / new items |
| `GET /recommendations/hybrid` | Weighted combination of both (configurable α) | Sparse data |
| `GET /recommendations/auto` | Self-configuring — infers the best method from data | General use |

### Self-configuring logic (`/auto`)

The `/auto` endpoint inspects the seed item's rating count and picks the algorithm automatically:

| Ratings for seed item | Method chosen |
|---|---|
| 0 | `content_based` — no behavioural signal yet |
| 1 – `HYBRID_THRESHOLD-1` | `hybrid` — sparse signal, combine both |
| ≥ `HYBRID_THRESHOLD` | `collaborative` — sufficient rating history |

The response always includes `method`, `reason`, and `ratings_count` so the decision is fully transparent.

## Project structure

```
.
├── app/
│   ├── main.py              # App factory and router registration
│   ├── config.py            # All settings, loaded from env vars with defaults
│   ├── database.py          # SQLAlchemy engine, session, Base
│   ├── models/              # ORM models (Item, UserRating, Event)
│   ├── schemas/             # Pydantic request/response schemas
│   ├── repositories/        # Data-access layer (SQL queries)
│   ├── services/            # Business logic
│   └── routers/             # HTTP controllers (items, users, events, recommendations, admin)
├── recommenders/
│   ├── collaborative.py     # KNN collaborative filtering
│   ├── content_based.py     # TF-IDF content-based filtering
│   └── hybrid.py            # Weighted hybrid
├── data/
│   ├── db0.db               # SQLite database (git-ignored)
│   ├── items.json           # Sample item payload
│   ├── users.json           # Sample ratings payload
│   └── items/               # Domain-specific item catalogues (food, movies, marketplace)
├── docs/
│   ├── api.png              # API screenshot
│   ├── Experimento.md       # Experiment notes
│   └── recsys.postman_collection.json
├── .env.example             # All available environment variables with defaults
├── Dockerfile
├── requirements.txt
└── run.py                   # Entry point
```

## Setup

**Requirements:** Python 3.10+

```bash
git clone https://github.com/<your-username>/recommender-system-api.git
cd recommender-system-api

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

## Running

```bash
# directly
uvicorn app.main:app --reload

# or via the entry point
python run.py
```

### Docker

```bash
docker build -t recsys-api .
docker run -p 8000:8000 recsys-api
```

The API and its interactive docs are available at `http://localhost:8000/docs`.

## Configuration

All tunable parameters are read from environment variables. Copy `.env.example` to `.env` and adjust as needed — every variable has a default so the app works out of the box without a `.env` file.

```bash
cp .env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/db0.db` | DB connection string |
| `APP_HOST` | `0.0.0.0` | Server host |
| `APP_PORT` | `8000` | Server port |
| `APP_RELOAD` | `false` | Enable auto-reload (dev only) |
| `HYBRID_THRESHOLD` | `5` | Min ratings to prefer collaborative over hybrid |
| `HYBRID_ALPHA` | `0.5` | Collaborative weight in the hybrid score |
| `HYBRID_POOL_MULTIPLIER` | `3` | Candidate pool = nrec × multiplier |
| `FUZZY_MATCH_THRESHOLD` | `60` | Min fuzz ratio (0–100) for title matching |
| `COLLAB_POPULARITY_THRESHOLD` | `1` | Min ratings an item needs to enter the matrix |
| `COLLAB_ACTIVITY_THRESHOLD` | `1` | Min ratings a user needs to enter the matrix |
| `COLLAB_MAX_RATINGS` | `2000000` | Memory cap on ratings loaded |
| `COLLAB_N_NEIGHBORS` | `20` | k for the KNN model |
| `CONTENT_NGRAM_MAX` | `3` | Upper bound of TF-IDF n-gram range |
| `CONTENT_MIN_DF` | `1` | Min document frequency for TF-IDF terms |

## API endpoints

### Items

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/items` | List all items |
| `POST` | `/items` | Add items (batch) |
| `GET` | `/items/{item_id}` | Get a single item |
| `PUT` | `/items/{item_id}` | Update an item |
| `DELETE` | `/items/{item_id}` | Delete an item |

### Users (ratings)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/users` | List all ratings |
| `POST` | `/users` | Add ratings (batch) |
| `GET` | `/users/{user_id}` | Get ratings for a user |
| `PUT` | `/users/{user_id}` | Update ratings for a user |
| `DELETE` | `/users/{user_id}` | Delete all ratings for a user |

### Events (implicit feedback)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/events` | List events (filter by `?user_id=` or `?item_id=`) |
| `POST` | `/events` | Record an event |

### Recommendations

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/recommendations/collaborative` | KNN collaborative filtering |
| `GET` | `/recommendations/content-based` | TF-IDF content-based filtering |
| `GET` | `/recommendations/hybrid` | Weighted hybrid (param: `alpha`) |
| `GET` | `/recommendations/auto` | Self-configuring |

### Admin

| Method | Endpoint | Description |
|---|---|---|
| `DELETE` | `/admin/database` | Wipe all tables |
| `GET` | `/admin/system` | Server resource usage |

## Typical workflow

**1. Load the catalogue**
```bash
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d @data/items.json
```

**2. Load ratings**
```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d @data/users.json
```

**3. Get recommendations**
```bash
# Let the system choose the algorithm automatically
curl "http://localhost:8000/recommendations/auto?sel_item=Eiffel+Tower&nrec=5"

# Or pick an algorithm explicitly
curl "http://localhost:8000/recommendations/collaborative?sel_item=Eiffel+Tower&nrec=5"
curl "http://localhost:8000/recommendations/content-based?item_index=1&n=5"
curl "http://localhost:8000/recommendations/hybrid?sel_item=Eiffel+Tower&nrec=5&alpha=0.6"
```

The `sel_item` parameter uses fuzzy matching, so partial or approximate titles are accepted.

## Experiment questions

As part of a master's degree research project, feedback on the API is greatly appreciated. Please take a moment to answer the following questions:

1. How would you rate the overall performance and responsiveness of the API?
2. Were you able to successfully set up and run the API using the provided instructions?
3. Did you encounter any difficulties or issues while interacting with the API or running the scripts?
4. Did you find the API documentation and the provided examples clear and helpful?
5. Were you able to understand and utilize the recommendation systems effectively?
6. Did the recommendations generated by the system align with your expectations? Were they useful and relevant?
7. Were there any specific features or functionalities that you felt were missing from the API?
8. Do you have any suggestions for improving the API or the recommendation systems?
9. How does this API compare to other recommender system APIs you may have used in the past? Please share insights on features, usability, performance, or any other relevant aspects.

Your feedback is invaluable. If you have any additional comments, please feel free to share them. Thank you!

## License

MIT
