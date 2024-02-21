import pygame
import random
import csv
import numpy as np
import time
from datetime import datetime
import os

speed_increase_factor = 1.0
PIPE_SPEED = -3


def get_player_folder_path(player_id):
    folder_path = os.path.join("player_videos", str(player_id))
    
    # Create the folder if it doesn't exist
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    return folder_path


def get_or_create_player_id(player_name, file_path='player_keys.csv'):
    try:
        with open(file_path, mode='r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['Names'] == player_name:
                    return row['ID']  # Return existing ID for the player
    except FileNotFoundError:
        pass  # File doesn't exist yet, will be created when adding new player

    # Generate a new ID for new players
    new_id = str(random.randint(10000, 99999))  # Consider a more robust ID generation method for production
    with open(file_path, mode='a', newline='') as csvfile:
        fieldnames = ['ID', 'Names']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if csvfile.tell() == 0:
            writer.writeheader()  # If file is empty, write header
        writer.writerow({'ID': new_id, 'Names': player_name})

    return new_id




# Game Environment
class GameEnvironment:
    def __init__(self, screen_width, screen_height):
        pygame.init()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.background_img = pygame.transform.scale(pygame.image.load('Images/bg2.png').convert(), (self.screen_width, self.screen_height))
        self.score_font = pygame.font.Font(None, 32)
        self.WHITE = (255, 255, 255)

    def draw_background(self):
        self.screen.blit(self.background_img, (0, 0))

    def show_score(self, score):
        score_surface = self.score_font.render(f'Score: {int(score)}', True, self.WHITE)
        score_rect = score_surface.get_rect(center=(self.screen_width // 2, 20))
        self.screen.blit(score_surface, score_rect)

# Bird
class Bird:
    GRAVITY = 0.25
    JUMP_FORCE = -5

    def __init__(self, screen_height):
        self.image = pygame.transform.scale(pygame.image.load('Images/bird.png').convert_alpha(), (50, 35))
        self.rect = self.image.get_rect(center=(100, screen_height // 2))
        self.movement = 0

    def jump(self):
        self.movement = self.JUMP_FORCE

    def move(self):
        self.movement += self.GRAVITY
        self.rect.centery += self.movement

    def draw(self, screen):
        screen.blit(self.image, self.rect)




# Pipe
class Pipe(pygame.sprite.Sprite):
    

    def __init__(self, screen_width, screen_height, gap_size):
        pygame.sprite.Sprite.__init__(self)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.gap_size = gap_size
        self.image = pygame.Surface((20, self.screen_height))
        self.image.fill((0, 255, 0))
        self.rect = self.image.get_rect()

        # Determine the position of the top and bottom pipes
        gap_y = random.randint(self.gap_size // 2, self.screen_height - self.gap_size // 2)
        top_height = gap_y - self.gap_size // 2
        bottom_height = self.screen_height - (gap_y + self.gap_size // 2)

        # Create two pipe instances for top and bottom
        self.top_pipe = pygame.Rect(self.screen_width + 100, 0, 20, top_height)
        self.bottom_pipe = pygame.Rect(self.screen_width + 100, gap_y + self.gap_size // 2, 20, bottom_height)
        self.score_counted = False
        






    def move(self):
        self.top_pipe.centerx += PIPE_SPEED*speed_increase_factor
        self.bottom_pipe.centerx += PIPE_SPEED*speed_increase_factor

    def draw(self, screen):
        pygame.draw.rect(screen, (0, 255, 0), self.top_pipe)
        pygame.draw.rect(screen, (0, 255, 0), self.bottom_pipe)

    def is_off_screen(self):
        return self.top_pipe.right < 0

    def check_collision(self, bird):
        return self.top_pipe.colliderect(bird.rect) or self.bottom_pipe.colliderect(bird.rect)


# Game
class FlappyBirdGame:
    SCREEN_WIDTH, SCREEN_HEIGHT = 800, 400
    GAME_SPEED = 70

    def __init__(self):
        self.player_name = input("Please enter your full name: ")
        self.player_id = get_or_create_player_id(self.player_name)  # Retrieve or create a unique player ID
        print(f"Welcome, {self.player_name}! Your player ID is {self.player_id}.")
        self.env = GameEnvironment(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        self.start_time = None
        self.end_time = None
        
        self.bird = Bird(self.SCREEN_HEIGHT)
        self.pipes = [Pipe(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, random.randint(100, 300)) for _ in range(2)]
        self.score = 0
        self.game_active = False
        self.game_start = True
        self.clock = pygame.time.Clock()

        # Initialize sound
        pygame.mixer.init()
        self.flap_sound = pygame.mixer.Sound('Sounds/Flap_Sound.mp3')
        self.game_over_sound = pygame.mixer.Sound('Sounds/Game_Over_Sound.mp3')
        self.time = time.time() # Save the initial time

    def check_all_collisions(self):
        # Check for pipe collisions
        for pipe in self.pipes:
            if pipe.check_collision(self.bird):
                self.game_over_sound.play()
                self.game_active = False
                self.end_time = datetime.now()  # Record the end time
                self.save_score()
                time.sleep(2)
                break
        
        # Check for floor and ceiling collisions
        if self.bird.rect.top <= 0 or self.bird.rect.bottom >= self.SCREEN_HEIGHT:
            self.game_over_sound.play()
            self.game_active = False
            self.end_time = datetime.now()  # Record the end time
            self.save_score()
            time.sleep(1)


    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        if not self.game_start:
                            self.game_start = True
                            self.game_active = True
                            self.reset_game()
                            self.start_time = datetime.now()  # Record the start time
                        elif self.game_active:
                            self.bird.jump()
                            self.flap_sound.play()
                        else:
                            self.reset_game()
                            self.start_time = datetime.now()  # Record the start time

            self.env.draw_background()
            if self.game_active:
                self.bird.move()
                self.bird.draw(self.env.screen)
                self.check_all_collisions()  
                self.handle_pipes()
                self.env.show_score(self.score)

            self.display_game_status()

            pygame.display.update()
            self.clock.tick(self.GAME_SPEED)

    def handle_pipes(self):
        global speed_increase_factor
        # Add pipes more frequently
        if not self.pipes or self.pipes[-1].bottom_pipe.centerx < self.SCREEN_WIDTH - 100:  # Adjusted distance for more frequent pipes
            gap_size = random.randint(100, 300)
            elapsed_time = time.time() - self.time
            decay_factor = np.exp(-elapsed_time / 100)  # Decay the gap size over time
            new_pipe = Pipe(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, int(float(decay_factor)*gap_size))
            self.pipes.append(new_pipe)

        # Move and draw pipes, and remove off-screen pipes
        for pipe in list(self.pipes):
            pipe.move()

            # Check if the bird has passed the pipe to increment the score
            if not pipe.score_counted and pipe.bottom_pipe.centerx < self.bird.rect.left:
                self.score += 1
                pipe.score_counted = True
                speed_increase_factor += 0.1  # Increase the speed of the pipes over time

            pipe.draw(self.env.screen)
            if pipe.is_off_screen():
                self.pipes.remove(pipe)

        
        # Check for collisions
        for pipe in self.pipes:
            if pipe.check_collision(self.bird):
                self.game_over_sound.play()
                self.game_active = False
                self.save_score()
                time.sleep(1)
                break


    def reset_game(self):
        global speed_increase_factor
        speed_increase_factor = 1.0
        self.bird = Bird(self.SCREEN_HEIGHT)
        self.pipes = [Pipe(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, random.randint(100, 300))]
        self.score = 0
        self.game_active = True
        self.game_start = True


    def display_game_status(self):
        if self.game_start and not self.game_active:
            start_font = pygame.font.Font(None, 32)
            start_surface = start_font.render('Press Space to Start', True, self.env.WHITE)
            start_rect = start_surface.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2))
            self.env.screen.blit(start_surface, start_rect)
        elif not self.game_start and not self.game_active:
            game_over_font = pygame.font.Font(None, 64)
            restart_font = pygame.font.Font(None, 32)

            game_over_surface = game_over_font.render('Game Over', True, self.env.WHITE)
            game_over_rect = game_over_surface.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 3))
            self.env.screen.blit(game_over_surface, game_over_rect)

            restart_surface = restart_font.render('Press Space to Restart', True, self.env.WHITE)
            restart_rect = restart_surface.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2))
            self.env.screen.blit(restart_surface, restart_rect)


    def save_score(self):
        filename = 'scores.csv'
        fieldnames = ['name', 'score', 'start_time', 'end_time', 'duration']

        # Check if file is empty
        file_is_empty = False
        try:
            with open(filename, 'r') as csvfile:
                file_is_empty = csvfile.read() == ''
        except FileNotFoundError:
            file_is_empty = True

        with open(filename, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write headers if file is empty
            if file_is_empty:
                writer.writeheader()

            if self.end_time is None:
                self.end_time = datetime.now()

            duration = self.end_time - self.start_time
            writer.writerow({'name': self.player_name, 'score': self.score, 'start_time': self.start_time, 'end_time': self.end_time, 'duration': duration})


def run_the_game():
    game = FlappyBirdGame()
    game.run()


run_the_game()

