# Basics of FastAPI

This is a full-stack AI tool project consisting of:

React frontend
FastAPI backend (Python)
PostgreSQL database
Docker Compose setup for easy deployment

---

##  Tech Stack

* **Frontend:** React (with Node.js)
* **Backend:** FastAPI (Python)
* **Database:** PostgreSQL
* **Containerization:** Docker & Docker Compose

---

##  How to Run the Project

### Prerequisites

* [Docker](https://www.docker.com/products/docker-desktop) installed
* [Git](https://git-scm.com/downloads) installed

---

##  Steps to Run with Docker

1. **Clone the repository**

```bash
git clone https://github.com/harsh-kasana-work/ai-tool.git
cd ai-tool
```

2. **Build & Run all services**

```bash
docker-compose up --build
```

---

##  Access the Application

* **Frontend:** [http://localhost:3000](http://localhost:3000)
* **Backend API:** [http://localhost:8000](http://localhost:8000)
* **PostgreSQL Database:** running on port `5432` (can be connected via tools like `pgAdmin`)

---

##  Development Notes

* Frontend React development server runs inside Docker on port `3000`
* Backend FastAPI server runs inside Docker on port `8000`
* PostgreSQL persists data via Docker volume

---

##  Useful Commands

* **Stop containers:**
  `docker-compose down`

* **Stop & remove containers + volumes:**
  `docker-compose down -v`

* **Rebuild containers:**
  `docker-compose up --build`

---

##  Project Structure

```
.
├── backend/      # FastAPI backend code  
├── frontend/     # React frontend code  
├── docker-compose.yml  
└── README.md  
```

---

##  Additional Notes

* Node modules are included in the frontend folder if needed inside Docker.
* `.gitignore` is set to exclude unnecessary files (except frontend's node\_modules if explicitly included).
* Adjust environment variables inside `docker-compose.yml` as needed.

