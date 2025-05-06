import os
import random
import time
import csv
import pygame
from pygame.locals import *

from main import show_message

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

# === Pygame Initialization ===
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((0, 0), FULLSCREEN)
pygame.display.set_caption('Badanie reakcji emocjonalnych na muzykę')
font = pygame.font.SysFont('Arial', 36)
time_font = pygame.font.SysFont('Arial', 24)
clock = pygame.time.Clock()
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# === Utility Functions ===
def draw_text(lines, prompt=""):
    screen.fill(BLACK)
    total_height = len(lines) * font.get_linesize()
    for idx, line in enumerate(lines):
        surf = font.render(line, True, WHITE)
        rect = surf.get_rect(
            center=(screen.get_width()//2,
                    screen.get_height()//2 - total_height//2 + idx*font.get_linesize())
        )
        screen.blit(surf, rect)
    if prompt:
        prompt_surf = time_font.render(prompt, True, WHITE)
        screen.blit(prompt_surf, (50, screen.get_height()-50))
    pygame.display.flip()


def text_input(question):
    text = ''
    while True:
        lines = question.split('\n') + [text]
        draw_text(lines, "Enter=OK, Backspace=Usuń")
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                if event.key == K_RETURN:
                    return text
                elif event.key == K_BACKSPACE:
                    text = text[:-1]
                else:
                    text += event.unicode
            elif event.type == QUIT:
                pygame.quit(); exit()
        clock.tick(30)


def multiple_choice(question, options):
    idx = 0
    while True:
        lines = [question] + [f"{'>' if i==idx else ' '} {opt}" for i,opt in enumerate(options)]
        draw_text(lines, "Enter=Potwierdź, ↑/↓=Wybór")
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                if event.key in (K_UP, K_w): idx = (idx-1) % len(options)
                elif event.key in (K_DOWN, K_s): idx = (idx+1) % len(options)
                elif event.key == K_RETURN:
                    return options[idx]
            elif event.type == QUIT:
                pygame.quit(); exit()
        clock.tick(30)


def play_fragment(path, idx, max_duration=None):
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()
    start_time = time.time()
    while pygame.mixer.music.get_busy():
        elapsed = time.time() - start_time
        if max_duration and elapsed >= max_duration:
            pygame.mixer.music.stop(); break
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit(); exit()
        screen.fill(BLACK)
        msg = f"Odtwarzanie {idx}/{len(stimuli)}"
        timer = time_font.render(f"Czas: {int(elapsed)} s", True, WHITE)
        screen.blit(font.render(msg, True, WHITE),(50,50))
        screen.blit(timer, (50,100))
        pygame.display.flip(); clock.tick(30)

# === Data Logging Setup with Demographics ===
# Collect demographics
show_message(
    "Witaj w badaniu reakcji emocjonalnych na muzykę!\n"
    "Przed rozpoczęciem, proszę odpowiedzieć na kilka pytań demograficznych."
)
gender = multiple_choice("1. Płeć:", ['Kobieta', 'Mężczyzna', 'Inna'])
age = text_input("2. Wiek (w latach):")
education = multiple_choice("3. Wykształcenie:", ['Podstawowe','Średnie','Wyższe (lic./inż.)','Wyższe (mgr)','Doktorat lub wyższe'])
music_edu = multiple_choice("4. Czy masz wykształcenie muzyczne?", ['Tak','Nie'])
if music_edu == 'Tak':
    music_years = text_input("5. Ile lat trwało Twoje wykształcenie muzyczne?:")
    instrument = text_input("6. Na jakim instrumencie?:")
else:
    music_years = ''
    instrument = ''
listening_freq = multiple_choice("7. Jak często słuchasz muzyki?",
                                 ['Codziennie','Kilka razy w tygodniu','Kilka razy w miesiącu','Rzadko','Prawie nigdy'])

# Write CSV header including demographics
with open(log_filename, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['trial_num','condition','file','gender','age','education','music_edu','music_years','instrument','listening_freq','pleasant','arousal','emotions']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerow({
        'trial_num': 0,
        'gender': gender,
        'age': age,
        'education': education,
        'music_edu': music_edu,
        'music_years': music_years,
        'instrument': instrument,
        'listening_freq': listening_freq
    })

# === Main Experiment Flow ===
def main():
    # Instrukcja Apple Watch przed eksperymentem
    show_message(
        "Przed rozpoczęciem eksperymentu:\n"
        "• Załóż Apple Watch na nadgarstek.\n"
        "• Uruchom aplikację EKG, aby rejestrować sygnał.\n"
        "• Upewnij się, że Apple Watch jest poprawnie dopasowany.\n"
        "\nNaciśnij dowolny klawisz, aby rozpocząć."
    )

    total_trials = len(stimuli)
    # Pętla prób
    for idx, (rel_path, cond) in enumerate(stimuli, start=1):
        # Ekran startu odtwarzania
        show_message(
            f"Fragment {idx} z {total_trials}\n"
            "Naciśnij dowolny klawisz, aby rozpocząć odtwarzanie."
        )

        # Odtwarzanie fragmentu z limitem dla atonalnych
        max_dur = 30 if cond == 'atonal' else None
        play_fragment(os.path.join(stim_dir, rel_path), idx, max_duration=max_dur)

        # Pytania oceniajace fragment
        pleasant = text_input("1. Jak przyjemny był fragment? Skala 1–7:")
        arousal = text_input("2. Jak bardzo pobudzony/a czujesz się? Skala 1–7:")
        emotions = text_input("3. Jakie emocje wywołał fragment?:")

        # Zapis wyników
        with open(log_filename, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow({
                'trial_num': idx,
                'condition': cond,
                'file': rel_path,
                'pleasant': pleasant,
                'arousal': arousal,
                'emotions': emotions
            })

        # Między próbami: przypomnienie Apple Watch
        if idx < total_trials:
            show_message(
                f"Przygotowanie do fragmentu {idx+1} z {total_trials}:\n"
                "• Sprawdź, czy Apple Watch nadal rejestruje sygnał EKG.\n"
                "• Jeśli trzeba, popraw ułożenie zegarka.\n"
                "\nNaciśnij dowolny klawisz, aby kontynuować."
            )


    show_message(
        "Dziękujemy za udział w badaniu!\n"
        "Twoje dane zostały zapisane.\n"
        "Naciśnij dowolny klawisz, aby zakończyć."
    )
    pygame.quit()

if __name__ == '__main__':
    main()
