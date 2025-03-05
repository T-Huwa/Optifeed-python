from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True, nullable=False)
    password: str = Field(nullable=False)
    phone_number: Optional[str] = None
    

class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    ingredients: List["Ingredient"] = Relationship(back_populates="category")


class Ingredient(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    price: Optional[float] = None
    category_id: int = Field(foreign_key="category.id")

    category: Optional[Category] = Relationship(back_populates="ingredients")
    nutrient_compositions: List["NutrientComposition"] = Relationship(back_populates="ingredient")
    additive_requirements: List["AdditiveRequirement"] = Relationship(back_populates="ingredient")


class NutritionalRequirement(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    feed_type: str
    category: str  # Choices: "Layers", "Broilers"
    age: int
    DM: Optional[float] = None  # Dry Matter (%)
    ME: Optional[float] = None  # Metabolizable Energy (MJ/kg)
    CP: Optional[float] = None  # Crude Protein (%)
    Ca: Optional[float] = None  # Calcium (%)
    P: Optional[float] = None  # Phosphorus (%)
    Mg: Optional[float] = None  # Magnesium (%)
    Na: Optional[float] = None  # Sodium (%)
    K: Optional[float] = None  # Potassium (%)

    # Additives
    premix: Optional[float] = None
    toxicin: Optional[float] = None
    lysine: Optional[float] = None
    methionine: Optional[float] = None
    threonine: Optional[float] = None
    salt: Optional[float] = None
    tyrosine: Optional[float] = None
    mcp: Optional[float] = None
    lime: Optional[float] = None

    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class NutrientComposition(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ingredient_id: int = Field(foreign_key="ingredient.id")
    DM: int
    ME: int
    CP: int
    Ca: int
    P: int
    Mg: int
    Na: int
    K: int
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    ingredient: Optional[Ingredient] = Relationship(back_populates="nutrient_compositions")


class AdditiveRequirement(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ingredient_id: int = Field(foreign_key="ingredient.id")
    feed_category: str
    amount: float
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    ingredient: Optional[Ingredient] = Relationship(back_populates="additive_requirements")
