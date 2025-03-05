from fastapi import FastAPI, Depends, APIRouter, HTTPException
from sqlmodel import Session, select
from db import create_db_and_tables, get_session
from models import (
    Category, Ingredient, NutritionalRequirement,
    NutrientComposition, AdditiveRequirement
)

from auth.auth_endpoints import router as auth_router

app = FastAPI()

app.include_router(auth_router, prefix="/auth", tags=["auth"])

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
# router = APIRouter()

# @router.post("/optimize/")
# def optimize_feed_formulation(
#     chicken_type: str,
#     age: int,
#     feed_amount: float,
#     ingredient_ids: list[int],
#     session: Session = Depends(get_session)
# ):
#     """
#     Optimize feed formulation based on user-selected parameters.
#     """
#     return optimize_feed(session, chicken_type, age, feed_amount, ingredient_ids)

# app.include_router(router)


# from optimizer_pulp import solve_feed_recipe as optimize_feed_with_pulp


# @app.post("/optimize-pulp/")
# def optimize_feed_pulp(
#     chicken_type: str,
#     age: int,
#     session: Session = Depends(get_session)
# ):
#     """
#     Optimize feed formulation using PuLP without user-selected ingredients.
#     """
#     return optimize_feed_with_pulp(session, chicken_type, age)

from typing import Dict
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import pulp
from sqlmodel import Session, select
from models import NutritionalRequirement  # Ensure this import is correct
from db import engine  # Ensure you have a database engine setup

# Response model
class OptimizationResult(BaseModel):
    status: str
    composition: Dict[str, float]
    total_cost: float
    nutrient_values: Dict[str, float]

