# Product Catalog Service

The Product Catalog Service is a core component of the First Viscount e-commerce platform, providing comprehensive product and category management capabilities.

## Features

### Phase 1 MVP Features ✅

- **Product Management**: Full CRUD operations for products with attributes and pricing
- **Category Management**: Hierarchical category organization with automatic path generation
- **Basic Search**: Text-based product search with relevance ranking
- **Price Management**: Decimal-precision pricing with range filtering
- **Pagination**: Efficient pagination for large product catalogs
- **Monitoring**: Prometheus metrics and Grafana dashboards
- **Health Checks**: Comprehensive health and readiness endpoints

## Architecture

- **Framework**: FastAPI with async/await support
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Search**: Basic text search with future full-text search support
- **Metrics**: Prometheus monitoring with Grafana visualization
- **Containerization**: Docker with multi-stage builds
- **Testing**: Pytest with async support and comprehensive coverage

## Quick Start

### Development Setup

1. **Clone and navigate to the service:**
   ```bash
   cd /home/dwdra/workspace/first-viscount/product-catalog-service
   ```

2. **Start development environment:**
   ```bash
   make dev-setup
   ```

3. **Access the service:**
   - API: http://localhost:8082
   - API Documentation: http://localhost:8082/docs
   - Grafana: http://localhost:3001 (admin/admin)
   - Prometheus: http://localhost:9091

### API Usage

#### Categories

```bash
# Create a category
curl -X POST "http://localhost:8082/api/v1/categories/" \
  -H "Content-Type: application/json" \
  -d '{"name": "Electronics", "description": "Electronic devices"}'

# List categories
curl "http://localhost:8082/api/v1/categories/"

# Get category with children
curl "http://localhost:8082/api/v1/categories/{category_id}/with-children"
```

#### Products

```bash
# Create a product
curl -X POST "http://localhost:8082/api/v1/products/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "iPhone 15",
    "description": "Latest iPhone model",
    "category_id": "{category_id}",
    "price": 999.99,
    "attributes": {"color": "blue", "storage": "128GB"}
  }'

# List products with pagination
curl "http://localhost:8082/api/v1/products/?offset=0&limit=20"

# Search products
curl "http://localhost:8082/api/v1/products/search?q=iPhone"

# Filter by category and price
curl "http://localhost:8082/api/v1/products/?category_id={id}&min_price=100&max_price=1000"
```

## Development

### Available Commands

```bash
make help              # Show all available commands
make dev-setup         # Set up development environment
make dev-test          # Run formatting, linting, and tests
make test-cov          # Run tests with coverage report
make format            # Format code with black and ruff
make lint              # Run linting checks
make run               # Run service locally with reload
```

### Project Structure

```
src/
├── api/
│   ├── middleware/     # Request/response middleware
│   ├── models/         # Pydantic schemas
│   └── routes/         # FastAPI route handlers
├── core/
│   ├── config.py       # Configuration management
│   ├── database.py     # Database connection and session management
│   ├── logging.py      # Structured logging setup
│   └── metrics.py      # Prometheus metrics
├── models/
│   └── product.py      # SQLAlchemy database models
├── repositories/
│   ├── base.py         # Base repository pattern
│   ├── category.py     # Category data access
│   └── product.py      # Product data access
└── main.py             # FastAPI application

tests/
├── conftest.py         # Test configuration and fixtures
├── test_health.py      # Health endpoint tests
├── test_categories.py  # Category API tests
└── test_products.py    # Product API tests
```

### Database Schema

#### Categories Table
- Hierarchical structure with `parent_id` and `path`
- Automatic path generation for efficient querying
- Supports unlimited nesting levels

#### Products Table
- Rich product information with JSON attributes
- Decimal precision pricing
- Search vector for text-based search
- Foreign key relationship to categories

## API Documentation

### Endpoints

#### Health & Monitoring
- `GET /health` - Basic health check
- `GET /health/ready` - Readiness probe
- `GET /metrics` - Prometheus metrics

#### Categories
- `POST /api/v1/categories/` - Create category
- `GET /api/v1/categories/` - List categories
- `GET /api/v1/categories/root` - List root categories
- `GET /api/v1/categories/{id}` - Get category
- `GET /api/v1/categories/{id}/with-children` - Get category with children
- `PUT /api/v1/categories/{id}` - Update category
- `DELETE /api/v1/categories/{id}` - Delete category

#### Products
- `POST /api/v1/products/` - Create product
- `GET /api/v1/products/` - List products (with pagination and filters)
- `GET /api/v1/products/search` - Search products
- `GET /api/v1/products/{id}` - Get product
- `PUT /api/v1/products/{id}` - Update product
- `DELETE /api/v1/products/{id}` - Delete product

### Response Format

All API responses follow consistent patterns:

**Success Response:**
```json
{
  "id": "uuid",
  "name": "Product Name",
  "created_at": "2025-01-29T12:00:00Z",
  ...
}
```

**List Response:**
```json
{
  "products": [...],
  "total": 100,
  "offset": 0,
  "limit": 50
}
```

**Error Response:**
```json
{
  "error": {
    "type": "ValidationError",
    "message": "Validation failed",
    "code": "VALIDATION_ERROR",
    "details": [...],
    "timestamp": "2025-01-29T12:00:00Z",
    "path": "/api/v1/products"
  }
}
```

## Monitoring

### Metrics

The service exposes Prometheus metrics including:
- HTTP request counts and duration
- Database connection pool statistics
- Product and category operation counts
- Search query performance
- Error rates by endpoint

### Health Checks

- `/health` - Basic health check for load balancers
- `/health/ready` - Comprehensive readiness check for Kubernetes

## Testing

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test files
pytest tests/test_products.py -v

# Run integration tests only
pytest tests/ -m integration -v
```

## Configuration

Environment variables:

- `DATABASE_URL` - PostgreSQL connection string
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARN, ERROR)
- `LOG_FORMAT` - Log format (json, console)
- `ENVIRONMENT` - Environment (development, staging, production)
- `CORS_ORIGINS` - Allowed CORS origins

## Security

- Non-root container user
- No sensitive data in logs
- SQL injection protection via SQLAlchemy
- Input validation with Pydantic
- CORS configuration

## Future Enhancements

- Full-text search with PostgreSQL or Elasticsearch
- Product image management
- Inventory tracking
- Product reviews and ratings
- Recommendation engine integration
- Advanced filtering and faceted search
- Bulk product operations
- Product import/export

## Contributing

1. Follow the established patterns from platform-coordination-service
2. Write tests for all new features
3. Ensure all linting and formatting checks pass
4. Update documentation for API changes
5. Add monitoring metrics for new operations

## License

See the LICENSE file in the repository root.# product-catalog-service
