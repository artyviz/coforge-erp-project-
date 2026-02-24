use std::net::SocketAddr;

use axum::{routing::{get, post}, Router};
use sqlx::postgres::PgPoolOptions;
use tower_http::cors::{Any, CorsLayer};
use tower_http::trace::TraceLayer;
use tower::limit::RateLimitLayer;
use std::time::Duration;
use tracing_subscriber::EnvFilter;

pub mod auth;
mod config;
mod db;
mod errors;
mod handlers;
mod models;

#[tokio::main]
async fn main() {
    dotenvy::dotenv().ok();

    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::from_default_env())
        .init();

    let cfg = config::Config::from_env();

    let pool = PgPoolOptions::new()
        .max_connections(20)
        .connect(&cfg.database_url)
        .await
        .expect("Failed to connect to Postgres");

    tracing::info!("Connected to database");

    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods(Any)
        .allow_headers(Any);

    // Auth routes (public — no token needed)
    let auth_routes = Router::new()
        .route("/register", post(auth::register))
        .route("/login", post(auth::login))
        .route("/me", get(auth::me));

    let app = Router::new()
        .nest("/api/auth", auth_routes)
        .nest("/api", handlers::routes())
        .layer(cors)
        .layer(TraceLayer::new_for_http())
        .layer(RateLimitLayer::new(100, Duration::from_secs(1)))
        .with_state(pool);

    let addr = SocketAddr::from(([0, 0, 0, 0], cfg.port));
    tracing::info!("Rust API listening on {}", addr);

    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}
