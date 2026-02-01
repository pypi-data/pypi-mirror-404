import pygame, pyglet, arcade
import time, os, math

_FONT_CACHE = {}

#* This function you can use to get cached fonts but it was created for internal use mainly
def get_font(name, size):
    key = (name, size)
    if key not in _FONT_CACHE:
        try:
            _FONT_CACHE[key] = pygame.font.SysFont(name, size)
        except:
            _FONT_CACHE[key] = pygame.font.SysFont("Arial", size)
    return _FONT_CACHE[key]

class PygameEasyDraw:
    @staticmethod
    def star(surface, color, center, size, points=5, corner_rounding=0):
        if not isinstance(surface, pygame.Surface):
            raise TypeError(f"surface must be a pygame.Surface, not {type(surface).__name__}")
        
        if not isinstance(color, (tuple, list, pygame.Color)):
            raise TypeError(f"color must be a tuple, list, or pygame.Color, not {type(color).__name__}")
            
        if not isinstance(center, (tuple, list, pygame.math.Vector2)):
            raise TypeError(f"center must be a sequence of 2 coordinates, not {type(center).__name__}")

        if not isinstance(size, (int, float)):
            raise TypeError(f"size must be a number, not {type(size).__name__}")

        if not isinstance(points, int):
            raise TypeError(f"points must be an integer, not {type(points).__name__}")

        if not isinstance(corner_rounding, (int, float)):
            raise TypeError(f"corner_rounding must be a number, not {type(corner_rounding).__name__}")

        if not (3 <= len(color) <= 4):  # RGB or RGBA
            raise ValueError(f"Color must have 3 or 4 values (RGB/A), got {len(color)}")

        for val in color:
            if not (0 <= val <= 255):
                raise ValueError(f"Color values must be between 0 and 255, got {val}")
        
        if len(center) != 2:
            raise ValueError(f"Center must be a pair of (x, y) coordinates, got {len(center)} values")

        if size <= 0:
            raise ValueError(f"size must be greater than 0, got {size}")

        if points < 2:
            raise ValueError(f"points must be at least 2 to form a star, got {points}")

        inner_radius = size / 2.5
        outer_radius = size
        point_list = []
        
        for i in range(points * 2):
            radius = float(outer_radius) if i % 2 == 0 else float(inner_radius)
            angle = math.radians(i * (360 / (points * 2)))
            
            x = center[0] + radius * math.cos(angle)
            y = center[1] + radius * math.sin(angle)
            point_list.append((x, y))

        if corner_rounding <= 0:
            return pygame.draw.polygon(surface, color, point_list)
        else:
            return pygame.draw.polygon(surface, color, point_list, width=0)

#* This will change the way your sprite or sprite group spins
def change_axis(sprite, angle, pivot_offset):
    if not isinstance(sprite, (pygame.sprite.Sprite, pygame.sprite.Group)):
        raise TypeError(f"Sprite must be a pygame Sprite or Group, not{type(sprite).__name__}")
    if not isinstance(angle, (int, float)):
        raise TypeError(f"angle must be a number, not {type(angle).__name__}")
    if not isinstance(pivot_offset, (int, float)):
        raise TypeError(f"pivot_offset must be a number, not {type(pivot_offset).__name__}")

    rotated_image = pygame.transform.rotate(sprite.image, angle)
    
    offset_rotated = pygame.math.Vector2(pivot_offset).rotate(-angle)
    
    sprite.image = rotated_image
    sprite.rect = rotated_image.get_rect(center=sprite.pos.to_pygame() + offset_rotated)

