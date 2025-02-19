# AI Flappy Bird

## Description
This project is an AI-controlled version of the classic Flappy Bird game. Using machine learning, the AI learns to navigate the bird through pipes by optimizing its actions for the highest possible score. The game is implemented using Python and utilizes image assets to replicate the original Flappy Bird aesthetics.

## Features
- AI-controlled gameplay using a pre-trained model
- Realistic Flappy Bird visuals
- Dynamic pipe generation and collision detection
- Score tracking and game over screen

## Installation
```bash
# Clone the repository
git clone <https://github.com/pyshivansh/AI-Flappy-Bird.git>

# Install required dependencies
pip install -r requirements.txt

# Run the game
python Scripts/game.py
```

## Usage
- The game runs automatically with the AI controlling the bird.
- Observe the AI learning and then improving its score over time.

## Technologies Used
- Python.
- Machine Learning (using scikit-learn or a similar framework).
- Pygame for game rendering.

## File Structure
```
AI-Flappy-Bird/
│   .gitattributes
│   .gitignore
│   AI Flappy Bird.pyproj
│   AI Flappy Bird.sln
│   README.md
│
├── Assets/
│   ├── AI_model.pkl
│   ├── background-day.png
│   ├── base.png
│   ├── data.csv
│   ├── gameover.png
│   ├── pipe-green.png
│   ├── redbird-downflap.png
│   └── redbird-upflap.png
│
└── Scripts/
    ├── adjust_data.py
    ├── ai_model.py
    └── game.py
```

## AI Model Explanation
The AI model is trained through gameplay as for each new set of pipes, the AI attempts to find the y-level that it needs to be flapping at. Each time the AI attempts to go through a set of pipes, an accuracy score is calculated, which is a representation of how close to the perfect y-level did the AI choose to flap at. Regardless of whether the AI successfully passes through the set of pipes or not, a new data record is then added to `data.csv`, consisting of pipe information and the accuracy for that given attempt. This is so that the AI has more data to learn off and hence it will improve. 

## License
This project is licensed under the MIT License.

## Acknowledgments
- Inspired by the original Flappy Bird game by Dong Nguyen.
- Special thanks to open-source contributors for free Flappy Bird assets and tools (such as python modules) used in the project.
