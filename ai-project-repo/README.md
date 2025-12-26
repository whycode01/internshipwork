# AI Project Repo

## Running with Docker Compose

This project uses Docker Compose to build and run all services (`anony-api`, `backend`, and `frontend`) together.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed
- [Docker Compose](https://docs.docker.com/compose/install/) installed

### Steps

1. **Clone the repository**  
   ```sh
   git clone <your-repo-url>
   cd ai-project-repo
   ```

2. **Build and start all services**  
   ```sh
   docker compose up --build
   ```

3. **Access the Application**  
    [http://localhost:4173](http://localhost:4173)

### Stopping the services

```sh
docker compose down
```

---

**Note:**
Docker handles dependencies for each service.