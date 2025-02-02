import pygame
from random import randint
from sys import exit
from pandas import DataFrame, read_csv
from math import ceil
from ai_model import complete_model
from numpy import array, expand_dims
import threading
from queue import Queue
import os

pygame.init()
game_font_style = "Monsterrat"

display_size = [pygame.display.Info().current_w, pygame.display.Info().current_h]
print(display_size)
win_length, win_height = int(display_size[0]*0.75), int(display_size[1]*0.75)
win_x, win_y = display_size[0]/2-win_length/2, display_size[1]/2-win_height/2
os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (win_x, win_y)
window = pygame.display.set_mode((win_length, win_height))
pygame.display.set_caption("AI Flappy Bird")
game_font = pygame.font.SysFont(game_font_style, 60)


white = (255, 255, 255)
black = (0, 0, 0)
player_size = (51, 36)

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

fps = 60
clock = pygame.time.Clock()

score = 0
game_enabled = True

dataset_file = os.path.join("Assets", "training_data.csv")
dataset = read_csv(dataset_file)
data_cols = dataset.columns
curr_data = []


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
   

player = Player(100, win_height/2-player_upflap.get_height()/2, [player_upflap, player_downflap], 80, 100, 3)
spawner = Spawner([230, 270], 140, 25, fps)


def start_game():
    spawner.start_spawner(player.x)
    player.y = win_height/2-player_upflap.get_height()/2
    player.score(spawner.obstacle_list)
    return [0, 0, True]


def add_data(player, spawner):
    global curr_data
    obstacles = player.danger_obstacles
    new_data = [player.y, obstacles[0].y+obstacles[0].height, obstacles[1].y, 
                (player.y-(obstacles[0].y+obstacles[0].height))/spawner.gap, abs((player.y-obstacles[1].y)/spawner.gap)]
    curr_data = new_data
    

def upload_data(data):
    global dataset
    organised_data = {}
    for j in range(0, len(data)):
        organised_data[data_cols[j]] = [data[j]]
    new_row = DataFrame(organised_data)
    new_row.to_csv(dataset_file, mode="a", index=False, header=False)
 

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
        

def enter_data(player, spawner, input_queue):
    obstacles = player.danger_obstacles
    gap = 0.6
    new_data = array([obstacles[0].y+obstacles[0].height, obstacles[1].y, 
                gap, 1-gap])
    input_queue.put(new_data)


def main():
    global curr_data
    run = True
    auto_retry = False
    score, curr_score, game_enabled = start_game()
    rendered_score_text = game_font.render(f"{score}", True, black)
    restart_game_text = game_font.render("Press 'R' to restart game.", True, black)
    input_queue, output_queue = Queue(), Queue()
    predict_thread = threading.Thread(target=predict_data, args=(input_queue, output_queue))
    predict_thread.start()
    prediction = None
    while run:
        clock.tick(fps)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if game_enabled and event.key == pygame.K_SPACE:
                    # add_data(player, spawner)
                    # player.click()
                    pass
                if not game_enabled and event.key == pygame.K_r:
                    score, curr_score, game_enabled = start_game()
                    rendered_score_text = game_font.render(f"{score}", True, black)
                    prediction = None
        window.fill(white)
        window.blit(bg, (0, 0))
        if player.y+player.height < win_height:
            score += player.move(fps, spawner.obstacle_list)
        if game_enabled:
            if prediction is not None and player.y >= prediction:
                # add_data(player, spawner)
                player.click()
            if input_queue.empty() and prediction is None:
                enter_data(player, spawner, input_queue)
                prediction = output_queue.get()
            if score > curr_score:
                prediction = None
                rendered_score_text = game_font.render(f"{score}", True, black)
                curr_score = score
                # upload_data(curr_data)
                curr_data = []
            game_enabled = player.check_collision()
        else:
            score = curr_score
        player.display_player()
        spawner.maintain_spawner(game_enabled)
        window.blit(base, (0, win_height-base.get_height()))
        window.blit(rendered_score_text, (win_length-1.25*game_font.size(f"{score}")[0], 15))
        if not game_enabled:
            if auto_retry:
                score, curr_score, game_enabled = start_game()
                rendered_score_text = game_font.render(f"{score}", True, black)
                prediction = None
            else:
                window.blit(game_over, (win_length/2-game_over.get_width()/2, (win_height-base.get_height())/2-game_over.get_height()/2))
                window.blit(restart_game_text, (win_length/2-restart_game_text.get_width()/2, (win_height-base.get_height())/2-restart_game_text.get_height()/2+100))
        pygame.display.update()
    input_queue.put(None)
    predict_thread.join()
    exit()


if __name__ == "__main__":
    main()