class PygameClickedCalculator(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()

    """this function calculates if the sprite was clicked or not"""
    def clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if hasattr(self, 'rect') and self.rect.collidepoint(event.pos):
                return True
        return False

    """this function changes the cursor to a hand when hovering over the sprite"""
    def handle_cursor(self):
        mouse_pos = pygame.mouse.get_pos()
        if hasattr(self, 'rect') and self.rect.collidepoint(mouse_pos):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            return True
        return False

#* A tool you can use to have the camera follow something
class PygameSmartCamera:
    def __init__(self, screen_width, screen_height, lerp_speed=0.1):
        if not isinstance(screen_width, (int, float)):
            raise TypeError(f"screen_width must be a number, not {type(screen_width).__name__}")
        if not isinstance(screen_height, (int, float)):
            raise TypeError(f"screen_height must be a number, not {type(screen_height).__name__}")
        if not isinstance(lerp_speed, (int, float)):
            raise TypeError(f"lerp_speed must be a number, not {type(lerp_speed).__name__}")
        
        self.offset = pygame.Vector2(0, 0)
        self.width = screen_width
        self.height = screen_height
        self.lerp_speed = lerp_speed

    def update(self, target_rect):
        target_center_x = target_rect.centerx - self.width // 2
        target_center_y = target_rect.centery - self.height // 2

        self.offset.x += (target_center_x - self.offset.x) * self.lerp_speed
        self.offset.y += (target_center_y - self.offset.y) * self.lerp_speed

    def apply(self, entity_rect):
        return entity_rect.move(-self.offset.x, -self.offset.y)

#* This will create a visible variable that can contain any type of data ints floats strings etc
class PygameVisibleVariable(PygameClickedCalculator):
    def __init__(self, font, fontsize, fontcolor, x, y, string, background_t_f, backgroundcolor=None):
        if not isinstance(font, str):
            raise TypeError(f"Font name must be a string, not {type(font).__name__}")
        
        if not isinstance(fontsize, (int, float)) or fontsize <= 0:
            raise ValueError(f"Font size must be a positive number, you provided: {fontsize}")
            
        if not isinstance(fontcolor, (tuple, list)) or len(fontcolor) < 3:
             raise TypeError("fontcolor must be an RGB tuple or list (e.g., (255, 255, 255))")

        if not isinstance(background_t_f, bool):
            raise TypeError(f"background_t_f must be True or False, not {type(background_t_f).__name__}")

        if background_t_f and backgroundcolor is None:
            raise ValueError("When background_t_f is True, you must provide a backgroundcolor (e.g., (0,0,255))")
        
        if not background_t_f and backgroundcolor is not None:
            raise ValueError("backgroundcolor should not be provided when background_t_f is False")

        super().__init__()
        self.font_name = font
        self.font_size = int(fontsize)
        self.font_color = fontcolor
        self.background_t_f = background_t_f
        self.background_color = backgroundcolor
        self.x, self.y = x, y
        
        self._current_string = string
        self.refresh_image(string)

    @property
    def value(self):
        """Allows users to get the current value: print(obj.value)"""
        return self._current_string

    @value.setter
    def value(self, new_val):
        """Allows users to update via: obj.value = 100"""
        self._current_string = new_val
        self.refresh_image(new_val)

    def refresh_image(self, new_val):
        font_obj = pygame.font.SysFont(self.font_name, self.font_size)
        string_val = str(new_val)
        
        text_surface = font_obj.render(string_val, True, self.font_color)
        w, h = text_surface.get_size()

        if not self.background_t_f:
            self.image = pygame.Surface((w, h), pygame.SRCALPHA).convert_alpha()
            self.image.blit(text_surface, (0, 0))
        else:
            self.image = pygame.Surface((w + 4, h + 4)).convert()
            self.image.fill(self.background_color)
            self.image.blit(text_surface, (2, 2))
        
        self.rect = self.image.get_rect(topleft=(self.x, self.y))

#* This is basically a group of variables but visible and it will layout them out either vertically or horizontally you dont need to make multiple visible variables for this
class PygameVisibleList(pygame.sprite.Group):
    def __init__(self, font, fontsize, fontcolor, x, y, variablegroup, 
                 vh, v_bg_t_f, v_bg_color=None, 
                 l_bg_t_f=False, l_bg_color=None):
        
        if vh.lower() not in ["vertical", "horizontal"]:
            raise ValueError(f"Layout 'vh' must be 'vertical' or 'horizontal', not '{vh}'")
            
        if not isinstance(variablegroup, (list, tuple)):
            raise TypeError(f"variablegroup must be a list or tuple of data, not {type(variablegroup).__name__}")

        if l_bg_t_f and l_bg_color is None:
             raise ValueError("When l_bg_t_f is True, you must provide a list_background_color")

        super().__init__()
        self.font, self.fontsize, self.fontcolor = font, fontsize, fontcolor
        self.x, self.y = x, y
        self.vh = vh.lower()
        self.v_bg_t_f, self.v_bg_color = v_bg_t_f, v_bg_color
        self.l_bg_t_f, self.l_bg_color = l_bg_t_f, l_bg_color
        self.refresh_list(variablegroup)

    #* This function will do the same as the visible variable but for the whole list
    def refresh_list(self, variablegroup):
        
        if not isinstance(variablegroup, (list, tuple)):
            raise TypeError(f"Expected a list or tuple, not {type(variablegroup).__name__}")
        self.empty()
        curr_x, curr_y = self.x, self.y
        spacing = 10
        for item in variablegroup:
            node = PygameVisibleVariable(self.font, self.fontsize, self.fontcolor, 
                                         curr_x, curr_y, item, self.v_bg_t_f, self.v_bg_color)
            self.add(node)
            if self.vh == "vertical":
                curr_y += node.rect.height + spacing
            else:
                curr_x += node.rect.width + spacing

    #* This function lets you just draw the list
    def draw(self, surface):
        
        if not isinstance(surface, (pygame.Surface)):
            raise TypeError(f"Expected a pygame Surface, not {type(surface).__name__}")
        if self.l_bg_t_f and self.l_bg_color and self.sprites():
            all_rects = [s.rect for s in self.sprites()]
            combined_rect = all_rects[0].unionall(all_rects[1:])
            bg_rect = combined_rect.inflate(15, 15)
            pygame.draw.rect(surface, self.l_bg_color, bg_rect)
        super().draw(surface)

#* Creates a simple health bar for pygame you can use to show health
class PygameHealthBar(pygame.sprite.Sprite):
    def __init__(self, x, y, width_per_1hp, max_health, current_health, bar_height, border_color, health_color):
        super().__init__()
        if width_per_1hp <= 0:
            raise ValueError("width_per_1hp must be a positive number.")
        if max_health <= 0:
            raise ValueError("max_health must be greater than 0.")
        
        if not isinstance(x, (int, float)):
            raise TypeError(f"x must be an int or float, not {type(x).__name__}")
        if not isinstance(y, (int, float)):
            raise TypeError(f"y must be an int or float, not {type(y).__name__}")
        if not isinstance(width_per_1hp, (int, float)):
            raise TypeError(f"width_per_1hp must be an int or float, not {type(width_per_1hp).__name__}")
        if not isinstance(max_health, (int, float)):
            raise TypeError(f"max_health must be an int or float, not {type(max_health).__name__}")
        if not isinstance(current_health, (int, float)):
            raise TypeError(f"current_health must be an int or float, not {type(current_health).__name__}")
        if not isinstance(bar_height, (int, float)):
            raise TypeError(f"bar_height must be an int or float, not {type(bar_height).__name__}")
        if not isinstance(border_color, (list, tuple)):
            raise TypeError(f"border_color must be an list or tuple, not {type(border_color).__name__}")
        if not isinstance(health_color, (list, tuple)):
            raise TypeError(f"health_color must be an list or tuple, not {type(health_color).__name__}")
        
        self.x, self.y = x, y
        self.w_p_1 = width_per_1hp
        self.max_h = max_health
        self.height = bar_height
        self.b_color = border_color
        self.h_color = health_color
        
        self.image = pygame.Surface((max_health * width_per_1hp + 4, bar_height)).convert()
        self.rect = self.image.get_rect(topleft=(x, y))
        
        self.refresh_bar(current_health)

    """Redraws the bar. Only need to pass the new health value!"""
    def refresh_bar(self, current_health):
        if not isinstance(current_health, (int, float)):
            raise TypeError(f"current_health must be an int or float, not {type(current_health).__name__}")
        
        self.image.fill(self.b_color)
        
        
        draw_health = current_health
        if draw_health > self.max_h:
            draw_health = self.max_h
        if draw_health < 0:
            draw_health = 0
            
        pygame.draw.rect(self.image, self.h_color, (2, 2, draw_health * self.w_p_1, self.height - 4))

    def update_hp(self, current_health):
        """The 'Easy' way to change health in your loop."""
        if not isinstance(current_health, (int, float)):
            raise TypeError(f"current_health must be an int or float, not {type(current_health).__name__}")
        self.refresh_bar(current_health)

#* This is a slider that can be dragged left and right to get to get a value you want that will customize something in your game
class PygameDraggableSlider(PygameClickedCalculator):
    def __init__(self, color, startingX, y, min_x, max_x):
        if not isinstance(color, (tuple, list, pygame.Color)):
            raise TypeError(f"color must be a tuple, list, or pygame.Color, not {type(color).__name__}")
        
        for name, val in [("startingX", startingX), ("y", y), ("min_x", min_x), ("max_x", max_x)]:
            if not isinstance(val, (int, float)):
                raise TypeError(f"{name} must be a number (int or float), not {type(val).__name__}")

        if not (3 <= len(color) <= 4):
            raise ValueError(f"color must have 3 (RGB) or 4 (RGBA) values, not {len(color)}")

        for val in color:
            if not isinstance(val, int) or not (0 <= val <= 255):
                raise ValueError(f"color values must be integers between 0 and 255, not {val}")

        if min_x >= max_x:
            raise ValueError(f"min_x ({min_x}) must be strictly less than max_x ({max_x})")
        
        if not (min_x <= startingX <= max_x):
            raise ValueError(f"startingX ({startingX}) must be within the range of min_x and max_x")

        super().__init__()
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA).convert_alpha() 
        pygame.draw.circle(self.image, color, (10, 10), 10)
        
        self.rect = self.image.get_rect(center=(startingX, y))
        self.color = color
        self.dragging = False
        
        self.min_x = min_x
        self.max_x = max_x

    def handle_input(self, event):
        if not isinstance(event, pygame.event.Event):
            raise TypeError(f"handle_input expects a pygame.event.Event, not {type(event).__name__}")

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.rect.collidepoint(event.pos):
                    self.dragging = True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
            
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                new_x = event.pos[0]
                self.rect.centerx = max(self.min_x, min(new_x, self.max_x))

    def get_value(self):
        """Returns the slider position as a float between 0.0 and 1.0"""
        total_range = self.max_x - self.min_x
        if total_range == 0:
            return 0.0
            
        current_pos = self.rect.centerx - self.min_x
        return float(current_pos / total_range)


