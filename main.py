import pygame
import random
import csv
import numpy as np
import time
from datetime import datetime
import os
import re


speed_increase_factor = 1.0
PIPE_SPEED = -3

def render_text_with_outline(font, text, text_color, outline_color, x, y, screen):
    outline_width = 2  # Width of the outline in pixels

    # Create a surface for the text with outline
    text_surface = font.render(text, True, text_color)
    outline_surface = font.render(text, True, outline_color)

    # Render the outline by offsetting the text in all directions
    for dx, dy in [(-outline_width, -outline_width), (-outline_width, outline_width),
                   (outline_width, -outline_width), (outline_width, outline_width),
                   (0, -outline_width), (-outline_width, 0), (0, outline_width), (outline_width, 0)]:
        screen.blit(outline_surface, (x + dx, y + dy))

    # Render the main text on top
    screen.blit(text_surface, (x, y))

def get_player_folder_path(player_id):
    folder_path = os.path.join("player_videos", str(player_id))
    
    # Create the folder if it doesn't exist
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    return folder_path


def get_or_create_player_id(player_name, file_path='player_keys.csv'):
    # Trim, lowercase, and capitalise the first letter of each word
    formatted_name = player_name.strip().lower().title()

    try:
        with open(file_path, mode='r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['Names'].strip().lower() == formatted_name.lower():
                    return row['ID']  # Return existing ID for the player if found
    except FileNotFoundError:
        pass  # File doesn't exist yet, will be created when adding new player

    # Generate a new ID for new players
    new_id = str(random.randint(10000, 99999))
    with open(file_path, mode='a', newline='') as csvfile:
        fieldnames = ['ID', 'Names']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if csvfile.tell() == 0:
            writer.writeheader()  # If file is empty, write header
        writer.writerow({'ID': new_id, 'Names': formatted_name})

    return new_id




def is_valid_name(name):
    # Example pattern: Allow letters, numbers, spaces, and some common characters
    pattern = re.compile(r'^[a-zA-Z0-9 \-\']+$')
    return bool(pattern.match(name))




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
        self.background_img = pygame.transform.scale(pygame.image.load('Images/bg2.png').convert(), (screen_width, screen_height))

    def draw_background(self):
        self.screen.blit(self.background_img, (0, 0))

    def show_score(self, score):
        # Assuming 'screen' is your Pygame display surface
        score_text = f'Score: {int(score)}'
        text_color = (255, 255, 255)  # White
        outline_color = (0, 0, 0)  # Black

        # Calculate the position for the score text to be centered
        text_surface = self.score_font.render(score_text, True, text_color)
        x = (self.screen_width - text_surface.get_width()) // 2
        y = 20  # Fixed position from the top of the screen

        # Use the custom function to render the score with an outline
        render_text_with_outline(self.score_font, score_text, text_color, outline_color, x, y, self.screen)


    def show_text(self, text, x, y):
        font = pygame.font.Font(None, 36)
        text_surface = font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(x, y))
        self.screen.blit(text_surface, text_rect)


