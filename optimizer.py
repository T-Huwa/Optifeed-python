from scipy.optimize import linprog
from sqlmodel import Session, select
from models import Ingredient, NutritionalRequirement, NutrientComposition


def optimize_feed(session: Session, chicken_type: str, age: int, feed_amount: float, ingredient_ids: list):
    """
    Optimize the feed formulation to minimize cost while meeting nutritional requirements.
    
    :param session: SQLModel session
    :param chicken_type: "Layers" or "Broilers"
    :param age: Age of birds in weeks
    :param feed_amount: Total amount of feed to mix (kg)
    :param ingredient_ids: List of ingredient IDs to use in the mix
    :return: Optimized ingredient mix, total cost, and nutritional profile
    """

    # 1️⃣ Extract Nutritional Requirements
    nutrient_req = session.exec(
        select(NutritionalRequirement)
        .where(NutritionalRequirement.category == chicken_type)
        .where(NutritionalRequirement.age == age)
    ).first()

    if not nutrient_req:
        return {"error": "No nutritional requirements found for this selection."}

    # Nutrient constraints (min & max)
    nutrient_constraints = {
        "ME": (nutrient_req.ME, nutrient_req.ME * 1.1),
        "CP": (nutrient_req.CP, nutrient_req.CP * 1.1),
        "Ca": (nutrient_req.Ca, nutrient_req.Ca * 1.1),
        "P": (nutrient_req.P, nutrient_req.P * 1.1),
        "Mg": (nutrient_req.Mg, nutrient_req.Mg * 1.1),
        "Na": (nutrient_req.Na, nutrient_req.Na * 1.1),
        "K": (nutrient_req.K, nutrient_req.K * 1.1),
    }

    # 2️⃣ Get Selected Ingredients & Nutrient Profiles
    selected_ingredients = (
        session.exec(select(Ingredient).where(Ingredient.id.in_(ingredient_ids))).all()
    )

    if not selected_ingredients:
        return {"error": "No valid ingredients found."}

    nutrient_compositions = (
        session.exec(select(NutrientComposition).where(NutrientComposition.ingredient_id.in_(ingredient_ids))).all()
    )

    # 3️⃣ Formulate Optimization Problem
    num_ingredients = len(selected_ingredients)
    
    # Cost vector (minimize total cost)
    costs = [ingredient.price for ingredient in selected_ingredients]
    
    # Constraint matrix & bounds
    A_eq = []
    b_eq = []
    
    # Nutrient constraints
    for nutrient, (min_val, max_val) in nutrient_constraints.items():
        nutrient_values = [
            getattr(nc, nutrient, 0) for nc in nutrient_compositions
        ]
        A_eq.append(nutrient_values)
        b_eq.append(min_val)  # We enforce only the minimum constraint

    # Ingredient constraints (0-100% for most, but specific limits for some)
    bounds = [(0, 1)] * num_ingredients  # Default: 0-100%
    special_ingredient_limits = {
        "Maize Bran": (0, 0.05),  # Max 5%
        "Fishmeal": (0, 0.05),    # Max 5%
    }

    for i, ingredient in enumerate(selected_ingredients):
        if ingredient.name in special_ingredient_limits:
            bounds[i] = special_ingredient_limits[ingredient.name]

    # 4️⃣ Solve Optimization Problem
    result = linprog(
        c=costs,              # Minimize cost
        A_eq=A_eq,            # Nutrient constraints
        b_eq=b_eq,
        bounds=bounds,        # Ingredient constraints
        method="highs",
    )

    if not result.success:
        return {"error": "Optimization failed. Adjust constraints or try again.", "constraints" : nutrient_req}

    # 5️⃣ Compute Optimized Ingredient Quantities
    optimized_percentages = result.x
    total_cost = sum(cost * perc * feed_amount for cost, perc in zip(costs, optimized_percentages))

    ingredient_mix = {
        selected_ingredients[i].name: round(optimized_percentages[i] * feed_amount, 2)
        for i in range(num_ingredients)
    }

    return {
        "optimized_mix": ingredient_mix,
        "total_cost": round(total_cost, 2),
        "cost_per_kg": round(total_cost / feed_amount, 2),
    }