class PygameScreenShake:
    def __init__(self, seed=None):
        if not isinstance(seed, (int, float)):
            raise TypeError(f"seed must be a number, not {type(seed).__name__}")
        self.s0 = seed or int(time.time() * 1000) & 0xFFFFFFFFFFFFFFFF
        self.s1 = 0xBEA123456789ABCD ^ self.s0
        self.offset = pygame.Vector2(0, 0)
        self.duration = 0
        self.intensity = 0
        self.impact_vec = pygame.Vector2(0, 0)

    def _next_xorshift(self):
        x, y = self.s0, self.s1
        self.s0 = y
        x ^= (x << 23) & 0xFFFFFFFFFFFFFFFF
        self.s1 = (x ^ y ^ (x >> 17) ^ (y >> 26)) & 0xFFFFFFFFFFFFFFFF
        return (self.s1 + y) & 0xFFFFFFFFFFFFFFFF

    def _get_rand_float(self):
        return (self._next_xorshift() / 0xFFFFFFFFFFFFFFFF) * 2 - 1

#* This really is the only neccessary thing if you would like you can figure out how to use the rest but just this command is all you need
    def shake(self, intensity=None, duration=None, impact_pos=None, center_pos=None):
        if intensity is not None:
            self.intensity = intensity
            self.duration = duration
            if impact_pos and center_pos:
                self.impact_vec = (pygame.Vector2(center_pos) - pygame.Vector2(impact_pos))
                if self.impact_vec.length() > 0:
                    self.impact_vec = self.impact_vec.normalize()
            else:
                self.impact_vec = pygame.Vector2(0, 0)

        if self.duration > 0:
            self.duration -= 1
            rand_vec = pygame.Vector2(self._get_rand_float(), self._get_rand_float())
            if self.impact_vec.length() > 0:
                alignment = rand_vec.dot(self.impact_vec)
                self.offset = self.impact_vec * alignment * self.intensity
            else:
                self.offset = rand_vec * self.intensity
        else:
            self.offset = pygame.Vector2(0, 0)
            
        return self.offset

