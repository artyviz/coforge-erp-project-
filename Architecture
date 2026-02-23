#high level architecture


university_erp/
│── config/
│   └── settings.yaml                # DB config, server config, environment
│
│── core/
│   ├── base.py                      # Abstract Base Classes
│   ├── models/                      # OOP models (pure Python classes)
│   │   ├── student.py
│   │   ├── course.py
│   │   ├── department.py
│   │   ├── faculty.py
│   │   ├── enrollment.py
│   │   └── grade.py
│   │
│   ├── repository/                  # Python OOP "database layer"
│   │   ├── base_repository.py
│   │   ├── student_repo.py
│   │   ├── course_repo.py
│   │   ├── department_repo.py
│   │   └── enrollment_repo.py
│   │
│   ├── services/                    # Business logic layer (Domain services)
│   │   ├── student_service.py
│   │   ├── enrollment_service.py
│   │   └── analytics_service.py
│   │
│   ├── extractor.py                 # ETL Extractor base + implementations
│   ├── transformer.py               # ETL Transformer base + implementations
│   ├── loader.py                    # ETL Loader for DB / CSV / JSON
│   └── validator.py                 # Schema Validation + Quality checks
│
│── api/                             # Server Layer
│   ├── server.py                    # Python FastAPI or Rust Axum server
│   ├── routers/
│   │   ├── students.py
│   │   ├── courses.py
│   │   ├── departments.py
│   │   └── enrollment.py
│   └── dto/                         # Data Transfer Objects
│       ├── student_dto.py
│       └── course_dto.py
│
│── frontend/                        # UI (HTML/JS or React)
│   ├── index.html
│   ├── js/
│   └── css/
│
│── utils/
│   ├── logger.py
│   └── exceptions.py
│
│── database/
│   ├── local_db.sqlite              # Local DB
│   └── migrations/                  # (Optional)
│
│── cargo-rust-server/               # OPTIONAL Rust API Server (Axum)
│   ├── src/
│   ├── Cargo.toml
│   └── build.sh
│
│── tests/
│   ├── test_models.py
│   ├── test_repository.py
│   ├── test_services.py
│   └── test_api.py
│
└── main.py                            # Entry Point
