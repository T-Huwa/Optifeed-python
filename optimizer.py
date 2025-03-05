from typing import Dict, List
from fastapi import HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from models import NutritionalRequirement, NutrientComposition, Ingredient
import pulp

class OptimizationResult(BaseModel):
    status: str
    composition: Dict[str, float]
    total_cost: float
    nutrient_values: Dict[str, float]

def optimize_feed(session: Session, category: str, age: int, ingredient_ids: List[int]) -> OptimizationResult:
    # Fetch nutritional requirements from the database
    statement = select(NutritionalRequirement).where(
        (NutritionalRequirement.category == category) & (NutritionalRequirement.age == age)
    )
    requirement = session.exec(statement).first()

    if not requirement:
        raise HTTPException(status_code=404, detail="No nutritional requirements found for the given parameters.")

    # Create requirements dictionary
    requirements = {k: v for k, v in requirement.dict().items() if v is not None and k not in ['id', 'feed_type', 'category', 'age', 'created_at', 'updated_at']}

    # Fetch ingredient details from the database
    ingredients = {}
    nutrient_composition = {}
    for ingredient_id in ingredient_ids:
        ingredient = session.get(Ingredient, ingredient_id)
        if not ingredient:
            raise HTTPException(status_code=404, detail=f"Ingredient with ID {ingredient_id} not found")
        ingredients[ingredient.name] = ingredient.price

        # Fetch nutrient composition for the ingredient
        composition = session.exec(
            select(NutrientComposition).where(NutrientComposition.ingredient_id == ingredient_id)
        ).first()
        if not composition:
            raise HTTPException(status_code=404, detail=f"Nutrient composition for ingredient ID {ingredient_id} not found")

        for nutrient, value in composition.dict().items():
            if nutrient not in ['id', 'ingredient_id', 'created_at', 'updated_at']:
                if nutrient not in nutrient_composition:
                    nutrient_composition[nutrient] = {}
                nutrient_composition[nutrient][ingredient.name] = value

    # Create the model
    model = pulp.LpProblem("Feed_Optimization", pulp.LpMinimize)

    # Create variables for each ingredient
    x = pulp.LpVariable.dicts("ingr", ingredients.keys(), lowBound=0, upBound=1)

    # Objective function: Minimize cost
    model += pulp.lpSum([x[i] * cost for i, cost in ingredients.items()])

    # Add nutrient constraints
    for nutrient, min_value in requirements.items():
        if nutrient in nutrient_composition:  # Ensure nutrient is supported
            nutrient_sum = pulp.lpSum([x[i] * nutrient_composition[nutrient].get(i, 0) for i in ingredients.keys()])
            model += nutrient_sum >= min_value
        else:
            print(f"Skipping unsupported nutrient: {nutrient}")

    # Constraint: sum of ingredients = 100%
    model += pulp.lpSum([x[i] for i in ingredients.keys()]) == 1

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