#* A simple text box that only allows strings but will wrap text and gives you a max length for whatever you want it to be
class PygameTextBox(pygame.sprite.Sprite):
    def __init__(self, x, y, width, string, font_name, fontsize, fontcolor, 
                 background_t_f=False, backgroundcolor=None, 
                 typewrite_t_f=False, time_per_char=50):
        if not (2 <= len(fontcolor) <= 4):
            raise ValueError(f"fontcolor must have 2-4 values, got {len(fontcolor)}")
        for val in fontcolor:
            if not (0 <= val <= 255):
                raise ValueError(f"fontcolor values must be 0-255, got {val}")

        if background_t_f and backgroundcolor is not None:
            if not (2 <= len(backgroundcolor) <= 4):
                raise ValueError(f"backgroundcolor must have 2-4 values, got {len(backgroundcolor)}")
            for val in backgroundcolor:
                if not (0 <= val <= 255):
                    raise ValueError(f"backgroundcolor values must be 0-255, got {val}")

        if width <= 0:
            raise ValueError(f"TextBox width must be greater than 0, got {width}")
            
        if time_per_char < 0:
            raise ValueError(f"time_per_char (speed) cannot be negative, got {time_per_char}")
        super().__init__()
        
        if isinstance(x, (list, tuple)):
            raise TypeError(f"EasyCode Error: 'x' must be a number, but you passed a {type(x).__name__}. Check the order of your arguments in PygameDialogueText!")
        elif isinstance(y, (list, tuple)):
            raise TypeError(f"EasyCode Error: 'y' must be a number, but you passed a {type(y).__name__}. Check the order of your arguments in PygameDialogueText!")

        self.x = int(x)
        self.y = int(y)
        self.width = int(width)
        self.full_string = str(string)
        self.font = get_font(font_name, int(fontsize))
        self.color = fontcolor
        self.bg_enabled = background_t_f
        self.bg_color = backgroundcolor
        
        self.typewrite_enabled = typewrite_t_f
        self.ms_per_char = time_per_char
        self.char_index = 0
        self.last_type_time = pygame.time.get_ticks()

        if not self.typewrite_enabled:
            self.char_index = len(self.full_string)
            
        self.refresh_text()

    def update(self):
        """Standard Pygame update to handle typewriter timing."""
        if self.typewrite_enabled and self.char_index < len(self.full_string):
            now = pygame.time.get_ticks()
            if now - self.last_type_time >= self.ms_per_char:
                self.char_index += 1
                self.last_type_time = now
                self.refresh_text()

    def wrap_text(self, text):
        """Splits text into lines that fit within self.width."""
        words = str(text).split(' ')
        lines, current_line = [], []
        for word in words:
            if self.font.size(' '.join(current_line + [word]))[0] <= self.width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        lines.append(' '.join(current_line))
        return lines

    def refresh_text(self):
        """Redraws the surface based on how many characters are revealed."""
        visible_text = self.full_string[:self.char_index]
        lines = self.wrap_text(visible_text)
        
        line_height = self.font.get_linesize()
        total_height = len(lines) * line_height

        if self.bg_enabled:
            self.image = pygame.Surface((self.width + 10, total_height + 10)).convert()
            self.image.fill(self.bg_color)
            padding = 5
        else:
            self.image = pygame.Surface((self.width, total_height), pygame.SRCALPHA).convert_alpha()
            padding = 0

        for i, line in enumerate(lines):
            text_surf = self.font.render(line, True, self.color)
            self.image.blit(text_surf, (padding, padding + (i * line_height)))

        self.rect = self.image.get_rect(topleft=(self.x, self.y))

#* A dialogue tool that when used will take a list of strings turn them into PygameTextBox(s) and has a next string which can be triggered by whatever you want
class PygameDialogueText(pygame.sprite.Group):
    def __init__(self, text_list, x, y, width, font_name, fontsize, fontcolor, 
                 background_t_f=False, backgroundcolor=None, 
                 typewrite_t_f=False, time_per_char=50):
        super().__init__()
        
        self.text_list = text_list
        self.index = 0
        self.x, self.y, self.width = x, y, width
        self.font_name, self.font_size = font_name, fontsize
        self.font_color = fontcolor
        self.bg_t_f, self.bg_color = background_t_f, backgroundcolor
        self.typewrite_t_f, self.time_per_char = typewrite_t_f, time_per_char

        self._update_display()

    def _update_display(self):
        self.empty()
        new_box = PygameTextBox(
            self.x, self.y, self.width, 
            self.text_list[self.index], 
            self.font_name, self.font_size, self.font_color, 
            self.bg_t_f, self.bg_color,
            self.typewrite_t_f, self.time_per_char
        )
        self.add(new_box)

    def next_string(self):
        self.index += 1
        if self.index >= len(self.text_list):
            self.index = 0
        self._update_display()

    def update(self):
        """Passes the update command to the internal TextBox."""
        for sprite in self.sprites():
            sprite.update()

