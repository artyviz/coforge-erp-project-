# University Management System

A comprehensive full-stack application for managing university operations, including student enrollment, course management, faculty assignments, and analytics. Built with Python for core logic and ETL processes, Rust for high-performance API services, and a Flask-based web application for user interaction.

## Features

- **Student Management**: Register, update, and track student information.
- **Course Management**: Create and manage courses across departments.
- **Department Management**: Organize academic departments and their faculty.
- **Enrollment Tracking**: Handle student enrollments in courses.
- **Faculty Management**: Assign and manage faculty members.
- **ETL Pipeline**: Extract, transform, and load data for analytics.
- **Analytics Service**: Generate insights on enrollments, performance, etc.
- **RESTful API**: High-performance Rust-based API for backend operations.
- **Web Dashboard**: User-friendly web interface for administration.
- **Docker Support**: Containerized deployment for easy scaling.

## Tech Stack

- **Backend Core**: Python 3.x
  - ETL: Custom pipeline for data processing
  - Models: Pydantic or similar for data validation
  - Services: Business logic layer
  - Repositories: Data access layer
- **API**: Rust (Actix-web or similar)
- **Web App**: Flask (Python)
- **Database**: SQL (PostgreSQL/MySQL)
- **Containerization**: Docker & Docker Compose
- **Testing**: Pytest for Python components

## Prerequisites

- Python 3.8+
- Rust 1.50+
- Docker & Docker Compose
- Git

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/university-management-system.git
   cd university-management-system
   ```

2. **Set up Python environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r web_app/requirements.txt
   ```

3. **Set up Rust environment**:
   ```bash
   cd rust_api
   cargo build
   cd ..
   ```

4. **Set up the database**:
   - Ensure you have a database server running (e.g., PostgreSQL).
   - Run the initialization scripts:
     ```bash
     # Assuming you have psql or similar
     psql -U your_user -d your_db < database/init.sql
     psql -U your_user -d your_db < database/seed.sql
     ```

5. **Configure environment variables**:
   - Copy `.env.example` to `.env` and fill in your database credentials, API keys, etc.

## Usage

### Running with Docker Compose (Recommended)

```bash
docker-compose up --build
```

This will start all services: database, Rust API, and web app.

### Running Locally

1. **Start the database** (if not using Docker).

2. **Run the Rust API**:
   ```bash
   cd rust_api
   cargo run
   ```

3. **Run the web app**:
   ```bash
   cd web_app
   flask run
   ```

4. **Access the application**:
   - Web app: http://localhost:5000
   - API: http://localhost:8080 (adjust port as per config)

### Running ETL Pipeline

```bash
python main.py
```

## API Endpoints

The Rust API provides the following endpoints:

- `GET /health` - Health check
- `GET /students` - List students
- `POST /students` - Create student
- `GET /courses` - List courses
- `POST /courses` - Create course
- `GET /departments` - List departments
- `POST /departments` - Create department
- `GET /faculty` - List faculty
- `POST /faculty` - Create faculty
- `GET /enrollments` - List enrollments
- `POST /enrollments` - Create enrollment
- `GET /analytics` - Get analytics data

For detailed API documentation, refer to the handlers in `rust_api/src/handlers/`.

## Testing

Run the test suite:

```bash
pytest tests/
```

## Project Structure

```
.
├── database/          # SQL scripts for DB setup
├── python_core/       # Core Python modules
│   ├── etl/          # ETL pipeline
│   ├── models/       # Data models
│   ├── repository/   # Data access
│   ├── services/     # Business logic
│   └── utils/        # Utilities
├── rust_api/         # Rust API server
├── web_app/          # Flask web application
├── tests/            # Test files
├── docker-compose.yml # Docker orchestration
└── README.md         # This file
```

## Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

