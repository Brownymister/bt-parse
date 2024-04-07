import matplotlib.pyplot as plt

# Example data
x = [1, 2, 3, 4, 5]
y = ['A', 'B', 'C', 'D', 'E']

# Create a plot
plt.plot(x, y)

# Set y-axis ticks and labels
# Assuming you want ticks at positions 1, 2, 3, 4, 5 with corresponding labels 'A', 'B', 'C', 'D', 'E'
plt.yticks([1, 2, 3, 4, 5], ['A', 'B', 'C', 'D', 'E'])

# Customize tick appearance (optional)
plt.tick_params(axis='y', colors='r', length=10, width=2, direction='in')

# Show the plot
plt.savefig("aoeu.png")
