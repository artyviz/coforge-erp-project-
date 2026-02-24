pub mod students;
pub mod courses;
pub mod departments;
pub mod faculty;
pub mod enrollments;
pub mod analytics;
pub mod health;

use axum::Router;
use crate::db::Db;

/// Mount all API routes under /api.
pub fn routes() -> Router<Db> {
    Router::new()
        .nest("/students", students::routes())
        .nest("/courses", courses::routes())
        .nest("/departments", departments::routes())
        .nest("/faculty", faculty::routes())
        .nest("/enrollments", enrollments::routes())
        .nest("/analytics", analytics::routes())
        .merge(health::routes())
}
