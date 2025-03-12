import scipy.optimize as opt
import numpy as np

# Ingredient names
ingredient_names = [
    "Maize Bran", "White Maize", "Wheat Bran", "Rice Bran", "Millet", 
    "Sorghum", "Soya Full Fat", "Soy Cake", "Sunflower", 
    "Sunflower Cake", "Fish Meal", "BSF"
]

# Nutrient minimums (g or MJ per kg of feed).
nutrients = np.array([
    0,    # DM (not constrained)
    12.5, # ME (MJ)
    20.0, # CP (%)
    1.05, # Ca (%)
    0.45, # P (%)
    0.0,  # Mg (%)
    0.18, # Na (%)
    0     # K (%)
])

# Ingredient data: [Price, DM, ME, CP, Ca, P, Mg, Na, K]
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

# Objective function: minimize cost.
def objective(x):
    return np.dot(prices, x)

# Constraints for nutrients.
constraints = [
    {"type": "eq", "fun": lambda x: np.sum(x) - 100},  # Total weight must be 100 kg
]

for i in range(len(nutrients)):
    constraints.append({
        "type": "ineq",
        "fun": lambda x, i=i: np.dot(nutrient_matrix[i], x) - nutrients[i]
    })

# Bounds: non-negative amounts.
bounds = [(0, None) for _ in range(len(data))]

# Non-uniform initial guess (random values summing to 100)
initial_guess = np.random.rand(len(data))
initial_guess = initial_guess / np.sum(initial_guess) * 100

# Run optimization.
result = opt.minimize(objective, initial_guess, bounds=bounds, constraints=constraints, method="SLSQP")

# Prepare result.
if result.success:
    print("\nFeed for 100kg Bag:")
    for i, amount in enumerate(result.x):
        if amount > 0:
            print(f"{ingredient_names[i]}: {amount:.2f} kg (Cost: MWK{amount * prices[i]:.2f})")
    print(f"\nOptimal total cost: MWK{result.fun:.2f}")

    # Calculate nutrient content in the final mix
    final_nutrients = np.dot(nutrient_matrix, result.x)
    print("\nNutrient Content in Final Mix:")
    print(f"DM: {final_nutrients[0]:.2f}% (Min: {nutrients[0]:.2f}%)")
    print(f"ME: {final_nutrients[1]:.2f} MJ/kg (Min: {nutrients[1]:.2f} MJ/kg)")
    print(f"CP: {final_nutrients[2]:.2f}% (Min: {nutrients[2]:.2f}%)")
    print(f"Ca: {final_nutrients[3]:.2f}% (Min: {nutrients[3]:.2f}%)")
    print(f"P: {final_nutrients[4]:.2f}% (Min: {nutrients[4]:.2f}%)")
    print(f"Mg: {final_nutrients[5]:.2f}% (Min: {nutrients[5]:.2f}%)")
    print(f"Na: {final_nutrients[6]:.2f}% (Min: {nutrients[6]:.2f}%)")
    print(f"K: {final_nutrients[7]:.2f}% (Min: {nutrients[7]:.2f}%)")
else:
    print("Optimization failed.")