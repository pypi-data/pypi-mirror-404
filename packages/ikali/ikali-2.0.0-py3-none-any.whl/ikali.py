"""
iKALI - The iCarly-themed terminal experience
A joke on Kali Linux meets iCarly
Now with TRUE RGB gradient colors!
"""
import time
import sys
import os
import math

# ===== CONFIGURATION OPTIONS =====
# Adjust these values to customize the animation speeds and behavior

# Typewriter effect speed (seconds per character)
TYPEWRITER_SPEED = 0.03

# Rainbow animation cycles (how many color shifts after typewriter)
RAINBOW_CYCLES = 36

# Rainbow animation speed (seconds per cycle)
RAINBOW_SPEED = 0.04

# Logo rainbow animation cycles
LOGO_RAINBOW_CYCLES = 36

# Logo rainbow animation speed
LOGO_RAINBOW_SPEED = 0.04

# Pause after each lyric line (seconds)
LYRIC_PAUSE = 0.05

# Pause between stanzas (seconds)
STANZA_PAUSE = 0.1

# Pause before showing footer (seconds)
FOOTER_DELAY = 1.0

# Pause after footer before exit (seconds)
EXIT_DELAY = 3.0

# ===== END CONFIGURATION =====


def rgb_to_ansi(r, g, b):
    """Convert RGB to ANSI true color code"""
    return f"\033[38;2;{r};{g};{b}m"

def reset_color():
    """Reset color to default"""
    return "\033[0m"

def get_rainbow_rgb(position):
    """Generate smooth RGB rainbow color using HSV color wheel"""
    # Normalize position to 0-1 range
    hue = (position % 360) / 360.0
    
    # Convert HSV (hue, saturation=1, value=1) to RGB
    h = hue * 6.0
    x = 1 - abs((h % 2) - 1)
    
    if h < 1:
        r, g, b = 1, x, 0
    elif h < 2:
        r, g, b = x, 1, 0
    elif h < 3:
        r, g, b = 0, 1, x
    elif h < 4:
        r, g, b = 0, x, 1
    elif h < 5:
        r, g, b = x, 0, 1
    else:
        r, g, b = 1, 0, x
    
    # Convert to 0-255 range
    return int(r * 255), int(g * 255), int(b * 255)

def rainbow_text(text, offset=0):
    """Apply smooth gradient rainbow colors to text"""
    result = ""
    char_count = 0
    for char in text:
        if char != ' ' and char != '\n':
            # Calculate hue position (0-360 degrees)
            # Adjusted so offset=0 starts with red (hue=0)
            hue = (offset * 10 + char_count * 8) % 360
            r, g, b = get_rainbow_rgb(hue)
            result += rgb_to_ansi(r, g, b) + char
            char_count += 1
        else:
            result += char
    return result + reset_color()

def clear_screen():
    """Clear the terminal screen"""
    os.system('clear' if os.name != 'nt' else 'cls')

def hide_cursor():
    """Hide the terminal cursor"""
    sys.stdout.write('\033[?25l')
    sys.stdout.flush()

def show_cursor():
    """Show the terminal cursor"""
    sys.stdout.write('\033[?25h')
    sys.stdout.flush()

def print_logo_animated():
    """Print iKALI ASCII logo with animated rainbow effect"""
    logo = """
██╗██╗  ██╗ █████╗ ██╗     ██╗
╚═╝██║ ██╔╝██╔══██╗██║     ██║
██╗█████╔╝ ███████║██║     ██║
██║██╔═██╗ ██╔══██║██║     ██║
██║██║  ██╗██║  ██║███████╗██║
╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝
    """
    
    lines = logo.strip().split('\n')
    
    # Print initial logo (no typewriter, just appear)
    for line in lines:
        print(rainbow_text(line, offset=0))
    
    # Animate the logo with smooth gradient flow - end at offset 0 (back to red)
    for cycle in range(1, LOGO_RAINBOW_CYCLES + 1):
        sys.stdout.write(f'\033[{len(lines)}A')
        for line in lines:
            sys.stdout.write('\r')
            sys.stdout.write('\033[K')
            print(rainbow_text(line, offset=cycle % 36))  # Modulo 36 to cycle back to start
        sys.stdout.flush()
        time.sleep(LOGO_RAINBOW_SPEED)

def print_line_animated(text):
    """Print a single line with typewriter effect then animated gradient rainbow effect"""
    # Typewriter effect - starts at offset 0 (red)
    for i in range(len(text) + 1):
        sys.stdout.write('\r')
        sys.stdout.write('\033[K')
        sys.stdout.write(rainbow_text(text[:i], offset=0))
        sys.stdout.flush()
        time.sleep(TYPEWRITER_SPEED)
    
    print()
    
    # Animate it through color spectrum - one full rainbow cycle
    for cycle in range(0, RAINBOW_CYCLES):
        sys.stdout.write('\033[1A')
        sys.stdout.write('\r')
        sys.stdout.write('\033[K')
        print(rainbow_text(text, offset=cycle))
        sys.stdout.flush()
        time.sleep(RAINBOW_SPEED)

def sing_theme():
    """Display the iCarly theme song lyrics with animation"""
    lyrics = [
        "I know, you see,",
        "Somehow the world will change for me,",
        "And be so wonderful.",
        "",
        "Live life, breathe air,",
        "I know somehow we're gonna get there,",
        "And feel so wonderful.",
        "",
        "It's all for real-",
        "I'm telling you just how I feel;",
        "So wake up the members of my nation",
        "It's your time to be-",
        "There's no chance unless you take one.",
        "And the time to see the brighter side of every situation.",
        "Some things are meant to be",
        "So give me your best and leave the rest to me.",
        "",
        "Leave it all to me.",
        "Leave it all to me.",
        "Just leave it all to me.",
    ]
    
    for line in lyrics:
        if line:
            print_line_animated(line)
            time.sleep(LYRIC_PAUSE)
        else:
            print()
            time.sleep(STANZA_PAUSE)

def footer():
    """Print footer message"""
    print("\n")
    messages = [
        "iKALI: a stupid command that shouldn't exist.",
        "Not affiliated with Kali Linux or Nickelodeon.",
        "Powered by nostalgia and plenty of Vodka.",
    ]
    
    for msg in messages:
        print_line_animated(msg)
        time.sleep(LYRIC_PAUSE)
    print()

def main():
    """Main function"""
    try:
        hide_cursor()
        clear_screen()
        print_logo_animated()
        print("\n")
        time.sleep(0.8)
        sing_theme()
        time.sleep(FOOTER_DELAY)
        footer()
        time.sleep(EXIT_DELAY)
        show_cursor()
    except KeyboardInterrupt:
        show_cursor()
        r, g, b = get_rainbow_rgb(60)
        print(f"\n\n{rgb_to_ansi(r, g, b)}Interrupted! See you later! 👋{reset_color()}")
        sys.exit(0)

if __name__ == "__main__":
    main()
