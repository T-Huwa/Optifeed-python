from fastapi import APIRouter, HTTPException, Query, Depends
import scipy.optimize as opt
import numpy as np
from sqlmodel import Session, select
from db import get_session
from models import NutritionalRequirement

router = APIRouter()

ingredient_names = [
    "Maize Bran", "White Maize", "Wheat Bran", "Rice Bran", "Millet", 
    "Sorghum", "Soya Full Fat", "Soy Cake", "Sunflower", 
    "Sunflower Cake", "Fish Meal", "BSF"
]

data = np.array([
    [300, 88.7, 8.8, 11.9, 0.47, 0.34, 0.22, 0.08, 0.73],
    [1200, 90, 14.8, 8, 0.04, 0.29, 0.13, 0.05, 0.36],
    [300, 87, 7.4, 17.3, 0.14, 1.11, 0.45, 0.01, 1.37],
    [300, 90.2, 10.6, 12.7, 0.07, 1.38, 0.65, 0.02, 1.23],
    [300, 89.6, 13.3, 12.5, 0.05, 0.33, 0.13, 0.009, 0.41],
    [300, 87.4, 16, 10.8, 0.03, 0.33, 0.18, 0.02, 0.43],
    [1500, 88.6, 15.7, 39.5, 0.34, 0.59, 0.24, 0, 1.92],
    [300, 93.2, 12.8, 47, 0.37, 0.69, 0.29, 0.011, 2.24],
    [300, 92.8, 19.7, 16, 0.27, 0.57, 0.29, 0.007, 0.84],
    [450, 91.8, 10.8, 27.9, 0.39, 0.92, 0.36, 0.01, 1.12],
    [300, 92.5, 12, 48.4, 7.93, 3.98, 0, 2.84, 1.11],
    [300, 91.3, 12, 42.1, 7.56, 0.9, 0.39, 0.13, 0.69]
])

prices = data[:, 0]
nutrient_matrix = data[:, 1:].T

def objective(x):
    return np.dot(prices, x)
@router.get("/optimize-feed")
def optimize_feed(
    category: str = Query(..., description="Category of chicken (Layers or Broilers)"),
    age: int = Query(..., description="Age of the chicken in weeks"),
    ingredient_ids: list[int] = Query(..., description="List of ingredient IDs to use in the optimization process"),
    session: Session = Depends(get_session)
):
    nutrient_query = session.exec(
        select(NutritionalRequirement).where(
            NutritionalRequirement.category == category,
            NutritionalRequirement.age == age,
        )
    ).first()

    if not nutrient_query:
        raise HTTPException(
            status_code=404,
            detail=f"Nutrient requirements not found for category '{category}' and age '{age}' weeks."
        )

    nutrients = np.array([
        nutrient_query.DM or 0,  # DM
        nutrient_query.ME or 0,  # ME
        nutrient_query.CP or 0,  # CP
        nutrient_query.Ca or 0,  # Ca
        nutrient_query.P or 0,   # P
        nutrient_query.Mg or 0,  # Mg
        nutrient_query.Na or 0,  # Na
        nutrient_query.K or 0   # K
    ])

    selected_ingredients = [data[i] for i in ingredient_ids if i < len(data)]
    selected_ingredient_names = [ingredient_names[i] for i in ingredient_ids if i < len(ingredient_names)]
    
    if not selected_ingredients:
        raise HTTPException(
            status_code=400,
            detail="No valid ingredients found for the provided IDs."
        )
    
    selected_data = np.array(selected_ingredients)
    selected_prices = selected_data[:, 0]
    selected_nutrient_matrix = selected_data[:, 1:].T 

    def objective(x):
        return np.dot(selected_prices, x)

    constraints = [
        {"type": "eq", "fun": lambda x: np.sum(x) - 100},
    ]

    for i in range(len(nutrients)):
        constraints.append({
            "type": "ineq",
            "fun": lambda x, i=i: np.dot(selected_nutrient_matrix[i], x) - nutrients[i]
        })

    bounds = [(0, None) for _ in range(len(selected_data))]

    initial_guess = np.random.rand(len(selected_data))
    initial_guess = initial_guess / np.sum(initial_guess) * 100

    result = opt.minimize(objective, initial_guess, bounds=bounds, constraints=constraints, method="SLSQP")

    if result.success:
        feed_result = []
        for i, amount in enumerate(result.x):
            if amount > 0:
                feed_result.append({
                    "ingredient": selected_ingredient_names[i],
                    "amount_kg": round(amount, 2),
                    "cost_mwk": round(amount * selected_prices[i], 2)
                })
        total_cost = round(result.fun, 2)
        final_nutrients = np.dot(selected_nutrient_matrix, result.x)

        return {
            "success": True,
            "feed": feed_result,
            "total_cost_mwk": total_cost,
        }
    else:
        return {"success": False, "message": "Optimization failed."}