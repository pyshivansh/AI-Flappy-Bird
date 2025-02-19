import pygame
from random import randint
from sys import exit
from pandas import DataFrame, read_csv
from math import ceil
from ai_model import return_model
from numpy import array, expand_dims
import threading
from queue import Queue
import os

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# Initialize pygame
pygame.init()
game_font_style = "Monsterrat"

# Set up display dimensions and window position
display_size = [pygame.display.Info().current_w, pygame.display.Info().current_h]
win_length, win_height = int(display_size[0]*0.75), int(display_size[1]*0.75)
win_x, win_y = display_size[0]/2-win_length/2, display_size[1]/2-win_height/2
os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (win_x, win_y)

# Create the game window
window = pygame.display.set_mode((win_length, win_height))
pygame.display.set_caption("AI Flappy Bird")
game_font = pygame.font.SysFont(game_font_style, 60)

# Define colors and player size
white = (255, 255, 255)
black = (0, 0, 0)
player_size = (51, 36)

# Load and scale game assets
player_upflap = pygame.image.load(os.path.join("Assets", "redbird-upflap.png")).convert()
player_upflap = pygame.transform.scale(player_upflap, player_size)
player_downflap = pygame.image.load(os.path.join("Assets", "redbird-downflap.png")).convert()
player_downflap = pygame.transform.scale(player_downflap, player_size)
pipe = pygame.image.load(os.path.join("Assets", "pipe-green.png")).convert()
bg = pygame.image.load(os.path.join("Assets", "background-day.png")).convert()
bg = pygame.transform.scale(bg, (win_length, win_height))
game_over = pygame.image.load(os.path.join("Assets", "gameover.png")).convert_alpha()
game_over = pygame.transform.scale(game_over, (300, 75))
base = pygame.image.load(os.path.join("Assets", "base.png")).convert()
base = pygame.transform.scale(base, (win_length, 50))

# Set up game clock and FPS
fps = 60
clock = pygame.time.Clock()

# Initialize game variables
score = 0
game_enabled = True
run_ai = True
data_rows_collected = 0
data_rows_limit = 200

# Load dataset and initialize model
dataset_file = os.path.join("Assets", "data.csv")
dataset = read_csv(dataset_file)
data_cols = dataset.columns
curr_data = []
complete_model = return_model(True)

# Spawner class to manage obstacle generation
class Spawner:
    def __init__(self, x_range, gap, min_pipe_length, fps):
        self.x_min, self.x_max = x_range
        self.gap = gap
        self.min_pipe_length = min_pipe_length
        self.curr_x_gap = randint(self.x_min, self.x_max)
        self.obstacle_list = []
        self.limit = ceil(win_length/self.x_min)*25
        self.fps = fps
        self.x_gap_remaining = self.curr_x_gap
        
    def set_new_xGap(self):
        self.curr_x_gap = randint(self.x_min, self.x_max)
        self.x_gap_remaining = self.curr_x_gap
        
    def create_new_pair(self, x_pos):
        top_pipe_height = randint(self.min_pipe_length, win_height-base.get_height()-self.gap-self.min_pipe_length)
        self.obstacle_list.append(Obstacle(x_pos, 50, top_pipe_height, "top", pipe, 100))
        self.obstacle_list.append(Obstacle(x_pos, 50, win_height-base.get_height()-top_pipe_height-self.gap, "bottom", pipe, 100))
        
    def start_spawner(self, player_x):
        self.obstacle_list = []
        positions = [player_x+self.curr_x_gap]
        while positions[-1] < win_length*2:
            self.set_new_xGap()
            positions.append(positions[-1]+self.curr_x_gap)
        for i in positions:
            self.create_new_pair(i)
    
    def maintain_spawner(self, game_enabled):
        for i in self.obstacle_list:
            if game_enabled:
                i.move_obstacle(self.fps)
            i.display_obstacle()
        if game_enabled:
            self.x_gap_remaining -= self.obstacle_list[-1].speed/fps
            if self.x_gap_remaining <= 0:
                if len(self.obstacle_list) < self.limit*2:
                    self.create_new_pair(self.obstacle_list[-1].x+self.curr_x_gap)
                    self.set_new_xGap()
                elif self.obstacle_list[0].x < 0-self.obstacle_list[0].length:
                    self.obstacle_list.remove(self.obstacle_list[0])
                    self.obstacle_list.remove(self.obstacle_list[0])
                

