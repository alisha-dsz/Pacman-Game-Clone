import pygame, sys, random
import math

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# --- Constants ---
CELL_SIZE = 24
ROWS, COLS = 31, 28
WIDTH, HEIGHT = COLS * CELL_SIZE, ROWS * CELL_SIZE + 40
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pac-Man Clone - Cyberpunk Edition")
CLOCK = pygame.time.Clock()
FONT = pygame.font.SysFont("Inter", 24)

# Colors
BLACK = (10, 10, 20)
NEON_PINK = (255, 20, 147)
HOT_PINK = (255, 0, 128)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
RED = (255, 80, 80)
PINK = (255, 105, 180)
CYAN = (0, 255, 255)
ORANGE = (255, 184, 82)
SCARED_GHOST_COLOR = (30, 30, 255)
EATEN_GHOST_EYES_COLOR = (200, 200, 200)
MAZE_COLOR = HOT_PINK
PACMAN_COLOR = YELLOW

# Game States
GAME_STATE_START = 0
GAME_STATE_PLAYING = 1
GAME_STATE_GAME_OVER = 2
GAME_STATE_LEVEL_COMPLETE = 3

# Directions
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
DIRECTIONS = [UP, DOWN, LEFT, RIGHT]

# Maze layout from classic Pac-Man (0=path, 1=wall, 2=pellet, 3=power pellet)
original_layout = [
    "1111111111111111111111111111",
    "1222222222222112222222222221",
    "1211112111112112111112111121",
    "1310012100012112100012100131",
    "1211112111112112111112111121",
    "1222222222222222222222222221",
    "1211112121111111111212111121",
    "1222222122222112222212222221",
    "1111112122222112222212111111",
    "0000012111112112111112100000",
    "0000012122222222222212100000",
    "0000012120000000000212100000",
    "1111112120111001110212111111",
    "0000002000100000010002000000",
    "0000002000000000000002000000",
    "1111112120100000010212111111",
    "0000012120111001110212100000",
    "0000012120000000000212100000",
    "0000012122222222222212100000",
    "1111112121111111111212111111",
    "1222222222222112222222222221",
    "1211112222222112222222111121",
    "1322212111112112111112122231",
    "1111212222222222222222121111",
    "1111212121111111111212121111",
    "1222212122222112222212122221",
    "1222222122222112222212222221",
    "1211111111112112111111111121",
    "1222222222222222222222222221",
    "11111111111111111111111111111",
]

# Ghost spawn points and scatter targets
GHOST_HOUSE_CENTER = (14, 13)
BLINKY_SPAWN = (11, 13)
PINKY_SPAWN = (14, 13)
INKY_SPAWN = (14, 11)
CLYDE_SPAWN = (14, 15)

BLINKY_SCATTER = (1, 23)
PINKY_SCATTER = (1, 6)
INKY_SCATTER = (30, 25)
CLYDE_SCATTER = (30, 3)