#* These are some built in sounds
class PygameSoundManager:
    def __init__(self):
        if not pygame.mixer.get_init():
            pygame.mixer.pre_init(44100, -16, 2, 512)
            pygame.mixer.init()
        self.sounds = {}
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

    def load(self, name: str, filename: str):
        if filename.startswith("sounds/"):
            clean_name = filename.replace("sounds/", "")
        else:
            clean_name = filename
        
        full_path = os.path.join(self.base_dir, "sounds", clean_name)

    def play(self, name: str):
        if name in self.sounds:
            self.sounds[name].play()

    def is_playing(self):
        return pygame.mixer.get_busy()

    def play_until_done(self, name: str):
        if name in self.sounds:
            if not self.is_playing():
                self.sounds[name].play()

#* This is a bigstring dont worry about what this thing does or actually is just use it as a string except has no limit in characters plus when it comes to short string it saves memory
#! This does not save memory and will be fixed in version 1.4.0
class BigString:
    def __init__(self, initial_text=""):
        self.data = 0
        self.set(str(initial_text))

    def set(self, text):
        byte_data = text.encode('utf-8')
        self.data = int.from_bytes(byte_data, 'big')

    def get(self):
        if self.data == 0: return ""
        byte_length = (self.data.bit_length() + 7) // 8
        return self.data.to_bytes(byte_length, 'big').decode('utf-8')
    
    def __add__(self, other):
        """Allows: bigstr("hi") + " there" """
        return bigstr(self.get() + str(other))

    def __radd__(self, other):
        """Allows: "hello " + bigstr("world") """
        return bigstr(str(other) + self.get())

    def __eq__(self, other):
        """Allows: if my_bigstr == "test": """
        return self.get() == str(other)

    def __len__(self):
        """Allows: len(my_bigstr) """
        return len(self.get())

    def __str__(self):
        """Allows: print(my_bigstr) """
        return self.get()

    def __repr__(self):
        """Shows up as bigstr('text') in the console"""
        return f"bigstr('{self.get()}')"
    
#TODO: Add BigNyblle here in version 1.4.0 so that the bigstring will actually save memory

#* Similar to the bigstring it can hold more number but because it uses bigints and not floats it actually is faster calculations and no limit and perfect accuracy just dont destroy your PC by not adding a limit to accuracy
class BigDecimal:
    def __init__(self, value, scale=0):
        if isinstance(value, str):
            if "." in value:
                parts = value.split(".")
                self.scale = len(parts[1])
                self.value = int(parts[0] + parts[1])
            else:
                self.value = int(value)
                self.scale = 0
        else:
            self.value = int(value)
            self.scale = scale

    def to_float(self):
        return self.value / (10 ** self.scale)

    def _align(self, other):
        if not isinstance(other, BigDecimal):
            other = BigDecimal(str(other))
        
        new_scale = max(self.scale, other.scale)
        v1 = self.value * (10 ** (new_scale - self.scale))
        v2 = other.value * (10 ** (new_scale - other.scale))
        return v1, v2, new_scale

    def __add__(self, other):
        v1, v2, s = self._align(other)
        return BigDecimal(v1 + v2, s)

    def __sub__(self, other):
        v1, v2, s = self._align(other)
        return BigDecimal(v1 - v2, s)

    def __mul__(self, other):
        if not isinstance(other, BigDecimal):
            other = BigDecimal(str(other))
        return BigDecimal(self.value * other.value, self.scale + other.scale)

    def __str__(self):
        s = str(abs(self.value)).zfill(self.scale + 1)
        res = s[:-self.scale] + "." + s[-self.scale:]
        return f"-{res}" if self.value < 0 else res

#* Like the bigdecimal instead of floats and decimals in this vector its bigints and bigdecimals and its for the same reason bigints are better then floats mostly
class BigVectorBase:
    def __init__(self, *args):
        self.components = [
            arg if isinstance(arg, BigDecimal) else bigdec(str(arg)) 
            for arg in args
        ]

    def __add__(self, other):
        if len(self.components) == len(other.components):
            new_comps = [a + b for a, b in zip(self.components, other.components)]
            return self.__class__(*new_comps)
        raise ValueError(f"Cannot add {len(self.components)}D and {len(other.components)}D vectors!")

    def __sub__(self, other):
        if len(self.components) == len(other.components):
            new_comps = [a - b for a, b in zip(self.components, other.components)]
            return self.__class__(*new_comps)
        raise ValueError("Dimension mismatch during subtraction!")

    def __mul__(self, scalar):
        new_comps = [a * scalar for a in self.components]
        return self.__class__(*new_comps)

    def __str__(self):
        coords = ", ".join(str(c) for c in self.components)
        return f"({coords})"

    def __repr__(self):
        return self.__str__()
    
    def to_pygame(self):
        if len(self.components) == 2:
            return pygame.Vector2(self.components[0].to_float(), self.components[1].to_float())
        elif len(self.components) == 3:
            return pygame.Vector3(self.components[0].to_float(), self.components[1].to_float(), self.components[2].to_float())
        return tuple(c.to_float() for c in self.components)

    def to_tuple(self):
        return tuple(c.to_float() for c in self.components)

    def magnitude(self):
        return (self.x * self.x + self.y * self.y)

class BigVector2(BigVectorBase):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.x, self.y = self.components[0], self.components[1]

class BigVector3(BigVectorBase):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.x, self.y, self.z = self.components[0], self.components[1], self.components[2]

