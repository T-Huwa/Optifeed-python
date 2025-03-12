from ortools.linear_solver import pywraplp

def optimizeFood():
    # Nutrient minimums.
    nutrients = [
        ["DM", 0],
        ["ME", 12.5 ],
        ["CP", 20.00],
        ["Ca", 1.05],
        ["P", 0.45],
        ["Mg", 0.00],
        ["Na", 0.18],
        ["K", 0],
    ]

    # Ingridient, Unit, Price, DM,	ME,	CP,	Ca,	P,	Mg,	Na,	K,
    data = [
        # fmt: off
    ['Maize Bran', '1 kg', 300, 88.7, 8.8, 11.9, 0.47, 0.34, 0.22, 0.08, 0.73],
    ['White Maize', '1 kg', 1200, 90, 14.8, 8, 0.04, 0.29, 0.13, 0.05, 0.36],
    ['Wheat Bran', '1 kg', 300, 87, 7.4, 17.3, 0.14, 1.11, 0.45, 0.01, 1.37],
    ['Rice Bran', '1 kg', 300, 90.2, 10.6, 12.7, 0.07, 1.38, 0.65, 0.02, 1.23],
    ['Millet', '1 kg', 300, 89.6, 13.3, 12.5, 0.05, 0.33, 0.13, 0.009, 0.41],
    ['Sorghum', '1 kg', 300, 87.4, 16, 10.8, 0.03, 0.33, 0.18, 0.02, 0.43],
    ['Soya Full Fat', '1 kg', 1500, 88.6, 15.7, 39.5, 0.34, 0.59, 0.24, 0, 1.92],
    ['Soy Cake', '1 kg', 300, 93.2, 12.8, 47, 0.37, 0.69, 0.29, 0.011, 2.24],
    ['Sunflower', '1 kg', 300, 92.8, 19.7, 16, 0.27, 0.57, 0.29, 0.007, 0.84],
    ['Sunflower Cake', '1 kg', 450, 91.8, 10.8, 27.9, 0.39, 0.92, 0.36, 0.01, 1.12],
    ['Fish Meal', '1 kg', 300, 92.5, 12, 48.4, 7.93, 3.98, 0, 2.84, 1.11],
    ['BSF', '1 kg', 300, 91.3, 12, 42.1, 7.56, 0.9, 0.39, 0.13, 0.69],
        # fmt: on
    ]


    # Instantiate a Glop solver and naming it.
    solver = pywraplp.Solver.CreateSolver("GLOP")
    if not solver:
        return
    
    # Declare an array to hold our variables.
    foods = [solver.NumVar(0.0, solver.infinity(), item[0]) for item in data]

    print("Number of variables =", solver.NumVariables())

    constraints = []
    for i, nutrient in enumerate(nutrients):
        constraints.append(solver.Constraint(nutrient[1], solver.infinity()))
        for j, item in enumerate(data):
            constraints[i].SetCoefficient(foods[j], item[i + 3])

    print("Number of constraints =", solver.NumConstraints())

    # Objective function: Minimize the sum of (price-normalized) foods.
    objective = solver.Objective()
    for food in foods:
        objective.SetCoefficient(food, 1)
    objective.SetMinimization()

    # objective = solver.Objective()
    # for i, food in enumerate(foods):
    #     objective.SetCoefficient(food, data[i][2])
    # objective.SetMinimization()

    weight_constraint = solver.Constraint(0, 100.0)
    for j, item in enumerate(data):
        weight_constraint.SetCoefficient(foods[j], 1)

    print(f"Solving with {solver.SolverVersion()}")
    status = solver.Solve()

    if status != solver.OPTIMAL:
        print("The problem does not have an optimal solution!")
        if status == solver.FEASIBLE:
            print("A potentially suboptimal solution was found.")
        return


    nutrients_result = [0] * len(nutrients)
    print("\ Feed:")
    for i, food in enumerate(foods):
        if food.solution_value() > 0.0:
            print("{}: MWK{}".format(data[i][0], food.solution_value()))
            for j, _ in enumerate(nutrients):
                nutrients_result[j] += data[i][j + 3] * food.solution_value()
    print("\nOptimal price: MWK{:.4f}".format( objective.Value()))

    print("\nNutrient Requirement:")
    for i, nutrient in enumerate(nutrients):
        print(
            "{}: {:.2f} (min {})".format(nutrient[0], nutrients_result[i], nutrient[1])
        )

    print("\nFeed for 100kg Bag:")
    for i, food in enumerate(foods):
        if food.solution_value() > 0.0:
            amount_per_100kg = 100.0 * food.solution_value()
            print("{}: {:.2f} kg for a 100 kg bag".format(data[i][0], amount_per_100kg))

optimizeFood()