# --- Helper Functions ---
def get_grid_coords(pixel_x, pixel_y):
    """Converts pixel coordinates to grid coordinates."""
    return int(pixel_y // CELL_SIZE), int(pixel_x // CELL_SIZE)

def get_pixel_coords(row, col):
    """Converts grid coordinates to pixel coordinates (center of cell)."""
    return col * CELL_SIZE + CELL_SIZE // 2, row * CELL_SIZE + CELL_SIZE // 2

def add_vectors(v1, v2):
    """Adds two 2D vectors."""
    return (v1[0] + v2[0], v1[1] + v2[1])

def manhattan_distance(pos1, pos2):
    """Calculates Manhattan distance between two grid positions."""
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

# --- Game Classes ---
class Entity:
    def __init__(self, start_pos, speed=1):
        self.grid_pos = list(start_pos)
        self.pixel_pos = list(get_pixel_coords(*start_pos))
        self.direction = (0, 0)
        self.speed = speed

    def set_direction(self, dr, dc):
        self.direction = (dr, dc)

    def can_move(self, target_grid_pos, maze_map):
        r, c = target_grid_pos
        return 0 <= r < ROWS and 0 <= c < COLS and maze_map[r][c] != 1

    def update_position(self, maze_map):
        target_pixel_x = self.grid_pos[1] * CELL_SIZE + CELL_SIZE // 2
        target_pixel_y = self.grid_pos[0] * CELL_SIZE + CELL_SIZE // 2

        if self.pixel_pos[0] != target_pixel_x:
            if self.pixel_pos[0] < target_pixel_x:
                self.pixel_pos[0] = min(self.pixel_pos[0] + self.speed * CELL_SIZE, target_pixel_x)
            else:
                self.pixel_pos[0] = max(self.pixel_pos[0] - self.speed * CELL_SIZE, target_pixel_x)
        if self.pixel_pos[1] != target_pixel_y:
            if self.pixel_pos[1] < target_pixel_y:
                self.pixel_pos[1] = min(self.pixel_pos[1] + self.speed * CELL_SIZE, target_pixel_y)
            else:
                self.pixel_pos[1] = max(self.pixel_pos[1] - self.speed * CELL_SIZE, target_pixel_y)

        if self.pixel_pos[0] == target_pixel_x and self.pixel_pos[1] == target_pixel_y:
            next_grid_r, next_grid_c = self.grid_pos[0] + self.direction[1], self.grid_pos[1] + self.direction[0]
            if self.can_move((next_grid_r, next_grid_c), maze_map):
                self.grid_pos = [next_grid_r, next_grid_c]
            else:
                self.direction = (0, 0)

class PacMan(Entity):
    def __init__(self, start_pos):
        super().__init__(start_pos, speed=0.1)
        self.mouth_open = True
        self.mouth_timer = 0
        self.mouth_delay = 50
        self.queued_direction = (0, 0)

    def set_queued_direction(self, dr, dc):
        self.queued_direction = (dr, dc)

    def update(self, maze_map, dt):
        self.handle_teleportation()

        if self.queued_direction != (0, 0):
            target_r, target_c = self.grid_pos[0] + self.queued_direction[1], self.grid_pos[1] + self.queued_direction[0]
            if self.can_move((target_r, target_c), maze_map):
                self.set_direction(*self.queued_direction)
                self.queued_direction = (0,0)
        
        if self.direction == (0,0) and self.queued_direction != (0,0):
             target_r, target_c = self.grid_pos[0] + self.queued_direction[1], self.grid_pos[1] + self.queued_direction[0]
             if self.can_move((target_r, target_c), maze_map):
                self.set_direction(*self.queued_direction)
                self.queued_direction = (0,0)

        self.mouth_timer += dt
        if self.mouth_timer >= self.mouth_delay:
            self.mouth_open = not self.mouth_open
            self.mouth_timer = 0
        
        super().update_position(maze_map)

    def handle_teleportation(self):
        if self.grid_pos[1] == 0 and self.direction == LEFT:
            self.grid_pos[1] = COLS - 1
            self.pixel_pos = list(get_pixel_coords(*self.grid_pos))
        elif self.grid_pos[1] == COLS - 1 and self.direction == RIGHT:
            self.grid_pos[1] = 0
            self.pixel_pos = list(get_pixel_coords(*self.grid_pos))

    def draw(self, surface):
        x, y = self.pixel_pos
        radius = CELL_SIZE // 2 - 2
        pygame.draw.circle(surface, YELLOW, (x, y), radius)

        if self.mouth_open and self.direction != (0, 0):
            mouth_half_angle = math.radians(30)
            center_angle = 0
            if self.direction == UP: center_angle = math.radians(90)
            elif self.direction == LEFT: center_angle = math.radians(180)
            elif self.direction == DOWN: center_angle = math.radians(270)
            
            p1_angle = center_angle - mouth_half_angle
            p2_angle = center_angle + mouth_half_angle
            
            p1 = (x + radius * math.cos(p1_angle), y + radius * math.sin(p1_angle))
            p2 = (x + radius * math.cos(p2_angle), y + radius * math.sin(p2_angle))
            mouth_points = [(x, y), p1, p2]
            pygame.draw.polygon(surface, BLACK, mouth_points)

class Ghost(Entity):
    def __init__(self, start_pos, color, ghost_type, scatter_target):
        super().__init__(start_pos, speed=0.1)
        self.original_color = color
        self.color = color
        self.ghost_type = ghost_type
        self.frightened = False
        self.eaten = False
        self.scatter_target = scatter_target
        self.spawn_pos = start_pos
        self.modes = ['scatter', 'chase']
        self.current_mode = 'scatter'
        self.mode_timer = 0
        self.mode_duration_scatter = 7000
        self.mode_duration_chase = 20000

    def set_frightened(self, value):
        self.frightened = value
        if value:
            self.color = SCARED_GHOST_COLOR
            self.speed = 0.05
        else:
            self.color = self.original_color
            self.speed = 0.1

    def set_eaten(self, value):
        self.eaten = value
        if value:
            self.color = BLACK
            self.speed = 0.2
            self.frightened = False

    def get_target_tile(self, pac_man_pos, pac_man_dir, blinky_pos=None):
        pr, pc = pac_man_pos
        pdr, pdc = pac_man_dir

        if self.eaten: return GHOST_HOUSE_CENTER
        if self.frightened: return self.grid_pos
        if self.current_mode == 'scatter': return self.scatter_target

        if self.ghost_type == 'blinky': return (pr, pc)
        elif self.ghost_type == 'pinky':
            if pac_man_dir == UP: return (pr + 4 * pdr, pc + 4 * pdc - 4)
            else: return (pr + 4 * pdr, pc + 4 * pdc)
        elif self.ghost_type == 'inky':
            if blinky_pos is None: return (pr, pc)
            target_tile_pac = (pr + 2 * pdr, pc + 2 * pdc)
            vector_x = target_tile_pac[1] - blinky_pos[1]
            vector_y = target_tile_pac[0] - blinky_pos[0]
            return (blinky_pos[0] + 2 * vector_y, blinky_pos[1] + 2 * vector_x)
        elif self.ghost_type == 'clyde':
            if manhattan_distance(self.grid_pos, (pr, pc)) < 8:
                return self.scatter_target
            else:
                return (pr, pc)
        return (pr, pc)

    def update(self, maze_map, pac_man_pos, pac_man_dir, blinky_pos, dt):
        self.mode_timer += dt

        if not self.frightened and not self.eaten:
            if self.current_mode == 'scatter' and self.mode_timer >= self.mode_duration_scatter:
                self.current_mode = 'chase'
                self.mode_timer = 0
            elif self.current_mode == 'chase' and self.mode_timer >= self.mode_duration_chase:
                self.current_mode = 'scatter'
                self.mode_timer = 0
        
        if self.eaten and self.grid_pos == list(self.spawn_pos):
            self.set_eaten(False)
            self.color = self.original_color
            self.speed = 0.1
            self.current_mode = 'scatter'
            self.mode_timer = 0

        target_tile = self.get_target_tile(pac_man_pos, pac_man_dir, blinky_pos)
        
        best_direction = self.direction
        min_dist = float('inf')
        opposite_dir = (-self.direction[0], -self.direction[1])
        possible_dirs = DIRECTIONS[:]
        if self.frightened or self.eaten: random.shuffle(possible_dirs)
        
        for dr, dc in possible_dirs:
            if (dr, dc) == opposite_dir and self.direction != (0,0) and not self.frightened and not self.eaten:
                num_valid_moves = 0
                for temp_dr, temp_dc in DIRECTIONS:
                    if self.can_move((self.grid_pos[0] + temp_dc, self.grid_pos[1] + temp_dr), maze_map):
                        num_valid_moves += 1
                if num_valid_moves > 1: continue

            next_r, next_c = self.grid_pos[0] + dc, self.grid_pos[1] + dr
            if self.can_move((next_r, next_c), maze_map):
                dist = manhattan_distance((next_r, next_c), target_tile)
                if dist < min_dist:
                    min_dist = dist
                    best_direction = (dr, dc)

        if best_direction != (0,0): self.set_direction(*best_direction)
        super().update_position(maze_map)

    def draw(self, surface):
        x, y = self.pixel_pos
        radius = CELL_SIZE // 2 - 2
        if self.eaten:
            eye_radius = 4
            pygame.draw.circle(surface, WHITE, (x - radius // 2, y - radius // 4), eye_radius)
            pygame.draw.circle(surface, WHITE, (x + radius // 2, y - radius // 4), eye_radius)
            pygame.draw.circle(surface, BLACK, (x - radius // 2 + self.direction[0]*2, y - radius // 4 + self.direction[1]*2), eye_radius // 2)
            pygame.draw.circle(surface, BLACK, (x + radius // 2 + self.direction[0]*2, y - radius // 4 + self.direction[1]*2), eye_radius // 2)
        else:
            pygame.draw.circle(surface, self.color, (x, y - radius // 4), radius)
            pygame.draw.rect(surface, self.color, (x - radius, y - radius // 4, radius * 2, radius + radius // 4))
            leg_count = 4
            leg_width = (radius * 2) / leg_count
            for i in range(leg_count):
                pygame.draw.circle(surface, self.color, (x - radius + (i * leg_width) + leg_width // 2, y + radius + 2), leg_width // 2 + 1)
            eye_radius = 4
            pygame.draw.circle(surface, WHITE, (x - radius // 2, y - radius // 4), eye_radius)
            pygame.draw.circle(surface, WHITE, (x + radius // 2, y - radius // 4), eye_radius)
            pupil_offset_x = self.direction[0] * 2
            pupil_offset_y = self.direction[1] * 2
            pygame.draw.circle(surface, BLACK, (x - radius // 2 + pupil_offset_x, y - radius // 4 + pupil_offset_y), eye_radius // 2)
            pygame.draw.circle(surface, BLACK, (x + radius // 2 + pupil_offset_x, y - radius // 4 + pupil_offset_y), eye_radius // 2)

class Game:
    def __init__(self):
        self.game_state = GAME_STATE_START
        self.load_sounds()
        self.play_startup_sound()
        self.reset_game()
        

    def reset_game(self):
        self.maze_map = []
        self.pellets = set()
        self.power_pellets = set()
        self.parse_maze_layout()

        self.pac_man = PacMan((21, 10))
        self.blinky = Ghost(BLINKY_SPAWN, RED, 'blinky', BLINKY_SCATTER)
        self.pinky = Ghost(PINKY_SPAWN, PINK, 'pinky', PINKY_SCATTER)
        self.inky = Ghost(INKY_SPAWN, CYAN, 'inky', INKY_SCATTER)
        self.clyde = Ghost(CLYDE_SPAWN, ORANGE, 'clyde', CLYDE_SCATTER)
        self.ghosts = [self.blinky, self.pinky, self.inky, self.clyde]

        self.score = 0
        self.lives = 3
        self.fright_mode = False
        self.fright_timer = 0
        self.fright_duration = 7000

        self.game_over_message = ""
        self.level_complete_message = ""

    def load_sounds(self):
        try:
            self.startup_sound = pygame.mixer.Sound("startup_sound.mp3")
            self.pellet_sound = pygame.mixer.Sound("pellet_sound.mp3")
            self.power_pellet_sound = pygame.mixer.Sound("power_pellet_sound.mp3")
            self.death_sound = pygame.mixer.Sound("death_sound.mp3")
        except pygame.error as e:
            print(f"Warning: Could not load sound file. Make sure sound files are in the same directory. Error: {e}")
            self.startup_sound = None
            self.pellet_sound = None
            self.power_pellet_sound = None
            self.death_sound = None

    def play_startup_sound(self):
        if self.startup_sound:
            self.startup_sound.play()

    def parse_maze_layout(self):
        self.maze_map = []
        self.pellets.clear()
        self.power_pellets.clear()
        for r, row_str in enumerate(original_layout):
            row_list = []
            for c, char in enumerate(row_str):
                if char == '1': row_list.append(1)
                elif char == '2':
                    row_list.append(0)
                    self.pellets.add((r, c))
                elif char == '3':
                    row_list.append(0)
                    self.power_pellets.add((r, c))
                else: row_list.append(0)
            self.maze_map.append(row_list)

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP: self.pac_man.set_queued_direction(0, -1)
            elif event.key == pygame.K_DOWN: self.pac_man.set_queued_direction(0, 1)
            elif event.key == pygame.K_LEFT: self.pac_man.set_queued_direction(-1, 0)
            elif event.key == pygame.K_RIGHT: self.pac_man.set_queued_direction(1, 0)
            elif event.key == pygame.K_RETURN and self.game_state != GAME_STATE_PLAYING:
                self.reset_game()
                self.game_state = GAME_STATE_PLAYING

    def update(self, dt):
        if self.game_state != GAME_STATE_PLAYING:
            return

        self.pac_man.update(self.maze_map, dt)
        pac_r, pac_c = self.pac_man.grid_pos

        if (pac_r, pac_c) in self.pellets:
            try: self.pellets.remove((pac_r, pac_c))
            except KeyError: pass
            self.score += 10
            if self.pellet_sound: self.pellet_sound.play()

        if (pac_r, pac_c) in self.power_pellets:
            try: self.power_pellets.remove((pac_r, pac_c))
            except KeyError: pass
            self.score += 50
            self.activate_fright_mode()
            if self.power_pellet_sound: self.power_pellet_sound.play()

        if self.fright_mode:
            self.fright_timer -= dt
            if self.fright_timer <= 0: self.deactivate_fright_mode()

        blinky_pos = self.blinky.grid_pos
        for ghost in self.ghosts:
            ghost.update(self.maze_map, self.pac_man.grid_pos, self.pac_man.direction, blinky_pos, dt)
            if manhattan_distance(ghost.grid_pos, self.pac_man.grid_pos) < 1.5:
                if ghost.frightened and not ghost.eaten:
                    self.score += 200
                    ghost.set_eaten(True)
                    ghost.grid_pos = list(ghost.spawn_pos)
                    ghost.pixel_pos = list(get_pixel_coords(*ghost.spawn_pos))
                    ghost.direction = (0, 0)
                elif not ghost.frightened and not ghost.eaten:
                    self.lives -= 1
                    if self.death_sound: self.death_sound.play()
                    self.reset_entities_position()
                    if self.lives == 0:
                        self.game_state = GAME_STATE_GAME_OVER
                        self.game_over_message = "GAME OVER!"
                    break

        if not self.pellets and not self.power_pellets:
            self.game_state = GAME_STATE_LEVEL_COMPLETE
            self.level_complete_message = "LEVEL COMPLETE!"

    def activate_fright_mode(self):
        self.fright_mode = True
        self.fright_timer = self.fright_duration
        for ghost in self.ghosts:
            if not ghost.eaten:
                ghost.set_frightened(True)
                ghost.direction = (-ghost.direction[0], -ghost.direction[1])

    def deactivate_fright_mode(self):
        self.fright_mode = False
        for ghost in self.ghosts:
            if not ghost.eaten:
                ghost.set_frightened(False)

    def reset_entities_position(self):
        self.pac_man.grid_pos = [21, 10]
        self.pac_man.pixel_pos = list(get_pixel_coords(21, 10))
        self.pac_man.direction = (0, 0)
        self.pac_man.queued_direction = (0,0)

        for ghost in self.ghosts:
            ghost.grid_pos = list(ghost.spawn_pos)
            ghost.pixel_pos = list(get_pixel_coords(*ghost.spawn_pos))
            ghost.direction = random.choice(DIRECTIONS)
            ghost.set_frightened(False)
            ghost.set_eaten(False)
            ghost.current_mode = 'scatter'
            ghost.mode_timer = 0

    def draw(self, surface):
        surface.fill(BLACK)
        for r, row in enumerate(self.maze_map):
            for c, val in enumerate(row):
                if val == 1:
                    rect = pygame.Rect(c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    pygame.draw.rect(surface, MAZE_COLOR, rect, border_radius=3)
        for r, c in self.pellets:
            pygame.draw.circle(surface, WHITE, (c * CELL_SIZE + CELL_SIZE // 2, r * CELL_SIZE + CELL_SIZE // 2), 3)
        for r, c in self.power_pellets:
            pygame.draw.circle(surface, WHITE, (c * CELL_SIZE + CELL_SIZE // 2, r * CELL_SIZE + CELL_SIZE // 2), 6)
        self.pac_man.draw(surface)
        for ghost in self.ghosts:
            ghost.draw(surface)

        score_txt = FONT.render(f"Score: {self.score}", True, WHITE)
        lives_txt = FONT.render(f"Lives: {self.lives}", True, WHITE)
        surface.blit(score_txt, (10, ROWS * CELL_SIZE + 5))
        surface.blit(lives_txt, (WIDTH - lives_txt.get_width() - 10, ROWS * CELL_SIZE + 5))

        if self.game_state == GAME_STATE_START:
            start_txt = FONT.render("Press ENTER to Start", True, WHITE)
            start_rect = start_txt.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            surface.blit(start_txt, start_rect)
        elif self.game_state == GAME_STATE_GAME_OVER:
            game_over_txt = FONT.render(self.game_over_message + " Press ENTER to Restart", True, WHITE)
            game_over_rect = game_over_txt.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            surface.blit(game_over_txt, game_over_rect)
        elif self.game_state == GAME_STATE_LEVEL_COMPLETE:
            level_complete_txt = FONT.render(self.level_complete_message + " Press ENTER to Play Again", True, WHITE)
            level_complete_rect = level_complete_txt.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            surface.blit(level_complete_txt, level_complete_rect)

        pygame.display.flip()

# --- Main Game Loop ---
if __name__ == "__main__":
    game = Game()
    running = True
    while running:
        dt = CLOCK.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            game.handle_input(event)
        game.update(dt)
        game.draw(SCREEN)

    pygame.quit()
    sys.exit()
