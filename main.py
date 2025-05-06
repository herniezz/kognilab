import os
import random
import time
import csv
import pygame
from pygame.locals import *

# === Configuration ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
stim_dir = os.path.join(BASE_DIR, 'stimuli')
data_dir = os.path.join(BASE_DIR, 'data')

# Subdirectories for tonal and atonal files
ton_dir = os.path.join(stim_dir, 'tonal')
aton_dir = os.path.join(stim_dir, 'atonal')

# Collect audio files
ton_files = [os.path.join('tonal', f) for f in os.listdir(ton_dir)
             if f.lower().endswith(('.wav', '.mp3', '.ogg'))]
aton_files = [os.path.join('atonal', f) for f in os.listdir(aton_dir)
              if f.lower().endswith(('.wav', '.mp3', '.ogg'))]

# Ensure exactly 5 of each condition
if len(ton_files) != 5 or len(aton_files) != 5:
    raise SystemExit(
        "Potrzebujesz dokładnie 5 plików tonalnych i 5 atonalnych w odpowiednich podfolderach.")

# Build and shuffle stimulus list
stimuli = [(f, 'tonal') for f in ton_files] + [(f, 'atonal') for f in aton_files]
random.shuffle(stimuli)

# Participant ID and logging setup
timestamp = int(time.time())
participant_id = f'participant_{timestamp}'
log_filename = os.path.join(data_dir, f"{participant_id}_data.csv")

# Create data directory if missing
os.makedirs(data_dir, exist_ok=True)

# Write CSV header
with open(log_filename, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['trial_num', 'condition', 'file']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

# === Pygame Initialization ===
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((0, 0), FULLSCREEN)
pygame.display.set_caption('Badanie reakcji emocjonalnych na muzykę')
font = pygame.font.SysFont('Arial', 48)
time_font = pygame.font.SysFont('Arial', 36)
clock = pygame.time.Clock()
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# === Utility Functions ===
def wait_for_input():
    """Czeka na dowolny klawisz lub kliknięcie myszy."""
    while True:
        for event in pygame.event.get():
            if event.type in (KEYDOWN, MOUSEBUTTONDOWN):
                return
            if event.type == QUIT:
                pygame.quit()
                exit()
        clock.tick(30)


def show_message(text):
    """Wyświetla tekst na środku ekranu i czeka na wejście."""
    screen.fill(BLACK)
    lines = text.split('\n')
    total_height = len(lines) * font.get_linesize()
    for idx, line in enumerate(lines):
        surf = font.render(line, True, WHITE)
        rect = surf.get_rect(
            center=(screen.get_width() // 2,
                    screen.get_height() // 2 - total_height // 2 + idx * font.get_linesize())
        )
        screen.blit(surf, rect)
    pygame.display.flip()
    wait_for_input()


def play_fragment(path, idx, max_duration=None):
    """Odtwarza fragment audio z opcjonalnym limitem czasu w sekundach."""
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()
    start_time = time.time()

    while pygame.mixer.music.get_busy():
        elapsed = time.time() - start_time
        if max_duration and elapsed >= max_duration:
            pygame.mixer.music.stop()
            break

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                exit()

        # Render playback screen\
        screen.fill(BLACK)
        msg = f"Odtwarzanie fragmentu {idx}"
        msg_surf = font.render(msg, True, WHITE)
        msg_rect = msg_surf.get_rect(
            center=(screen.get_width() // 2, screen.get_height() // 2)
        )
        screen.blit(msg_surf, msg_rect)

        timer_text = f"Czas: {int(elapsed)} s"
        timer_surf = time_font.render(timer_text, True, WHITE)
        timer_rect = timer_surf.get_rect(
            topright=(screen.get_width() - 20, 20)
        )
        screen.blit(timer_surf, timer_rect)

        pygame.display.flip()
        clock.tick(30)

# === Main Experiment Flow ===
def main():
    # Powitanie
    show_message(
        "Witaj w badaniu reakcji emocjonalnych na muzykę!\n\n"
        "Będziesz słuchał/a 10 fragmentów muzycznych.\n\n"
        "Załóż Apple Watch i przygotuj się do rejestracji ECG.\n\n"
        "Naciśnij dowolny klawisz, aby rozpocząć."
    )

    # Instrukcja przed rozpoczęciem rejestracji ECG
    show_message(
        "Proszę uruchomić rejestrację ECG na Apple Watch.\n\n"
        "Upewnij się, że urządzenie jest prawidłowo założone.\n\n"
        "Naciśnij dowolny klawisz, aby kontynuować."
    )

    # Pętle prób
    total_trials = len(stimuli)
    for idx, (rel_path, cond) in enumerate(stimuli, start=1):
        # Przed odtwarzaniem
        show_message(
            f"Fragment {idx} z {total_trials}\n\n"
            "Naciśnij dowolny klawisz, aby rozpocząć odtwarzanie."
        )
        full_path = os.path.join(stim_dir, rel_path)

        # Ustal limit czasu dla atonalnych
        limit = 30 if cond == 'atonal' else None
        play_fragment(full_path, idx, max_duration=limit)

        # Po odtwarzaniu: ankieta
        show_message(
            f"Fragment {idx} z {total_trials}\n\n"
            "Uzupełnij kwestionariusz na papierze.\n\n"
            "Po zakończeniu naciśnij dowolny klawisz."
        )

        # Zapis w CSV (z zachowaniem relatywnej ścieżki)
        with open(log_filename, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['trial_num', 'condition', 'file'])
            writer.writerow({
                'trial_num': idx,
                'condition': cond,
                'file': rel_path
            })

        # Przygotowanie do następnej próby
        if idx < total_trials:
            show_message(
                f"Przygotowanie do fragmentu {idx+1} z {total_trials}\n\n"
                "Uruchom rejestrację ECG na Apple Watch.\n\n"
                "Naciśnij dowolny klawisz, aby kontynuować."
            )

    # Ekran końcowy
    show_message(
        "Dziękujemy za udział w badaniu!\n\n"
        "Naciśnij dowolny klawisz, aby zakończyć."
    )
    pygame.quit()

if __name__ == '__main__':
    main()
