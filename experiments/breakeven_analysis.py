# Unrelated: break-even analysis script for EV cost modeling (ignore)

import numpy as np
import matplotlib.pyplot as plt

# Given values
fixed_cost = 3000000  # 30 lakh (fixed cost per month)
variable_cost_per_unit = 580000  # Variable cost per unit
selling_price_per_unit = 1100000  # Selling price per unit (to adjust break-even point)
bep_units = fixed_cost / (selling_price_per_unit - variable_cost_per_unit)  # Break-even point in units

# X-axis range (number of EVs produced)
units = np.arange(0, 50, 1)

# Total Cost = Fixed Cost + Variable Cost per Unit * Units Produced
total_cost = fixed_cost + (variable_cost_per_unit * units)

# Total Revenue = Selling Price per Unit * Units Produced
total_revenue = selling_price_per_unit * units

# Fixed cost line
fixed_cost_line = np.full_like(units, fixed_cost)

# Plot the graph
plt.figure(figsize=(8, 5))
plt.plot(units, total_cost / 1e5, 'r--', label="Total Cost")  # Red dashed line for total cost
plt.plot(units, total_revenue / 1e5, 'b-', label="Total Revenue")  # Blue line for total revenue
plt.plot(units, fixed_cost_line / 1e5, 'g-.', label="Fixed Cost")  # Green dash-dot line for fixed cost

# Mark Break-Even Point
plt.axvline(bep_units, color='green', linestyle='dotted', label="Break-Even Point")
plt.scatter(bep_units, (fixed_cost + variable_cost_per_unit * bep_units) / 1e5, color='black', marker='x', s=100)

# Labels and Title
plt.xlabel("Number of EVs Produced")
plt.ylabel("INR (in Lakh)")
plt.title("Break-Even Analysis for EVs")
plt.legend()
plt.grid(True, linestyle="--", alpha=0.6)

# Show the graph
plt.show()












