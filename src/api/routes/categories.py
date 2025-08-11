"""Category management endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.product import (
    Category,
    CategoryCreate,
    CategoryUpdate,
    CategoryWithChildren,
)
from src.core.database import get_db
from src.core.logging import get_logger
from src.repositories.category import CategoryRepository

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/",
    response_model=Category,
    status_code=status.HTTP_201_CREATED,
    summary="Create Category",
    description="""
Create a new product category.

Categories can be organized hierarchically by specifying a parent_id.
The path will be automatically generated based on the hierarchy.
    """,
    responses={
        201: {"description": "Category created successfully"},
        400: {"description": "Invalid input data"},
        404: {"description": "Parent category not found"},
        500: {"description": "Internal server error"},
    },
)
async def create_category(
    category_data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
) -> Category:
    """Create a new category."""
    repo = CategoryRepository(db)
    
    try:
        category = await repo.create(**category_data.model_dump())
        logger.info("Category created", category_id=str(category.id), name=category.name)
        return Category.model_validate(category)
    except ValueError as e:
        logger.warning("Category creation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to create category", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create category"
        )


@router.get(
    "/",
    response_model=list[Category],
    summary="List Categories",
    description="""
List categories with optional filtering.

Use parent_id to get children of a specific category.
Use name to search for categories by name (partial match).
    """,
    responses={
        200: {"description": "Categories retrieved successfully"},
        500: {"description": "Internal server error"},
    },
)
async def list_categories(
    parent_id: UUID | None = Query(None, description="Filter by parent category ID"),
    name: str | None = Query(None, description="Filter by category name (partial match)"),
    db: AsyncSession = Depends(get_db),
) -> list[Category]:
    """List categories with optional filters."""
    repo = CategoryRepository(db)
    
    try:
        filters = {}
        if parent_id:
            filters["parent_id"] = parent_id
        if name:
            filters["name"] = name
            
        categories = await repo.list(**filters)
        return [Category.model_validate(cat) for cat in categories]
    except Exception as e:
        logger.error("Failed to list categories", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list categories"
        )


@router.get(
    "/root",
    response_model=list[Category],
    summary="List Root Categories",
    description="""
Get all root categories (categories without a parent).
    """,
    responses={
        200: {"description": "Root categories retrieved successfully"},
        500: {"description": "Internal server error"},
    },
)
async def list_root_categories(
    db: AsyncSession = Depends(get_db),
) -> list[Category]:
    """List root categories."""
    repo = CategoryRepository(db)
    
    try:
        categories = await repo.list_root_categories()
        return [Category.model_validate(cat) for cat in categories]
    except Exception as e:
        logger.error("Failed to list root categories", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list root categories"
        )


@router.get(
    "/{category_id}",
    response_model=Category,
    summary="Get Category",
    description="""
Get a specific category by ID.
    """,
    responses={
        200: {"description": "Category retrieved successfully"},
        404: {"description": "Category not found"},
        500: {"description": "Internal server error"},
    },
)
async def get_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Category:
    """Get category by ID."""
    repo = CategoryRepository(db)
    
    try:
        category = await repo.get(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        return Category.model_validate(category)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get category", category_id=str(category_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get category"
        )


@router.get(
    "/{category_id}/with-children",
    response_model=CategoryWithChildren,
    summary="Get Category with Children",
    description="""
Get a category with all its child categories loaded.
    """,
    responses={
        200: {"description": "Category with children retrieved successfully"},
        404: {"description": "Category not found"},
        500: {"description": "Internal server error"},
    },
)
async def get_category_with_children(
    category_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> CategoryWithChildren:
    """Get category with children."""
    repo = CategoryRepository(db)
    
    try:
        category = await repo.get_with_children(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        return CategoryWithChildren.model_validate(category)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get category with children", category_id=str(category_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get category with children"
        )


@router.put(
    "/{category_id}",
    response_model=Category,
    summary="Update Category",
    description="""
Update a category's information.

Note: Changing the name or parent will update the path and affect all child categories.
    """,
    responses={
        200: {"description": "Category updated successfully"},
        404: {"description": "Category not found"},
        400: {"description": "Invalid input data"},
        500: {"description": "Internal server error"},
    },
)
async def update_category(
    category_id: UUID,
    category_data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
) -> Category:
    """Update category."""
    repo = CategoryRepository(db)
    
    try:
        # Only include non-None values in update
        update_data = {k: v for k, v in category_data.model_dump().items() if v is not None}
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No update data provided"
            )
        
        category = await repo.update(category_id, **update_data)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        logger.info("Category updated", category_id=str(category_id))
        return Category.model_validate(category)
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("Category update failed", category_id=str(category_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to update category", category_id=str(category_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update category"
        )


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Category",
    description="""
Delete a category.

Note: This will also delete all child categories and may affect products in these categories.
Use with caution in production systems.
    """,
    responses={
        204: {"description": "Category deleted successfully"},
        404: {"description": "Category not found"},
        500: {"description": "Internal server error"},
    },
)
async def delete_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete category."""
    repo = CategoryRepository(db)
    
    try:
        success = await repo.delete(category_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        logger.info("Category deleted", category_id=str(category_id))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete category", category_id=str(category_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete category"
        )