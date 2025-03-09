from typing import Dict, List, Optional
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
    cost_per_kg: float

def optimize_feed(
    session: Session, 
    feed_type: str,  # 'layers' or 'broilers'
    age: int, 
    ingredient_ids: List[int],
    amount: Optional[float] = None  # total amount of feed to mix in kg (optional)
) -> OptimizationResult:
    """
    Optimizes feed composition using a Stigler Diet-like approach.
    
    This function finds the minimum-cost combination of ingredients that satisfies
    all nutritional requirements for a specific type of animal at a specific age.
    """
    
    # Fetch nutritional requirements based on feed type and age
    statement = select(NutritionalRequirement).where(
        (NutritionalRequirement.category == feed_type) & (NutritionalRequirement.age == age)
    )
    requirement = session.exec(statement).first()

    if not requirement:
        raise HTTPException(status_code=404, detail=f"No nutritional requirements found for {feed_type} at {age} weeks.")

    # Extract nutrient requirements (exclude additives and non-nutrient fields)
    nutrient_requirements = {}
    for nutrient in ['ME', 'CP', 'Ca', 'P', 'Mg', 'Na', 'K']:
        if hasattr(requirement, nutrient) and getattr(requirement, nutrient) is not None:
            nutrient_requirements[nutrient] = getattr(requirement, nutrient)
    
    # Create maximum requirements (1.1 times minimum values)
    max_nutrient_requirements = {k: v * 1.1 for k, v in nutrient_requirements.items()}

    # Define fixed values for additives (as per LP guide.docx)
    additive_requirements = {
        "Premix": 0.25,  # 0.25%
        "Toxicin": 0.10,  # 0.10%
        "Lysine": 0.10,   # 0.10%
        "Methionine": 0.10,  # 0.10%
        "Threonine": 0.10,  # 0.10%
        "Salt": 0.25,    # 0.25%
        "Tyrosine": 0.10,  # 0.10%
        "MCP": 0.50,     # 0.50%
        "Lime": 2.50     # 2.50%
    }

    # Step 1: Gather all ingredients data
    ingredients_data = []
    
    for ingredient_id in ingredient_ids:
        # Get basic ingredient info
        ingredient = session.get(Ingredient, ingredient_id)
        if not ingredient:
            raise HTTPException(status_code=404, detail=f"Ingredient with ID {ingredient_id} not found")
        
        # Get nutrient composition
        composition = session.exec(
            select(NutrientComposition).where(NutrientComposition.ingredient_id == ingredient_id)
        ).first()
        
        if not composition:
            raise HTTPException(status_code=404, detail=f"Nutrient composition for ingredient ID {ingredient_id} not found")
        
        # Create ingredient data structure
        ingredient_data = {
            'id': ingredient_id,
            'name': ingredient.name,
            'category': ingredient.category,
            'price': ingredient.price,
            'nutrients': {}
        }
        
        # Add nutrient values
        for nutrient in nutrient_requirements.keys():
            if hasattr(composition, nutrient):
                ingredient_data['nutrients'][nutrient] = getattr(composition, nutrient)
            else:
                ingredient_data['nutrients'][nutrient] = 0
                
        ingredients_data.append(ingredient_data)

    # Step 2: Create the optimization model
    model = pulp.LpProblem("Feed_Optimization", pulp.LpMinimize)
    
    # Step 3: Define variables - percentage of each ingredient in the mix
    ingredient_vars = {}
    
    for ingredient in ingredients_data:
        # Set appropriate bounds based on ingredient type
        if ingredient['name'] == "Maize bran":
            ingredient_vars[ingredient['name']] = pulp.LpVariable(
                f"ingr_{ingredient['name'].replace(' ', '_')}", 
                lowBound=0, 
                #upBound=0.05  # Max 5%
            )
        elif ingredient['name'] == "Fish meal":
            ingredient_vars[ingredient['name']] = pulp.LpVariable(
                f"ingr_{ingredient['name'].replace(' ', '_')}", 
                lowBound=0, 
                #upBound=0.05  # Max 5%
            )
        elif ingredient['name'] in additive_requirements:
            # Fixed percentage for additives
            fixed_value = additive_requirements[ingredient['name']] / 100  # Convert to decimal
            ingredient_vars[ingredient['name']] = pulp.LpVariable(
                f"ingr_{ingredient['name'].replace(' ', '_')}", 
                lowBound=fixed_value, 
                #upBound=fixed_value
            )
        else:
            # Regular ingredients can be 0-100%
            ingredient_vars[ingredient['name']] = pulp.LpVariable(
                f"ingr_{ingredient['name'].replace(' ', '_')}", 
                lowBound=0, 
                upBound=1
            )
    
    # Step 4: Define the objective function - minimize cost
    model += pulp.lpSum([
        ingredient_vars[ingredient['name']] * ingredient['price'] 
        for ingredient in ingredients_data
    ]), "Total_Cost"
    
    # Step 5: Define constraints
    
    # Constraint: Sum of all ingredients must equal 100%
    model += pulp.lpSum([ingredient_vars[ingredient['name']] for ingredient in ingredients_data]) == 1, "Total_Percentage"
    
    # Nutrient minimum constraints
    for nutrient, min_value in nutrient_requirements.items():
        model += pulp.lpSum([
            ingredient_vars[ingredient['name']] * ingredient['nutrients'].get(nutrient, 0)
            for ingredient in ingredients_data
        ]) >= min_value, f"Min_{nutrient}"
    
    # Nutrient maximum constraints
    # for nutrient, max_value in max_nutrient_requirements.items():
    #     model += pulp.lpSum([
    #         ingredient_vars[ingredient['name']] * ingredient['nutrients'].get(nutrient, 0)
    #         for ingredient in ingredients_data
    #     ]) <= max_value, f"Max_{nutrient}"
    
    # Step 6: Solve the model
    solver = pulp.PULP_CBC_CMD(msg=False)
    print("Solving model...")
    print(model)
    status = model.solve(solver)
    
    # Step 7: Check results and prepare output
    if pulp.LpStatus[status] != 'Optimal':
        raise HTTPException(
            status_code=400, 
            detail=f"Could not find optimal solution. Status: {pulp.LpStatus[status]}"
        )
    
    # Step 8: Gather the results
    composition = {}
    total_cost = 0
    
    for ingredient in ingredients_data:
        value = ingredient_vars[ingredient['name']].value()
        if value is not None and value > 0.0001:  # Filter out very small values
            composition[ingredient['name']] = round(value * 100, 2)  # Convert to percentage
            total_cost += value * ingredient['price']
    
    # Calculate nutrient values in the final mix
    nutrient_values = {}
    for nutrient in nutrient_requirements.keys():
        value = sum(
            ingredient_vars[ingredient['name']].value() * ingredient['nutrients'].get(nutrient, 0)
            for ingredient in ingredients_data
            if ingredient_vars[ingredient['name']].value() is not None
        )
        nutrient_values[nutrient] = round(value, 2)
    
    # Add additive values to nutrient values
    for ingredient in ingredients_data:
        if ingredient['name'] in additive_requirements:
            nutrient_values[ingredient['name']] = additive_requirements[ingredient['name']]
    
    # Validate the solution
    total_percentage = sum(composition.values())
    if not (99.9 <= total_percentage <= 100.1):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid solution: total percentage is {total_percentage}%"
        )
    
    # Calculate final cost based on amount if provided
    cost_per_kg = round(total_cost, 2)
    final_cost = cost_per_kg
    if amount:
        final_cost = round(cost_per_kg * amount, 2)
    
    return OptimizationResult(
        status=pulp.LpStatus[status],
        composition=composition,
        total_cost=final_cost,
        nutrient_values=nutrient_values,
        cost_per_kg=cost_per_kg
    )