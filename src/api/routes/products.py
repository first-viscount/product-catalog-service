"""Product management endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.product import (
    Product,
    ProductCreate,
    ProductUpdate,
    ProductWithCategory,
    ProductListResponse,
    ProductSearchResponse,
)
from src.core.database import get_db
from src.core.logging import get_logger
from src.repositories.product import ProductRepository

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/",
    response_model=Product,
    status_code=status.HTTP_201_CREATED,
    summary="Create Product",
    description="""
Create a new product in the catalog.

The product will be associated with the specified category and include all provided attributes.
    """,
    responses={
        201: {"description": "Product created successfully"},
        400: {"description": "Invalid input data"},
        500: {"description": "Internal server error"},
    },
)
async def create_product(
    product_data: ProductCreate,
    db: AsyncSession = Depends(get_db),
) -> Product:
    """Create a new product."""
    repo = ProductRepository(db)
    
    try:
        product = await repo.create(**product_data.model_dump())
        logger.info("Product created", product_id=str(product.id), name=product.name)
        return Product.model_validate(product)
    except Exception as e:
        logger.error("Failed to create product", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create product"
        )


@router.get(
    "/",
    response_model=ProductListResponse,
    summary="List Products",
    description="""
List products with pagination and optional filtering.

Supports filtering by:
- category_id: Only products in the specified category
- min_price/max_price: Price range filtering
- name: Partial name matching

Results are paginated using offset and limit parameters.
    """,
    responses={
        200: {"description": "Products retrieved successfully"},
        400: {"description": "Invalid query parameters"},
        500: {"description": "Internal server error"},
    },
)
async def list_products(
    category_id: UUID | None = Query(None, description="Filter by category ID"),
    min_price: float | None = Query(None, ge=0, description="Minimum price filter"),
    max_price: float | None = Query(None, ge=0, description="Maximum price filter"),
    name: str | None = Query(None, description="Filter by name (partial match)"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=100, description="Pagination limit"),
    db: AsyncSession = Depends(get_db),
) -> ProductListResponse:
    """List products with filters and pagination."""
    repo = ProductRepository(db)
    
    try:
        # Validate price range
        if min_price is not None and max_price is not None and min_price > max_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="min_price cannot be greater than max_price"
            )
        
        # Build filters
        filters = {}
        if name:
            filters["name"] = name
        
        # Get products and total count
        products = await repo.list(
            offset=offset,
            limit=limit,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            **filters
        )
        
        total = await repo.count(
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            **filters
        )
        
        return ProductListResponse(
            products=[ProductWithCategory.model_validate(product) for product in products],
            total=total,
            offset=offset,
            limit=limit,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to list products", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list products"
        )


@router.get(
    "/search",
    response_model=ProductSearchResponse,
    summary="Search Products",
    description="""
Search for products using a text query.

The search looks through product names and descriptions.
Results are ranked by relevance with exact matches appearing first.
    """,
    responses={
        200: {"description": "Search completed successfully"},
        400: {"description": "Invalid query parameters"},
        500: {"description": "Internal server error"},
    },
)
async def search_products(
    q: str = Query(..., min_length=1, description="Search query"),
    category_id: UUID | None = Query(None, description="Filter by category ID"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=100, description="Pagination limit"),
    db: AsyncSession = Depends(get_db),
) -> ProductSearchResponse:
    """Search products by text query."""
    repo = ProductRepository(db)
    
    try:
        # Search products
        products = await repo.search(
            query=q,
            offset=offset,
            limit=limit,
            category_id=category_id,
        )
        
        # Get total count for search
        total = await repo.search_count(
            query=q,
            category_id=category_id,
        )
        
        logger.info("Product search executed", query=q, results=len(products), total=total)
        
        return ProductSearchResponse(
            products=[ProductWithCategory.model_validate(product) for product in products],
            total=total,
            offset=offset,
            limit=limit,
            query=q,
        )
    except Exception as e:
        logger.error("Failed to search products", query=q, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search products"
        )


@router.get(
    "/{product_id}",
    response_model=ProductWithCategory,
    summary="Get Product",
    description="""
Get a specific product by ID, including its category information.
    """,
    responses={
        200: {"description": "Product retrieved successfully"},
        404: {"description": "Product not found"},
        500: {"description": "Internal server error"},
    },
)
async def get_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ProductWithCategory:
    """Get product by ID."""
    repo = ProductRepository(db)
    
    try:
        product = await repo.get_with_category(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        return ProductWithCategory.model_validate(product)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get product", product_id=str(product_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get product"
        )


@router.put(
    "/{product_id}",
    response_model=Product,
    summary="Update Product",
    description="""
Update a product's information.

Only provided fields will be updated. Fields not included in the request will remain unchanged.
    """,
    responses={
        200: {"description": "Product updated successfully"},
        404: {"description": "Product not found"},
        400: {"description": "Invalid input data"},
        500: {"description": "Internal server error"},
    },
)
async def update_product(
    product_id: UUID,
    product_data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
) -> Product:
    """Update product."""
    repo = ProductRepository(db)
    
    try:
        # Only include non-None values in update
        update_data = {k: v for k, v in product_data.model_dump().items() if v is not None}
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No update data provided"
            )
        
        product = await repo.update(product_id, **update_data)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        logger.info("Product updated", product_id=str(product_id))
        return Product.model_validate(product)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update product", product_id=str(product_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update product"
        )


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Product",
    description="""
Delete a product from the catalog.

This action cannot be undone. Use with caution in production systems.
    """,
    responses={
        204: {"description": "Product deleted successfully"},
        404: {"description": "Product not found"},
        500: {"description": "Internal server error"},
    },
)
async def delete_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete product."""
    repo = ProductRepository(db)
    
    try:
        success = await repo.delete(product_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        logger.info("Product deleted", product_id=str(product_id))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete product", product_id=str(product_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete product"
        )