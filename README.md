# Adbrew Test - TODO app

A small TODO app: React frontend, Django REST API, MongoDB, all running in Docker.

- `GET /todos` returns every TODO from MongoDB
- `POST /todos` creates one
- The React app lists them and refreshes the list after every submit

## Running it

You need Docker with the Compose plugin.

```
git clone https://github.com/satyam-code45/adb_test.git
cd adb_test
docker compose build
docker compose up -d
```

`docker ps` should show three containers: `api`, `app` and `mongo`.

- App: http://localhost:3000 (first start takes a minute or two while `yarn install` runs, check `docker logs -f app`)
- API: http://localhost:8000/todos

`ADBREW_CODEBASE_PATH` still works like in the original setup, but it's optional now and defaults to `./src`.

Stop everything with `docker compose down`. Todos are kept in the `mongo_data` volume; `docker compose down -v` wipes them.

## Tests

With the containers running:

```
docker exec api bash -c "cd /src/rest && python manage.py test"
docker exec -e CI=true app bash -c "cd /src/app && yarn test --watchAll=false"
```

The API tests cover validation, the view (with a fake repository), routing for both `/todos` and `/todos/`, and the repository itself against the real mongo container, in a separate `test_db_tests` database that gets dropped afterwards. The app tests mock the API module and check loading, creating, refreshing and error states.

## API

### `GET /todos`

`200`, oldest first:

```json
[
  {
    "id": "6ac39e4cc35b160fa4eccfd4",
    "description": "Learn Docker",
    "created_at": "2026-10-05T12:55:40.115000+00:00"
  }
]
```

### `POST /todos`

Body:

```json
{ "description": "Learn Docker" }
```

| Status | When |
|---|---|
| `201` | Created, returns the new todo in the same shape as above |
| `400` | `description` missing, not a string, blank, or over 200 characters, e.g. `{"description": ["This field may not be blank."]}` |
| `400` | Body isn't valid JSON, or isn't a JSON object, e.g. `{"non_field_errors": ["Request body must be a JSON object."]}` |
| `415` | Body isn't `application/json` |
| `503` | MongoDB can't be reached, `{"detail": "Database is unavailable, please try again later."}` |

Both `/todos` and `/todos/` work.

## Project structure

```
src/
  rest/                     Django project
    rest/
      db.py                 the one MongoClient, configured from MONGO_HOST / MONGO_PORT
      exceptions.py         maps pymongo errors to a 503
      settings.py, urls.py
    todos/
      repository.py         TodoRepository - the only code that talks to mongo
      validators.py         request body validation
      views.py              TodoListView - validate, call the repository, respond
      urls.py
      tests.py
  app/src/                  React app
    api/todos.js            fetch wrapper: fetchTodos, createTodo
    hooks/useTodos.js       todos state, loading/error, addTodo (create + refetch)
    components/TodoList.js
    components/TodoForm.js
    App.js                  puts the two components together
```

Why it's split this way:

- **Views don't know about mongo.** They go through `TodoRepository`, so the view can be tested with a fake repository and the storage could change without touching HTTP code. The repository also converts `ObjectId` and `datetime` into JSON-friendly values in one place.
- **Validation is separate from the view**, and raises DRF's `ValidationError`, so DRF turns it into a `400` on its own.
- **Mongo errors are handled once**, in a custom DRF exception handler, instead of a `try/except` in every view method.
- **`todos` is its own Django app**, so a new resource would be a new app next to it rather than more code in `rest/`.
- On the frontend, **components only render**. Fetching lives in `api/`, state lives in the `useTodos` hook. Everything uses hooks, no class components.

## How the Docker setup works

`docker-compose.yml` runs three services on the default Compose network:

- **mongo** - official `mongo:4.4` image. Data goes into the `mongo_data` named volume, so it survives restarts.
- **api** - built from the `Dockerfile` (`python:3.8-slim` plus `requirements.txt`). `.dockerignore` keeps the build context down to `requirements.txt`, so `node_modules` isn't sent to Docker on every build. The code isn't copied into the image; `src/` is bind-mounted at `/src`, so `runserver` reloads when a file changes. `MONGO_HOST=mongo` works because Compose gives every service a DNS name on its network.
- **app** - official `node:16` image, with `src/` mounted as well. It runs `yarn install && yarn start` on start, which is why the first start is slow.

All three publish their port to the host. The browser loads the app from `localhost:3000` and calls the API on `localhost:8000`. That's a different origin, so the API sends CORS headers (`django-cors-headers`). Inside Docker, only the API talks to mongo, over the Compose network.

## Problems with the original setup and how I fixed them

The setup as given didn't build or start. In the order I hit them:

1. **`apt-get install mongodb-org` failed** with `Depends: libssl1.1 but it is not installable`. The MongoDB 4.4 apt repo is for Debian buster, but `python:3.8` is now based on Debian bookworm, which doesn't have `libssl1.1`. Also, every service was built from the same image, so the mongo container was a full Python + Node image just to run `mongod`. **Fix:** the mongo service uses the official `mongo:4.4` image. I kept 4.4 because that's what the original installed and it's supported by the pinned `pymongo==3.11.2`.
2. **`RUN easy_install pip` failed.** `easy_install` doesn't exist in the current image, and pip already comes with it. **Fix:** removed the step.
3. **The React app crashed on start** with `ERR_PACKAGE_PATH_NOT_EXPORTED` from postcss. Installing yarn through apt pulled in Node 18, and `react-scripts` 4 (webpack 4) doesn't run on Node 17+. **Fix:** the app service uses the official `node:16` image, and yarn is no longer installed in the API image.
4. **`POST /todos` without the trailing slash** makes Django raise a `RuntimeError` (with `DEBUG` on), because `APPEND_SLASH` can't redirect a POST without losing the body. **Fix:** the route accepts both forms.
5. **Django created an SQLite file** (`src/rest/mydatabase`) on every start even though nothing used it. **Fix:** `DATABASES = {}`.
6. **The api image was 1.46 GB.** It installed nginx, git, nano and the yarn repo, and `requirements.txt` pulled in Jupyter, pandas, matplotlib and Celery, none of which the API uses. **Fix:** `python:3.8-slim` and only the packages the code imports, which brings it to about 160 MB.
7. **`127.0.0.1:8000` returned 400** because `ALLOWED_HOSTS` only had `localhost`. **Fix:** added `127.0.0.1`.
8. **Leftover template settings.** `settings.py` still installed `admin`, `auth`, `sessions` and `messages` (all of which need a SQL database), printed `BASE_DIR` on every command and had unused imports. **Fix:** removed them. DRF's default anonymous user comes from `django.contrib.auth`, so `UNAUTHENTICATED_USER` is set to `None`.
9. Smaller things: removed the obsolete `version` key, replaced `links` with `depends_on`, `yarn install --frozen-lockfile` so installs match `yarn.lock`, removed the unused `ENV_TYPE`, CRA logo and CRA README, and ignored `__pycache__`, `.eslintcache` and `src/tmp/` in git.

## What I'd add next

- Update and delete endpoints (`PATCH` / `DELETE /todos/<id>`)
- Pagination on `GET /todos` once the list can get large
- An index on `(created_at, _id)` to back the sort
- Auth, so each user only sees their own todos
- Moving off Python 3.8, Django 3.0, Node 16 and MongoDB 4.4, which are all past end of life
- Production settings, which I left as the original setup had them: `DEBUG` off, `SECRET_KEY` from an env var, CORS limited to the frontend origin instead of all origins with credentials, and gunicorn instead of `runserver`
