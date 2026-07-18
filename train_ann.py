import numpy as np

# 1. PARSE THE LOGS AND EXTRACT FEATURES
print("Parsing logs.txt to extract agent features...")

agents = ["Aldric", "Maren", "Corvus", "Sylva", "Brennan", "Isolde", "Theron", "Wren"]
# Ground truth labels based on game rules (1 = Wolf, 0 = Villager)
labels = {"Aldric": 1, "Maren": 1, "Corvus": 0, "Sylva": 0, "Brennan": 0, "Isolde": 0, "Theron": 0, "Wren": 0}

# Feature Vector: [num_speaks, num_moves, num_votes_cast, num_accused]
features = {agent: [0.0, 0.0, 0.0, 0.0] for agent in agents}

try:
    with open('logs.txt', 'r', encoding='utf-8') as f:
        for line in f:
            # Check speaks
            if '[SPEAK]' in line:
                for agent in agents:
                    if line.startswith(f"[SPEAK] {agent}"):
                        features[agent][0] += 1
            # Check moves
            if '[MOVE]' in line:
                for agent in agents:
                    if line.startswith(f"[MOVE] {agent}"):
                        features[agent][1] += 1
            # Check votes
            if '[VOTE]' in line:
                for agent in agents:
                    if line.startswith(f"[VOTE] {agent}"):
                        features[agent][2] += 1
            # Check accuses (who was accused)
            if '[ACCUSE]' in line:
                for agent in agents:
                    if f"accuses {agent}" in line:
                        features[agent][3] += 1
except FileNotFoundError:
    print("Could not find logs.txt. Ensure it is in the same directory.")
    exit(1)

# Convert to numpy arrays
X = np.array([features[agent] for agent in agents])
y = np.array([[labels[agent]] for agent in agents])

# Normalize features (Min-Max scaling to 0-1 range for neural network stability)
max_vals = np.max(X, axis=0)
max_vals[max_vals == 0] = 1 # avoid division by zero
X = X / max_vals

print("Feature Extraction Complete.\n")


# 2. BUILD AND TRAIN A FROM-SCRATCH NEURAL NETWORK
print("Training Neural Network (Multi-Layer Perceptron)...")

# Hyperparameters
np.random.seed(42)
input_layer_neurons = X.shape[1]  # 4 features
hidden_layer_neurons = 8          # 1 hidden layer with 8 neurons
output_neurons = 1                # Binary classification (Wolf or not)
learning_rate = 0.1
epochs = 5000

# Initialize Weights and Biases randomly
W1 = np.random.uniform(-1, 1, (input_layer_neurons, hidden_layer_neurons))
b1 = np.zeros((1, hidden_layer_neurons))
W2 = np.random.uniform(-1, 1, (hidden_layer_neurons, output_neurons))
b2 = np.zeros((1, output_neurons))

# Activation Functions
def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def sigmoid_derivative(x):
    return x * (1 - x)

# Training Loop
for epoch in range(epochs):
    # --- FORWARD PROPAGATION ---
    hidden_layer_input = np.dot(X, W1) + b1
    hidden_layer_activation = sigmoid(hidden_layer_input)

    output_layer_input = np.dot(hidden_layer_activation, W2) + b2
    predicted_output = sigmoid(output_layer_input)

    # --- BACKWARD PROPAGATION (Learning) ---
    # Calculate error
    error = y - predicted_output
    
    # Calculate gradients for output layer
    d_predicted_output = error * sigmoid_derivative(predicted_output)

    # Calculate gradients for hidden layer
    error_hidden_layer = d_predicted_output.dot(W2.T)
    d_hidden_layer = error_hidden_layer * sigmoid_derivative(hidden_layer_activation)

    # Update Weights and Biases
    W2 += hidden_layer_activation.T.dot(d_predicted_output) * learning_rate
    b2 += np.sum(d_predicted_output, axis=0, keepdims=True) * learning_rate
    W1 += X.T.dot(d_hidden_layer) * learning_rate
    b1 += np.sum(d_hidden_layer, axis=0, keepdims=True) * learning_rate

    if epoch % 1000 == 0:
        loss = np.mean(np.square(error))
        print(f"Epoch {epoch} | Loss: {loss:.4f}")

print("Training Complete!\n")

# 3. EVALUATE RESULTS
print("--- PREDICTION RESULTS ---")
print("Target: Closer to 1.0 = Wolf, Closer to 0.0 = Villager\n")

for i, agent in enumerate(agents):
    prediction = predicted_output[i][0]
    actual = "Wolf" if labels[agent] == 1 else "Villager"
    guess = "Wolf" if prediction >= 0.5 else "Villager"
    print(f"{agent.ljust(10)} | Pred: {prediction:.4f} ({guess.ljust(8)}) | Actual: {actual}")
