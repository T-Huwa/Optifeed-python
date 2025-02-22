from sqlmodel import Session, select
from models import (
    Category, Ingredient, NutritionalRequirement,
    NutrientComposition, AdditiveRequirement
)

# ✅ CREATE functions
def create_category(session: Session, name: str):
    category = Category(name=name)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category

def create_ingredient(session: Session, name: str, price: float, category_id: int):
    ingredient = Ingredient(name=name, price=price, category_id=category_id)
    session.add(ingredient)
    session.commit()
    session.refresh(ingredient)
    return ingredient

# ✅ READ functions
def get_categories(session: Session):
    return session.exec(select(Category)).all()

def get_ingredients(session: Session):
    return session.exec(select(Ingredient)).all()

def get_nutritional_requirements(session: Session):
    return session.exec(select(NutritionalRequirement)).all()

# ✅ UPDATE function
def update_ingredient_price(session: Session, ingredient_id: int, new_price: float):
    ingredient = session.get(Ingredient, ingredient_id)
    if ingredient:
        ingredient.price = new_price
        session.commit()
        session.refresh(ingredient)
    return ingredient

# ✅ DELETE function
def delete_ingredient(session: Session, ingredient_id: int):
    ingredient = session.get(Ingredient, ingredient_id)
    if ingredient:
        session.delete(ingredient)
        session.commit()
        return True
    return False