class BigVector4(BigVectorBase):
    def __init__(self, x, y, z, w):
        super().__init__(x, y, z, w)
        self.x, self.y, self.z, self.w = self.components[0], self.components[1], self.components[2], self.components[3]

class PygletVisibleVariable(pyglet.text.Label):
    def __init__(self, font, fontsize, fontcolor, x, y, string, background_t_f, backgroundcolor=None):
        if fontsize <= 0:
            raise ValueError(f"fontsize must be greater than 0; received {fontsize}")

        if not (isinstance(fontcolor, (list, tuple)) and len(fontcolor) in (3, 4)):
            raise ValueError("fontcolor must be an RGB (3) or RGBA (4) tuple/list")

        if background_t_f and backgroundcolor is None:
            raise ValueError("backgroundcolor must be provided if background_t_f is True")

        rgba_font = (*fontcolor, 255) if len(fontcolor) == 3 else fontcolor
        
        bg_color = None
        if background_t_f:
            if not (isinstance(backgroundcolor, (list, tuple)) and len(backgroundcolor) in (3, 4)):
                raise ValueError("backgroundcolor must be an RGB (3) or RGBA (4) tuple/list")
            bg_color = (*backgroundcolor, 255) if len(backgroundcolor) == 3 else backgroundcolor
        
        super().__init__(
            str(string), 
            font_name=font, 
            font_size=fontsize, 
            color=rgba_font, 
            x=x, y=y, 
            background_color=bg_color
        )

    def update_value(self, new_value):
        """Helper to update the displayed text."""
        self.text = str(new_value)

class PygletHealthBar:
    def __init__(self, x, y, width_per_hp, max_hp, current_hp, height, border_color, health_color, batch=None):
        if max_hp <= 0:
            raise ValueError(f"max_hp must be greater than 0; received {max_hp}")
        if width_per_hp <= 0:
            raise ValueError(f"width_per_hp must be a positive value; received {width_per_hp}")
        if height <= 4:
            raise ValueError(f"height must be greater than 4 to accommodate the 2px border; received {height}")
        if current_hp < 0 or current_hp > max_hp:
            raise ValueError(f"current_hp ({current_hp}) must be between 0 and max_hp ({max_hp})")

        self.max_hp = max_hp
        self.w_p_hp = width_per_hp
        
        self.bg = pyglet.shapes.Rectangle(
            x, y, max_hp * width_per_hp, height, 
            color=border_color, batch=batch
        )
        
        bar_width = max(0, (current_hp * width_per_hp) - 4)
        self.bar = pyglet.shapes.Rectangle(
            x + 2, y + 2, bar_width, height - 4, 
            color=health_color, batch=batch
        )

    def refresh_bar(self, current_hp):
        safe_hp = max(0, min(current_hp, self.max_hp))
        self.bar.width = max(0, (safe_hp * self.w_p_hp) - 4)

class PygletVisibleList:
    def __init__(self, font, fontsize, fontcolor, x, y, items, vh="vertical", batch=None):
        if vh.lower() not in ("vertical", "horizontal"):
            raise ValueError(f"vh must be 'vertical' or 'horizontal'; received '{vh}'")
        
        if fontsize <= 0:
            raise ValueError(f"fontsize must be a positive value; received {fontsize}")
            
        if not (isinstance(fontcolor, (list, tuple)) and len(fontcolor) in (3, 4)):
            raise ValueError("fontcolor must be an RGB (3) or RGBA (4) tuple/list")

        self.items = []
        self.batch = batch
        self.x, self.y = x, y
        self.font, self.size, self.color = font, fontsize, fontcolor
        self.vh = vh.lower()
        self.refresh_list(items)

    def refresh_list(self, items):
        self.items = []
        curr_x, curr_y = self.x, self.y
        spacing = 10
        
        rgba_color = (*self.color, 255) if len(self.color) == 3 else self.color
        
        for text in items:
            label = pyglet.text.Label(
                str(text), 
                font_name=self.font, 
                font_size=self.size,
                color=rgba_color, 
                x=curr_x, 
                y=curr_y, 
                batch=self.batch
            )
            self.items.append(label)
            
            if self.vh == "vertical":
                curr_y -= (self.size + spacing)
            else:
                curr_x += (len(str(text)) * self.size * 0.6) + spacing


class PygletTextBox:
    def __init__(self, x, y, width, initial_text="", batch=None, window=None):
        if width <= 0:
            raise ValueError(f"width must be greater than 0 to render text layout; received {width}")
        
        if not isinstance(initial_text, str):
            raise ValueError(f"initial_text must be a string; received {type(initial_text).__name__}")

        if window is not None and not isinstance(window, pyglet.window.Window):
            raise ValueError("window must be an instance of pyglet.window.Window or None")

        self.doc = pyglet.text.document.UnformattedDocument(initial_text)
        
        self.layout = pyglet.text.layout.IncrementalTextLayout(
            self.doc, width, height=30, multiline=False, batch=batch
        )
        self.layout.x, self.layout.y = x, y
        
        self.caret = pyglet.text.caret.Caret(self.layout)
        
        if window:
            window.push_handlers(self.caret)

    @property
    def text(self):
        return self.doc.text
    
