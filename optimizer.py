import pulp
from sqlmodel import Session, select
from models import NutritionalRequirement

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

def optimize_feed_logic(chicken_type: str, age: int, session: Session):
    statement = select(NutritionalRequirement).where(
        (NutritionalRequirement.category == chicken_type) & (NutritionalRequirement.age == age)
    )
    requirement = session.exec(statement).first()
    
    if not requirement:
        return {"error": "No nutritional requirements found for the given parameters."}
    
    requirements = {k: v for k, v in requirement.dict().items() if v is not None and k not in ['id', 'feed_type', 'category', 'age']}
    
    model = pulp.LpProblem("Layer_Feed_Optimization", pulp.LpMinimize)
    x = pulp.LpVariable.dicts("ingr", ingredients.keys(), lowBound=0, upBound=1)
    model += pulp.lpSum([x[i] * cost for i, cost in ingredients.items()])
    

    for nutrient, min_value in requirements.items():
        if isinstance(min_value, (int, float)):  # Ensure min_value is numeric
            model += pulp.lpSum([x[i] * nutrient_composition.get(nutrient, {}).get(i, 0) for i in ingredients.keys()]) >= min_value
        else:
            print(f"Skipping invalid min_value for {nutrient}: {min_value} ({type(min_value)})")
        
    model += pulp.lpSum([x[i] for i in ingredients.keys()]) == 1
    model += x['Maize_bran'] <= 0.3
    model += x['Fish_meal'] <= 0.2
    model += x['White_maize'] <= 0.6
    model += x['Soya_full_fat'] <= 0.3
    
    model.solve()
    
    result = {i.replace('_', ' '): round(pulp.value(x[i]) * 100, 2) for i in ingredients.keys() if pulp.value(x[i]) > 0.0001}
    total_cost = sum(ingredients[i] * pulp.value(x[i]) for i in ingredients.keys())
    final_nutrients = {nutrient: round(sum(pulp.value(x[i]) * nutrient_composition.get(nutrient, {}).get(i, 0) for i in ingredients.keys()), 2) for nutrient in requirements.keys()}

    return {
        "status": pulp.LpStatus[model.status],
        "feed_composition": result,
        "total_cost": round(total_cost, 2),
        "requirements": requirements,
        "final_nutrient_composition": final_nutrients
    }
