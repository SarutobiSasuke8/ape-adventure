"""Tunable constants. Single source of truth for physics, screen, and timing values."""

# --- Display ---
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 540
WINDOW_TITLE = "Ape Adventure"
FPS = 60

# --- World / tiles ---
TILE_SIZE = 32
GRAVITY = 1500.0
TERMINAL_VELOCITY = 1000.0

# --- Player (Bongo) ---
PLAYER_WALK_SPEED = 140.0
PLAYER_RUN_SPEED = 240.0
PLAYER_JUMP_IMPULSE = -520.0
PLAYER_VARIABLE_JUMP_FACTOR = 0.30
PLAYER_COYOTE_TIME = 0.10
PLAYER_JUMP_BUFFER = 0.12
PLAYER_ROLL_SPEED = 320.0
PLAYER_ROLL_DURATION = 0.4
PLAYER_ROLL_BUFFER = 0.12      # a roll pressed this early still fires on contact
PLAYER_INVULN_AFTER_HIT = 1.2
PLAYER_MAX_HEALTH = 2
PLAYER_STAND_HEIGHT = 44
PLAYER_CROUCH_HEIGHT = 24     # hitbox while rolling / crawling (fits one-tile gaps)
PLAYER_CRAWL_SPEED = 110.0    # moving under a low ceiling after a roll ends

# --- Vine swing ---
VINE_PUMP_ACCEL = 520.0       # tangential px/s^2 from holding left/right
VINE_DAMPING = 0.12           # fraction of angular speed lost per second
VINE_MAX_ANGLE = 1.30         # radians from vertical
VINE_RELEASE_BOOST = -300.0   # extra upward velocity when jumping off
VINE_REGRAB_COOLDOWN = 0.35   # seconds before the same vine can be grabbed again
VINE_GRIP_OFFSET = 8          # grip point: px below the top of the player

# --- Camera ---
CAMERA_LOOKAHEAD = 80.0
CAMERA_LERP = 6.0

# --- Audio ---
MUSIC_VOLUME = 0.6
SFX_VOLUME = 0.85
DUCK_FACTOR = 0.5
