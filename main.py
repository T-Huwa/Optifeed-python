from fastapi import FastAPI, Depends, APIRouter
from sqlmodel import Session, select
from db import create_db_and_tables, get_session
from models import (
    Category, Ingredient, NutritionalRequirement,
    NutrientComposition, AdditiveRequirement
)
from optimizer import optimize_feed

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
def read_root():
    return {"welcome": "Welcome to OptiFeed!"}


# 🔹 GET a single category by ID
@app.get("/categories/{category_id}", response_model=Category)
def get_category(category_id: int, session: Session = Depends(get_session)):
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


# 🔹 GET a single ingredient by ID
@app.get("/ingredients/{ingredient_id}", response_model=Ingredient)
def get_ingredient(ingredient_id: int, session: Session = Depends(get_session)):
    ingredient = session.get(Ingredient, ingredient_id)
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return ingredient


# 🔹 GET a nutritional requirement by Age and Category
@app.get("/nutritional-requirements/{category}/{age}", response_model=NutritionalRequirement)
def get_nutritional_requirement(category: str, age: int, session: Session = Depends(get_session)):
    requirement = session.exec(
        select(NutritionalRequirement)
        .where(NutritionalRequirement.category == category)
        .where(NutritionalRequirement.age == age)
    ).first()

    if not requirement:
        raise HTTPException(status_code=404, detail="Nutritional requirement not found for the given category and age")

    return requirement


# 🔹 GET nutrient composition for a specific ingredient
@app.get("/nutrient-compositions/{ingredient_id}", response_model=NutrientComposition)
def get_nutrient_composition(ingredient_id: int, session: Session = Depends(get_session)):
    composition = session.exec(
        select(NutrientComposition)
        .where(NutrientComposition.ingredient_id == ingredient_id)
    ).first()

    if not composition:
        raise HTTPException(status_code=404, detail="Nutrient composition not found for the given ingredient")

    return composition


# 🔹 GET all categories
@app.get("/categories/", response_model=list[Category])
def get_categories(session: Session = Depends(get_session)):
    with session:
        return session.exec(select(Category)).all()

# 🔹 CREATE a new category
@app.post("/categories/", response_model=Category)
def create_category(category: Category, session: Session = Depends(get_session)):
    with session:
        session.add(category)
        session.commit()
        session.refresh(category)
        return category


# 🔹 GET all ingredients
@app.get("/ingredients/", response_model=list[Ingredient])
def get_ingredients(session: Session = Depends(get_session)):
    with session:
        return session.exec(select(Ingredient)).all()

# 🔹 CREATE a new ingredient
@app.post("/ingredients/", response_model=Ingredient)
def create_ingredient(ingredient: Ingredient, session: Session = Depends(get_session)):
    with session:
        session.add(ingredient)
        session.commit()
        session.refresh(ingredient)
        return ingredient


#Edit Ingridients
@app.put("/ingredients/{ingredient_id}", response_model=Ingredient)
def update_ingredient(ingredient_id: int, updated_data: Ingredient, session: Session = Depends(get_session)):
    with session:
        ingredient = session.get(Ingredient, ingredient_id)
        if not ingredient:
            return {"error": "Ingredient not found"}

        # Update fields
        ingredient.name = updated_data.name
        ingredient.categoryId = updated_data.categoryId
        ingredient.price = updated_data.price  # Allow updating price

        session.commit()
        session.refresh(ingredient)
        return ingredient


# 🔹 GET all nutritional requirements
@app.get("/nutritional-requirements/", response_model=list[NutritionalRequirement])
def get_nutritional_requirements(session: Session = Depends(get_session)):
    with session:
        return session.exec(select(NutritionalRequirement)).all()

# 🔹 CREATE a new nutritional requirement
@app.post("/nutritional-requirements/", response_model=NutritionalRequirement)
def create_nutritional_requirement(
    nutritional_requirement: NutritionalRequirement, session: Session = Depends(get_session)
):
    with session:
        session.add(nutritional_requirement)
        session.commit()
        session.refresh(nutritional_requirement)
        return nutritional_requirement

# 🔹 GET all nutrient compositions
@app.get("/nutrient-compositions/", response_model=list[NutrientComposition])
def get_nutrient_compositions(session: Session = Depends(get_session)):
    with session:
        return session.exec(select(NutrientComposition)).all()

# 🔹 CREATE a new nutrient composition
@app.post("/nutrient-compositions/", response_model=NutrientComposition)
def create_nutrient_composition(
    nutrient_composition: NutrientComposition, session: Session = Depends(get_session)
):
    with session:
        session.add(nutrient_composition)
        session.commit()
        session.refresh(nutrient_composition)
        return nutrient_composition

# 🔹 GET all additive requirements
@app.get("/additive-requirements/", response_model=list[AdditiveRequirement])
def get_additive_requirements(session: Session = Depends(get_session)):
    with session:
        return session.exec(select(AdditiveRequirement)).all()

# 🔹 CREATE a new additive requirement
@app.post("/additive-requirements/", response_model=AdditiveRequirement)
def create_additive_requirement(
    additive_requirement: AdditiveRequirement, session: Session = Depends(get_session)
):
    with session:
        session.add(additive_requirement)
        session.commit()
        session.refresh(additive_requirement)
        return additive_requirement
        


# 🔹 Endpoint for optimization
router = APIRouter()

@router.post("/optimize/")
def optimize_feed_formulation(
    chicken_type: str,
    age: int,
    feed_amount: float,
    ingredient_ids: list[int],
    session: Session = Depends(get_session)
):
    """
    Optimize feed formulation based on user-selected parameters.
    """
    return optimize_feed(session, chicken_type, age, feed_amount, ingredient_ids)

app.include_router(router)