# Bird
class Bird:
    GRAVITY = 0.25
    JUMP_FORCE = -5

    def __init__(self, screen_height):
        self.image = pygame.transform.scale(pygame.image.load('Images/bird1.png').convert_alpha(), (50, 35))
        self.rect = self.image.get_rect(center=(100, screen_height // 2))
        self.movement = 0

        self.collision_rect = pygame.Rect(self.rect.left + 10, self.rect.top + 5, self.rect.width - 20, self.rect.height - 10)

    def move(self):
        self.movement += self.GRAVITY
        self.rect.centery += self.movement

        # Update collision_rect to move with the bird
        self.collision_rect.center = self.rect.center
        self.collision_rect.y = self.rect.y + 5  

    def draw(self, screen):
        screen.blit(self.image, self.rect)
    def jump(self):
        self.movement = self.JUMP_FORCE

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
        return self.top_pipe.colliderect(bird.collision_rect) or self.bottom_pipe.colliderect(bird.collision_rect)


# Game
class FlappyBirdGame:
    SCREEN_WIDTH, SCREEN_HEIGHT = 800, 400
    GAME_SPEED = 90

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

        self.pipes = pygame.sprite.Group()

        self.monkey = Monkey(self.env.screen)
        self.frustration_level = 0  # Default frustration level before input


    def check_all_collisions(self):
        # Check for pipe collisions
        for pipe in self.pipes:
            if pipe.check_collision(self.bird):
                self.frustration_level = self.get_frustration_level()  # Prompt for frustration level - self reporting
                self.game_over_sound.play()
                self.game_active = False
                self.end_time = datetime.now()  
                self.save_score() 
                return  # Exit the method after handling collision

        # Check for floor and ceiling collisions
        if self.bird.rect.top <= 0 or self.bird.rect.bottom >= self.SCREEN_HEIGHT:
            self.frustration_level = self.get_frustration_level()  
            self.game_over_sound.play()
            self.game_active = False
            self.end_time = datetime.now() 
            self.save_score()  
             


    def handle_pipes(self):
        global speed_increase_factor
        # Add new pipes when needed
        if not self.pipes or self.pipes[-1].bottom_pipe.centerx < self.SCREEN_WIDTH - 100:  # Adjust gap for new pipe
            gap_size = random.randint(100, 300)  # Keep gap size consistent for simplicity
            new_pipe = Pipe(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, gap_size)
            self.pipes.append(new_pipe)

        # Move pipes and check for collisions and off-screen pipes
        for pipe in self.pipes[:]:
            pipe.move()

            # Increment score and increase speed when the bird passes a pipe
            if not pipe.score_counted and pipe.bottom_pipe.centerx < self.bird.rect.left:
                self.score += 1
                pipe.score_counted = True
                speed_increase_factor += 0.07  # Slight speed increase for a gradual difficulty ramp

            # Remove off-screen pipes
            if pipe.is_off_screen():
                self.pipes.remove(pipe)

            # Draw pipes
            pipe.draw(self.env.screen)

        # Display updated score
        self.env.show_score(self.score)

    def run(self):
        clock = pygame.time.Clock()
        FPS = 60

        while True:
            clock.tick(FPS)
            current_time = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        if not self.game_start:
                            self.game_start = True
                            self.game_active = True
                            self.reset_game()  # Resets game state and time stamps
                        elif self.game_active:
                            self.bird.jump()
                            self.flap_sound.play()
                        else:
                            self.reset_game()  # Resets game state and time stamps

            self.env.draw_background()
            if self.game_active:
                self.bird.move()
                self.bird.draw(self.env.screen)
                self.check_all_collisions()
                self.handle_pipes()
                self.env.show_score(self.score)

                # End time and score saving moved to check_all_collisions method
            else:
                # If the game is not active and has ended, ensure the end time is recorded once
                if self.end_time is None and self.start_time is not None:
                    self.end_time = datetime.now()
                    self.save_score()  # Save the score only once when the game ends

            self.display_game_status()

            # Monkey logic...
            self.monkey.update(current_time, self.game_active)
            if self.game_active:
                self.monkey.draw()

            pygame.display.update()

            self.clock.tick(self.GAME_SPEED)


        def reset_game(self):
            self.time = time.time()  # Reset the initial time for the new game
            global speed_increase_factor
            speed_increase_factor = 1.0  # Reset speed increase factor
            self.bird = Bird(self.SCREEN_HEIGHT)
            self.pipes = [Pipe(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, random.randint(100, 300))]
            self.score = 0
            self.game_active = True
            self.game_start = True
            self.monkey.reset()
            self.start_time = None
            self.end_time = None
            
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




        def display_game_status(self):
            # Helper function for rendering text with an outline
            def render_text_with_outline(font, text, text_color, outline_color, position):
                outline_width = 2  # Width of the outline in pixels
                text_surface = font.render(text, True, text_color)
                outline_surface = font.render(text, True, outline_color)

                # Render the outline by offsetting the text in all directions
                for dx, dy in [(-outline_width, -outline_width), (-outline_width, outline_width),
                            (outline_width, -outline_width), (outline_width, outline_width),
                            (0, -outline_width), (-outline_width, 0), (0, outline_width), (outline_width, 0)]:
                    self.env.screen.blit(outline_surface, (position[0] + dx, position[1] + dy))

                # Render the main text on top
                self.env.screen.blit(text_surface, position)

            white = self.env.WHITE
            black = (0, 0, 0)  # Outline color

            if self.game_start and not self.game_active:
                start_font = pygame.font.Font(None, 32)
                text = 'Press Space to Start'
                text_surface = start_font.render(text, True, white)
                text_rect = text_surface.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2))
                render_text_with_outline(start_font, text, white, black, text_rect.topleft)

            elif not self.game_start and not self.game_active:
                game_over_font = pygame.font.Font(None, 64)
                restart_font = pygame.font.Font(None, 32)

                # Game Over text
                game_over_text = 'Game Over'
                game_over_surface = game_over_font.render(game_over_text, True, white)
                game_over_rect = game_over_surface.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 3))
                render_text_with_outline(game_over_font, game_over_text, white, black, game_over_rect.topleft)

                # Restart text
                restart_text = 'Press Space to Restart'
                restart_surface = restart_font.render(restart_text, True, white)
                restart_rect = restart_surface.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2))
                render_text_with_outline(restart_font, restart_text, white, black, restart_rect.topleft)

    def reset_game(self):
        # Reset the initial time for the new game
        self.start_time = datetime.now()  # Capture the start time at the beginning of the game
        self.end_time = None  # Ensure end time is cleared for the new game session
        
        global speed_increase_factor
        speed_increase_factor = 1.0  # Reset speed increase factor
        
        self.bird = Bird(self.SCREEN_HEIGHT)
        self.pipes = [Pipe(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, random.randint(100, 300))]
        self.score = 0
    
        self.game_active = True
        self.game_start = True
        self.monkey.reset()

    def save_score(self):
        filename = 'scores.csv'
        fieldnames = ['name', 'score', 'start_time', 'end_time', 'duration', 'frustration_level']  # Include 'frustration_level'

        with open(filename, 'a+', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if csvfile.tell() == 0:
                writer.writeheader()

            writer.writerow({
                'name': self.player_name,
                'score': self.score,
                'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': self.end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'duration': round((self.end_time - self.start_time).total_seconds(), 2),
                'frustration_level': self.frustration_level  # Save frustration level
            })

    
    
    
    def display_game_status(self):
        # Helper function for rendering text with an outline
        def render_text_with_outline(font, text, text_color, outline_color, position):
            outline_width = 2  # Width of the outline in pixels
            text_surface = font.render(text, True, text_color)
            outline_surface = font.render(text, True, outline_color)

            # Render the outline by offsetting the text in all directions
            for dx, dy in [(-outline_width, -outline_width), (-outline_width, outline_width),
                        (outline_width, -outline_width), (outline_width, outline_width),
                        (0, -outline_width), (-outline_width, 0), (0, outline_width), (outline_width, 0)]:
                self.env.screen.blit(outline_surface, (position[0] + dx, position[1] + dy))

            # Render the main text on top
            self.env.screen.blit(text_surface, position)

        white = self.env.WHITE
        black = (0, 0, 0)  # Outline color

        if self.game_start and not self.game_active:
            start_font = pygame.font.Font(None, 32)
            text = 'Press Space to Start'
            text_surface = start_font.render(text, True, white)
            text_rect = text_surface.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2))
            render_text_with_outline(start_font, text, white, black, text_rect.topleft)

        elif not self.game_start and not self.game_active:
            game_over_font = pygame.font.Font(None, 64)
            restart_font = pygame.font.Font(None, 32)

            # Game Over text
            game_over_text = 'Game Over'
            game_over_surface = game_over_font.render(game_over_text, True, white)
            game_over_rect = game_over_surface.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 3))
            render_text_with_outline(game_over_font, game_over_text, white, black, game_over_rect.topleft)

            # Restart text
            restart_text = 'Press Space to Restart'
            restart_surface = restart_font.render(restart_text, True, white)
            restart_rect = restart_surface.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2))
            render_text_with_outline(restart_font, restart_text, white, black, restart_rect.topleft)

    def get_frustration_level(self):
        # Assuming the screen, font, and other necessary elements are accessible here
        screen = self.env.screen  # Reference to your Pygame screen
        font = pygame.font.Font(None, 36)  # Adjust font size as needed
        text_color = self.env.WHITE
        outline_color = (0, 0, 0)  # Black outline
        message = "Press 1, 2, or 3 to rate your frustration level"

        # Clear the screen or ensure the message is displayed on top of the current screen content
        self.env.draw_background()  # Optional: Redraw background or current game state if needed

        # Display the prompt message with outline
        # Since render_text_with_outline is a standalone function, call it directly
        # Adjust x, y coordinates as necessary to position the text appropriately
        x = self.env.screen_width // 2
        y = self.env.screen_height // 2
        # Adjust the x, y to center the text, as render_text_with_outline might not automatically center the text based on the provided coordinates
        render_text_with_outline(font, message, text_color, outline_color, x - font.size(message)[0] // 2, y, screen)

        pygame.display.update()  # Make sure to update the display to show the prompt

        frustration_level = 0
        waiting_for_input = True
        while waiting_for_input:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        frustration_level = 1
                        waiting_for_input = False
                    elif event.key == pygame.K_2:
                        frustration_level = 2
                        waiting_for_input = False
                    elif event.key == pygame.K_3:
                        frustration_level = 3
                        waiting_for_input = False

        return frustration_level





class Monkey:
    def __init__(self, screen, image_path='Images/monkey1.png', sound_path='Sounds/MonkeyNoise.mp3'):
        self.screen = screen
        self.original_image = pygame.image.load(image_path).convert_alpha()
        self.sound = pygame.mixer.Sound(sound_path)  # Load the sound
        self.reset()
        self.start_size = (50, 50)  # Starting size
        self.image = pygame.transform.scale(self.original_image, self.start_size)  # Start scaled
        self.rect = self.image.get_rect()

    def reset(self):
        self.visible = False
        self.last_appeared = pygame.time.get_ticks()
        self.initial_delay = 6000  # Delay the first appearance
        self.size_factor = 1.0  # Reset size scaling
        self.growing = True  # Start by growing
        self.velocity = [random.choice([-3, 3]), random.choice([-3, 3])]

    def update(self, current_time, game_active):
        if not game_active:  # Ensure monkey appears only during active gameplay
            self.visible = False
            return

        interval_since_last_appeared = current_time - self.last_appeared
        if self.visible:
            # Scale size within update method
            if self.growing:
                self.size_factor += 0.02
                if self.size_factor >= 4:  # Maximum size scaling factor
                    self.growing = False
            else:
                self.size_factor -= 0.01
                if self.size_factor <= 1:  # Return to starting size
                    self.growing = True

            new_size = (int(self.start_size[0] * self.size_factor), int(self.start_size[1] * self.size_factor))
            self.image = pygame.transform.scale(self.original_image, new_size)
            center = self.rect.center  # Preserve center
            self.rect = self.image.get_rect(center=center)

            # Update position with size-aware collision
            self.rect.x += self.velocity[0]
            self.rect.y += self.velocity[1]

            # Bounce off the edges with updated size consideration
            if self.rect.left <= 0 or self.rect.right >= self.screen.get_width():
                self.velocity[0] = -self.velocity[0]
            if self.rect.top <= 0 or self.rect.bottom >= self.screen.get_height():
                self.velocity[1] = -self.velocity[1]

        # Control visibility of monke based on game state and timing
        if not self.visible and interval_since_last_appeared > self.initial_delay and \
           interval_since_last_appeared > np.random.normal(10000, 3000):
            self.visible = True
            self.last_appeared = current_time
            self.sound.play()  # Play sound when the monkey appears
            # Reset size and position
            self.size_factor = 1.0
            self.image = pygame.transform.scale(self.original_image, self.start_size)
            self.rect = self.image.get_rect(center=(random.randint(0, self.screen.get_width()), random.randint(0, self.screen.get_height())))
        elif self.visible and interval_since_last_appeared > 7000:  # Visible for 7 seconds
            self.visible = False
            self.last_appeared = current_time

    def draw(self):
        if self.visible:
            self.screen.blit(self.image, self.rect)


def run_the_game():
    game = FlappyBirdGame()
    game.run()


run_the_game()