# Obstacle class to manage individual pipes
class Obstacle:
    def __init__(self, x, length, height, surface, image, speed):
        self.x = x
        self.length, self.height = length, height
        self.image = pygame.transform.scale(image, (self.length, self.height))
        if surface == "top":
            self.y = 0
            self.image = pygame.transform.rotate(self.image, 180)
        else:
            self.y = win_height-base.get_height()-self.height
        self.rect = pygame.Rect(self.x, self.y, self.length, self.height)
        self.speed = speed
    
    def move_obstacle(self, fps):
        self.x -= self.speed/fps
        self.rect = pygame.Rect(self.x, self.y, self.length, self.height)

    def display_obstacle(self):
        window.blit(self.image, (self.x, self.y))


# Player class to manage the bird
class Player:
    def __init__(self, x, y, images, gravity, bounce, speed_modifier):
        self.x, self.y = x, y
        self.up_image, self.down_image = images
        self.curr_image = self.up_image
        self.length, self.height = self.curr_image.get_width(), self.curr_image.get_height()
        self.rect = pygame.Rect(self.x, self.y, self.length, self.height)
        self.click_enabled = True
        self.gravity, self.terminal_velocity = gravity, gravity*3
        self.curr_force = self.gravity
        self.bounce = bounce
        self.speed_modifier = speed_modifier
        self.target_obstacle, self.danger_obstacles = None, None
    
    def click(self):
        if self.click_enabled:
            self.curr_force = -self.bounce
    
    def move(self, frame, obstacle_list):
        if self.target_obstacle is None:
            self.score(obstacle_list)
        score = 0
        self.y += self.curr_force/fps*self.speed_modifier
        self.rect = pygame.Rect(self.x, self.y, self.length, self.height)
        self.curr_force += self.gravity/fps*self.speed_modifier
        self.curr_force = min([self.curr_force, self.terminal_velocity])
        if self.x > self.target_obstacle.x+self.target_obstacle.length:
            score += 1
            self.score(obstacle_list)
        return score
    
    def score(self, obstacle_list):
        for i in range(0, len(obstacle_list)):
            if obstacle_list[i].x+obstacle_list[i].length > self.x:
                self.target_obstacle = obstacle_list[i]
                self.danger_obstacles = [self.target_obstacle, obstacle_list[i+1]]
                break
     
    def check_collision(self):
        for i in self.danger_obstacles:
            if self.rect.colliderect(i.rect):
                return False
        if self.y <= 0:
            return False
        if self.y+self.height >= win_height-base.get_height():
            return False
        return True
        
    def display_player(self):
        window.blit(self.curr_image, (self.x, self.y))
   

# Initialize player and spawner
player = Player(100, win_height/2-player_upflap.get_height()/2, [player_upflap, player_downflap], 80, 100, 3)
spawner = Spawner([230, 270], 140, 25, fps)


# Function to start the game
def start_game():
    spawner.start_spawner(player.x)
    player.y = win_height/2-player_upflap.get_height()/2
    player.score(spawner.obstacle_list)
    return [0, 0, True]


# Function to collect data for training
def add_data(player, spawner):
    global curr_data
    gap, harshness = 0.7, 20
    obstacles = player.danger_obstacles
    dist_from_optimal = abs(player.y-(obstacles[0].y+obstacles[0].height+spawner.gap*gap))
    accuracy = 1-(dist_from_optimal*harshness)/win_height
    new_data = [player.y, obstacles[0].y+obstacles[0].height, obstacles[1].y, 
                (player.y-(obstacles[0].y+obstacles[0].height)), obstacles[1].y-player.y, 
                accuracy, gap]
    curr_data = new_data
    

# Function to upload collected data to the dataset
def upload_data(data):
    global dataset
    organised_data = {}
    decimal_places = 1
    for j in range(0, len(data)):
        if data_cols[j] == "Accuracy":
            decimal_places = 4
        organised_data[data_cols[j]] = [round(data[j], decimal_places)]
    new_row = DataFrame(organised_data)
    new_row.to_csv(dataset_file, mode="a", index=False, header=False)
 

