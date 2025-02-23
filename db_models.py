from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum

class IngredientCategory(str, Enum):
    ENERGY_SOURCE = "energy_source"
    PROTEIN_SOURCE = "protein_source"
    ADDITIVE = "additive"

class Ingredient(SQLModel, table=True):
    __tablename__ = "ingredients"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    category: IngredientCategory
    min_inclusion: float
    max_inclusion: float
    description: Optional[str] = None
    
    # Relationships
    costs: List["IngredientCost"] = Relationship(back_populates="ingredient")
    nutrient_compositions: List["NutrientComposition"] = Relationship(back_populates="ingredient")

class Nutrient(SQLModel, table=True):
    __tablename__ = "nutrients"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)  # e.g., ME, CP, Ca
    unit: str  # e.g., %, MJ/kg
    description: Optional[str] = None
    
    # Relationships
    compositions: List["NutrientComposition"] = Relationship(back_populates="nutrient")
    requirements: List["NutrientRequirement"] = Relationship(back_populates="nutrient")

class IngredientCost(SQLModel, table=True):
    __tablename__ = "ingredient_costs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    ingredient_id: int = Field(foreign_key="ingredients.id")
    cost: float
    date: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship
    ingredient: Ingredient = Relationship(back_populates="costs")

class NutrientComposition(SQLModel, table=True):
    __tablename__ = "nutrient_composition"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    ingredient_id: int = Field(foreign_key="ingredients.id")
    nutrient_id: int = Field(foreign_key="nutrients.id")
    value: float
    
    # Relationships
    ingredient: Ingredient = Relationship(back_populates="nutrient_compositions")
    nutrient: Nutrient = Relationship(back_populates="compositions")
    
class BirdType(SQLModel, table=True):
    __tablename__ = "bird_types"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)  # e.g., layers, broilers
    description: Optional[str] = None
    
    # Relationships
    feed_stages: List["FeedStage"] = Relationship(back_populates="bird_type")

class FeedStage(SQLModel, table=True):
    __tablename__ = "feed_stages"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    bird_type_id: int = Field(foreign_key="bird_types.id")
    name: str = Field(index=True)  # e.g., starter, grower
    start_week: int
    end_week: int
    description: Optional[str] = None
    
    # Relationships
    bird_type: BirdType = Relationship(back_populates="feed_stages")
    nutrient_requirements: List["NutrientRequirement"] = Relationship(back_populates="feed_stage")

class NutrientRequirement(SQLModel, table=True):
    __tablename__ = "nutrient_requirements"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    feed_stage_id: int = Field(foreign_key="feed_stages.id")
    nutrient_id: int = Field(foreign_key="nutrients.id")
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    week: Optional[int] = None  # For week-specific requirements
    
    # Relationships
    feed_stage: FeedStage = Relationship(back_populates="nutrient_requirements")
    nutrient: Nutrient = Relationship(back_populates="requirements")