class PygletDialogueText:
    def __init__(self, text_list, x, y, width, font_name, fontsize, fontcolor, 
                 background_t_f=False, backgroundcolor=None, 
                 typewrite_t_f=True, time_per_char=0.05, batch=None):
        if not text_list or not isinstance(text_list, (list, tuple)):
            raise ValueError("text_list must be a non-empty list or tuple of strings")
        
        if width <= 0:
            raise ValueError(f"width must be a positive value; received {width}")
            
        if fontsize <= 0:
            raise ValueError(f"fontsize must be greater than 0; received {fontsize}")

        if time_per_char <= 0:
            raise ValueError(f"time_per_char must be a positive duration; received {time_per_char}")

        if background_t_f and backgroundcolor is None:
            raise ValueError("backgroundcolor must be provided if background_t_f is True")

        self.text_list = text_list
        self.index = 0
        self.batch = batch
        self.x, self.y, self.width = x, y, width
        self.font, self.size, self.color = font_name, fontsize, fontcolor
        
        self.bg = None
        if background_t_f:
            bg_h = (fontsize * len(text_list[0]) // 10) + 10
            self.bg = pyglet.shapes.Rectangle(x-5, y-5, width+10, bg_h, 
                                             color=backgroundcolor, batch=batch)
            self.bg.opacity = 200

        self.full_text = text_list[self.index]
        self.display_text = ""
        self.char_index = 0
        self.typewrite_enabled = typewrite_t_f
        
        rgba_color = (*fontcolor, 255) if len(fontcolor) == 3 else fontcolor
        self.label = pyglet.text.Label("", font_name=font_name, font_size=fontsize,
                                      color=rgba_color, x=x, y=y, width=width,
                                      multiline=True, batch=batch)

        if self.typewrite_enabled:
            pyglet.clock.schedule_interval(self._update_typewriter, time_per_char)
        else:
            self.label.text = self.full_text

    def _update_typewriter(self, dt):
        if self.char_index < len(self.full_text):
            self.char_index += 1
            self.label.text = self.full_text[:self.char_index]

    def next_string(self):
        self.index = (self.index + 1) % len(self.text_list)
        self.full_text = self.text_list[self.index]
        self.char_index = 0
        if not self.typewrite_enabled:
            self.label.text = self.full_text

class PygletScreenShake(PygameScreenShake):
    def apply_to_window(self, window):
        offset = self.shake()
        window.view = window.view.from_translation((offset.x, offset.y, 0))

from pyglet import shapes

class PygletDraggableSlider:
    def __init__(self, color, starting_x, y, min_x, max_x, batch=None, window=None):
        if max_x <= min_x:
            raise ValueError(f"max_x ({max_x}) must be greater than min_x ({min_x})")
        
        if not (min_x <= starting_x <= max_x):
            raise ValueError(f"starting_x ({starting_x}) must be between {min_x} and {max_x}")

        if not (isinstance(color, (list, tuple)) and len(color) in (3, 4)):
            raise ValueError("color must be an RGB (3) or RGBA (4) tuple/list")

        self.min_x = min_x
        self.max_x = max_x
        self.y = y
        self.dragging = False
        
        self.track = pyglet.shapes.Line(min_x, y, max_x, y, width=2, 
                                        color=(100, 100, 100, 255), batch=batch)
        
        self.handle = pyglet.shapes.Circle(starting_x, y, 10, color=color, batch=batch)
        
        if window:
            window.push_handlers(on_mouse_press=self.on_mouse_press,
                                 on_mouse_release=self.on_mouse_release,
                                 on_mouse_drag=self.on_mouse_drag)

    @property
    def value(self):
        """Returns a normalized value between 0.0 and 1.0 based on handle position."""
        return (self.handle.x - self.min_x) / (self.max_x - self.min_x)

    def on_mouse_press(self, x, y, button, modifiers):
        if (x - self.handle.x)**2 + (y - self.handle.y)**2 < 100:
            self.dragging = True

    def on_mouse_release(self, x, y, button, modifiers):
        self.dragging = False

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.dragging:
            self.handle.x = max(self.min_x, min(x, self.max_x))

    def get_value(self):
        total_range = self.max_x - self.min_x
        current_pos = self.handle.x - self.min_x
        return current_pos / total_range

class PygletEasyDraw:
    def __init__(self, batch=None):
        self.batch = batch if batch else pyglet.graphics.Batch()
        self.drawables = []

    def rect(self, x, y, width, height, color=(255, 255, 255), opacity=255):
        """Simple one-line Rectangle for Pyglet."""
        r = shapes.Rectangle(x, y, width, height, color=color, batch=self.batch)
        r.opacity = opacity
        self.drawables.append(r)
        return r

    def circle(self, x, y, radius, color=(255, 255, 255), opacity=255):
        """Simple one-line Circle for Pyglet."""
        c = shapes.Circle(x, y, radius, color=color, batch=self.batch)
        c.opacity = opacity
        self.drawables.append(c)
        return c

    def line(self, x, y, x2, y2, thickness=1, color=(255, 255, 255)):
        """Simple one-line Line for Pyglet."""
        l = shapes.Line(x, y, x2, y2, width=thickness, color=color, batch=self.batch)
        self.drawables.append(l)
        return l

    def draw(self):
        """The magic command to show everything on screen."""
        self.batch.draw()

class ArcadeVisibleVariable(arcade.Text):
    def __init__(self, font, fontsize, fontcolor, x, y, string, background_t_f, backgroundcolor=None):
        super().__init__(str(string), x, y, color=fontcolor, font_size=fontsize, font_name=font)
        self.bg_enabled = background_t_f
        self.bg_color = backgroundcolor

    def draw(self):
        if self.bg_enabled and self.bg_color:
            arcade.draw_lrtb_rectangle_filled(
                self.left - 5, self.right + 5, 
                self.top + 5, self.bottom - 5, 
                self.bg_color
            )
        super().draw()

class ArcadeClickedCalculator:
    def clicked(self, x, y, button):
        if button == arcade.MOUSE_BUTTON_LEFT:
            return self.collides_with_point((x, y))
        return False

class ArcadeHealthBar:
    def __init__(self, x, y, width_per_hp, max_hp, current_hp, height, border_color, health_color):
        self.x, self.y = x, y
        self.w_p_hp, self.max_hp = width_per_hp, max_hp
        self.height = height
        self.b_color, self.h_color = border_color, health_color
        self.current_hp = current_hp

    def draw(self):
        arcade.draw_rectangle_filled(self.x, self.y, self.max_hp * self.w_p_hp, self.height, self.b_color)
        hp_width = self.current_hp * self.w_p_hp
        arcade.draw_rectangle_filled(self.x - (self.max_hp * self.w_p_hp / 2) + (hp_width / 2), 
                                     self.y, hp_width, self.height - 4, self.h_color)

class ArcadeVisibleList:
    def __init__(self, font, fontsize, fontcolor, x, y, items):
        self.items = arcade.SpriteList()
        self.x, self.y = x, y
        self.font, self.size, self.color = font, fontsize, fontcolor
        self.refresh_list(items)

    def refresh_list(self, items):
        self.items = []
        for i, text in enumerate(items):
            label = arcade.Text(str(text), self.x, self.y - (i * (self.size + 10)), 
                                self.color, self.size, font_name=self.font)
            self.items.append(label)

    def draw(self):
        for item in self.items:
            item.draw()

class ArcadeGUIComponents:
    @staticmethod
    def create_textbox(manager, x, y, width, text=""):
        input_box = arcade.gui.UIInputText(x=x, y=y, width=width, text=text)
        manager.add(input_box)
        return input_box

    @staticmethod
    def create_slider(manager, x, y, width, value=50):
        slider = arcade.gui.UISlider(x=x, y=y, width=width, value=value)
        manager.add(slider)
        return slider

from arcade import shapes

class ArcadeEasyDraw:
    def __init__(self):
        self.shape_list = arcade.ShapeElementList()

    def rect(self, x, y, width, height, color=arcade.color.WHITE, border_width=0, tilt_angle=0):
        """Simple one-line Rectangle for Arcade."""
        center_x = x + (width / 2)
        center_y = y - (height / 2)
        try:
            r = arcade.create_rectangle_filled(center_x, center_y, width, height, color, tilt_angle)
            self.shape_list.append(r)
        except:
            r = arcade.create_rect_filled(center_x, center_y, width, height, color, tilt_angle)
            self.shape_list.append(r)
        
        if border_width > 0:
            try:
                b = arcade.create_rectangle_outline(center_x, center_y, width, height, color, border_width)
                self.shape_list.append(b)
            except:
                b = arcade.create_rect_outline(center_x, center_y, width, height, color, border_width)
                self.shape_list.append(b)
        return r

    def circle(self, x, y, radius, color=arcade.color.WHITE):
        """Simple one-line Circle for Arcade."""
        c = arcade.create_circle_filled(x, y, radius, color)
        self.shape_list.append(c)
        return c

    def line(self, x, y, x2, y2, color=arcade.color.WHITE, thickness=1):
        """Simple one-line Line for Arcade."""
        l = arcade.create_line(x, y, x2, y2, color, thickness)
        self.shape_list.append(l)
        return l

    def draw(self):
        """The magic command to show the entire batch at once."""
        self.shape_list.draw()

    def clear(self):
        """Clears the batch if the user wants to start fresh."""
        self.shape_list = arcade.ShapeElementList()

def bigstr(initial_text=""):
    return BigString(initial_text)

def bigdec(value, scale=0):
    return BigDecimal(value, scale)

bigvector2 = BigVector2
# --- PYGAME WRAPPERS ---
class PygameSprite(pygame.sprite.Sprite):
    def __init__(self, x="0.0", y="0.0", width=50, height=50, color=(255, 255, 255)):
        super().__init__()
        self.pos = bigvector2(str(x), str(y))
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.sync()

    def sync(self):
        p = self.pos.to_pygame()
        self.rect.topleft = (int(p.x), int(p.y))

class PygameGroup(pygame.sprite.Group):
    def draw_all(self, surface):
        self.draw(surface)

class PygameLayeredGroup(pygame.sprite.LayeredUpdates):
    pass

#? --- ARCADE WRAPPERS ---
class ArcadeSprite(arcade.Sprite):
    def __init__(self, x="0.0", y="0.0", scale=1.0):
        super().__init__(scale=scale)
        self.pos = bigvector2(str(x), str(y))
        self.center_x = self.pos.x.to_float()
        self.center_y = self.pos.y.to_float()

class ArcadeGroup(arcade.SpriteList):
    pass

#? --- PYGLET WRAPPERS ---
class PygletSprite(pyglet.sprite.Sprite):
    def __init__(self, img, x="0.0", y="0.0", batch=None):
        self.pos = bigvector2(str(x), str(y))
        super().__init__(img, x=self.pos.x.to_float(), y=self.pos.y.to_float(), batch=batch)

class PygletGroup(pyglet.graphics.Group):
    pass