# Function to predict the next move using the AI model
def predict_data(input_queue, output_queue):
    global complete_model
    while True:
        clock.tick(fps)
        data = input_queue.get()
        if data is None:
            break
        if data.ndim == 1:
            data = expand_dims(data, axis=0)
        prediction = complete_model.predict(data)
        output_queue.put(prediction)
        

# Function to prepare data for prediction
def enter_data(player, spawner, input_queue):
    obstacles = player.danger_obstacles
    gap = 0.7
    new_data = array([obstacles[0].y+obstacles[0].height, obstacles[1].y, 
                spawner.gap*gap, spawner.gap*(1-gap), 1, gap])
    input_queue.put(new_data)


# Main game loop
def main():
    global curr_data
    global complete_model
    global data_rows_collected, data_rows_limit
    # Game control variables
    run = True
    auto_retry = True
    data_for_failure = False
    # Initialize game state
    score, curr_score, game_enabled = start_game()
    rendered_score_text = game_font.render(f"{score}", True, black)
    restart_game_text = game_font.render("Press 'R' to restart game.", True, black)
    # Create input/output queues for AI predictions
    input_queue, output_queue = Queue(), Queue()
    predict_thread = threading.Thread(target=predict_data, args=(input_queue, output_queue))
    predict_thread.start()
    prediction = None
    while run:
        clock.tick(fps)
        # Handle user inputs
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False  
            if event.type == pygame.KEYDOWN:
                if game_enabled and event.key == pygame.K_SPACE and not run_ai:
                    add_data(player, spawner)  # Collect data for AI training
                    player.click()  
                if not game_enabled and event.key == pygame.K_r:
                    score, curr_score, game_enabled = start_game()
                    rendered_score_text = game_font.render(f"{score}", True, black)
                    prediction = None
                    data_for_failure = False  # Reset failure tracking
        # Render background
        window.fill(white)
        window.blit(bg, (0, 0))
        # Update game mechanics if player is alive
        if player.y + player.height < win_height:
            score += player.move(fps, spawner.obstacle_list)
        if game_enabled:
            # AI-driven actions
            if prediction is not None and player.y >= prediction and run_ai:
                add_data(player, spawner)
                player.click()
            if input_queue.empty() and prediction is None and run_ai:
                enter_data(player, spawner, input_queue)
                prediction = output_queue.get()
            # Update score if it increases
            if score > curr_score:
                prediction = None  # Reset AI prediction
                rendered_score_text = game_font.render(f"{score}", True, black)
                curr_score = score
                upload_data(curr_data)  # Save collected data
                curr_data = []  
                data_rows_collected += 1  # Track collected data rows
            game_enabled = player.check_collision()  
        else:
            score = curr_score 
        # Display game elements
        player.display_player()
        spawner.maintain_spawner(game_enabled)
        window.blit(base, (0, win_height - base.get_height()))
        window.blit(rendered_score_text, (win_length - 1.25 * game_font.size(f"{score}")[0], 15))
        # Handle game over scenario
        if not game_enabled:
            if not data_for_failure:
                upload_data(curr_data)  # Save failure data
                data_for_failure = True
                data_rows_collected += 1
            if auto_retry:
                score, curr_score, game_enabled = start_game()
                rendered_score_text = game_font.render(f"{score}", True, black)
                prediction = None
                data_for_failure = False
            else:
                # Display game over screen and restart prompt
                window.blit(game_over, (win_length / 2 - game_over.get_width() / 2, (win_height - base.get_height()) / 2 - game_over.get_height() / 2))
                window.blit(restart_game_text, (win_length / 2 - restart_game_text.get_width() / 2, (win_height - base.get_height()) / 2 - restart_game_text.get_height() / 2 + 100))
        # Stop the game if data collection limit is reached
        if data_rows_collected >= data_rows_limit:
            break
        pygame.display.update()
    # Clean up AI thread
    input_queue.put(None)
    predict_thread.join()


if __name__ == "__main__":
    while True:
        main()
        if data_rows_collected >= data_rows_limit:
            complete_model = return_model(True)
            data_rows_collected = 0
            print("New model being created.")
        else:
            break
    exit()