# Endpoint to optimize feed
@app.get("/optimizer/", response_model=OptimizationResult)
def optimize_feed(category: str = Query(..., description="Category of chicken (Layers or Broilers)"),
                  age: int = Query(..., description="Age of the chicken in weeks")):
    # Fetch nutritional requirements from the database
    with Session(engine) as session:
        statement = select(NutritionalRequirement).where(
            (NutritionalRequirement.category == category) & (NutritionalRequirement.age == age)
        )
        requirement = session.exec(statement).first()

        if not requirement:
            raise HTTPException(status_code=404, detail="No nutritional requirements found for the given parameters.")

        # Create requirements dictionary
        requirements = {k: v for k, v in requirement.dict().items() if v is not None and k not in ['id', 'feed_type', 'category', 'age', 'created_at', 'updated_at']}

    # Create the model
    model = pulp.LpProblem("Feed_Optimization", pulp.LpMinimize)

    # Define ingredients and their costs
    ingredients = {
        'Maize_bran': 300,
        'White_maize': 1200,
        'Wheat_bran': 300,
        'Rice_Bran': 300,
        'Millet': 300,
        'Sorghum': 300,
        'Soya_full_fat': 1500,
        'Soy_cake': 300,
        'Sunflower': 300,
        'Sunflower_Cake': 450,
        'Fish_meal': 300,
        'BSF': 300,
        'Premix': 1500,
        'Toxicin': 2000,
        'Lysine': 4500,
        'Methionine': 3000,
        'Threonine': 2500,
        'Salt': 800,
        'Tyrosine': 4500,
        'MCP': 4500,
        'Lime': 200
    }

    # Create variables for each ingredient
    x = pulp.LpVariable.dicts("ingr", ingredients.keys(), lowBound=0, upBound=1)

    # Objective function: Minimize cost
    model += pulp.lpSum([x[i] * cost for i, cost in ingredients.items()])

    # Nutrient composition data (per kg)
    nutrient_composition = {
        'ME': {
            'Maize_bran': 8.8, 'White_maize': 14.8, 'Wheat_bran': 7.4, 
            'Rice_Bran': 10.6, 'Millet': 13.3, 'Sorghum': 16.0,
            'Soya_full_fat': 15.7, 'Soy_cake': 12.8, 'Sunflower': 19.7,
            'Sunflower_Cake': 10.8, 'Fish_meal': 12.0, 'BSF': 12.0
        },
        'CP': {
            'Maize_bran': 11.9, 'White_maize': 8.0, 'Wheat_bran': 17.3,
            'Rice_Bran': 12.7, 'Millet': 12.5, 'Sorghum': 10.8,
            'Soya_full_fat': 39.5, 'Soy_cake': 47.0, 'Sunflower': 16.0,
            'Sunflower_Cake': 27.9, 'Fish_meal': 48.4, 'BSF': 42.1
        },
        'Ca': {
            'Maize_bran': 0.47, 'White_maize': 0.04, 'Wheat_bran': 0.14,
            'Rice_Bran': 0.07, 'Millet': 0.05, 'Sorghum': 0.03,
            'Soya_full_fat': 0.34, 'Soy_cake': 0.37, 'Sunflower': 0.27,
            'Sunflower_Cake': 0.39, 'Fish_meal': 7.93, 'BSF': 7.56
        },
        'P': {
            'Maize_bran': 0.34, 'White_maize': 0.29, 'Wheat_bran': 1.11,
            'Rice_Bran': 1.38, 'Millet': 0.33, 'Sorghum': 0.33,
            'Soya_full_fat': 0.59, 'Soy_cake': 0.69, 'Sunflower': 0.57,
            'Sunflower_Cake': 0.92, 'Fish_meal': 3.98, 'BSF': 0.90
        },
        'Na': {
            'Maize_bran': 0.08, 'White_maize': 0.05, 'Wheat_bran': 0.01,
            'Rice_Bran': 0.02, 'Millet': 0.009, 'Sorghum': 0.02,
            'Soya_full_fat': 0.0, 'Soy_cake': 0.011, 'Sunflower': 0.007,
            'Sunflower_Cake': 0.01, 'Fish_meal': 2.84, 'BSF': 0.13
        }
    }

    # Add nutrient constraints
    for nutrient, min_value in requirements.items():
        if nutrient in nutrient_composition:  # Ensure nutrient is supported
            nutrient_sum = pulp.lpSum([x[i] * nutrient_composition[nutrient].get(i, 0) for i in ingredients.keys()])
            model += nutrient_sum >= min_value
        else:
            print(f"Skipping unsupported nutrient: {nutrient}")

    # Constraint: sum of ingredients = 100%
    model += pulp.lpSum([x[i] for i in ingredients.keys()]) == 1

    # Maximum inclusion rates
    model += x['Maize_bran'] <= 0.05  # Max 5%
    model += x['Fish_meal'] <= 0.05   # Max 5%

    # Fixed inclusion rates for additives
    additives = {
        'Premix': 0.0025,
        'Toxicin': 0.001,
        'Lysine': 0.001,
        'Methionine': 0.001,
        'Threonine': 0.001,
        'Salt': 0.0025,
        'Tyrosine': 0.001,
        'MCP': 0.005,
        'Lime': 0.025
    }

    for additive, rate in additives.items():
        model += x[additive] == rate

    # Solve the model
    status = model.solve()

    # Check if solution is optimal
    if pulp.LpStatus[status] != 'Optimal':
        raise HTTPException(status_code=400, detail="Could not find optimal solution")

    # Prepare results
    composition = {}
    total_cost = 0
    
    # Collect results directly from the solved variables
    for ingredient in ingredients.keys():
        value = x[ingredient].value()
        if value is not None and value > 0.0001:
            composition[ingredient.replace('_', ' ')] = round(value * 100, 2)
            total_cost += value * ingredients[ingredient]

    # Calculate actual nutrient values
    nutrient_values = {}
    for nutrient in requirements.keys():
        if nutrient in nutrient_composition:  # Ensure nutrient is supported
            value = sum(x[i].value() * nutrient_composition[nutrient].get(i, 0)
                       for i in ingredients.keys()
                       if x[i].value() is not None)
            nutrient_values[nutrient] = round(value, 2)

    # Verify solution
    total_percentage = sum(composition.values())
    if not (99.9 <= total_percentage <= 100.1):  # Allow for small numerical errors
        raise HTTPException(status_code=400, detail=f"Invalid solution: total percentage is {total_percentage}%")

    return OptimizationResult(
        status=pulp.LpStatus[status],
        composition=composition,
        total_cost=round(total_cost, 2),
        nutrient_values=nutrient_values
    )