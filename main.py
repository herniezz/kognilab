import os
import random
import time
import csv
import pygame
from pygame.locals import *
import cv2

# === konfiguracja ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
stim_dir = os.path.join(BASE_DIR, 'stimuli')
data_dir = os.path.join(BASE_DIR, 'data')

# subfoldery
ton_dir = os.path.join(stim_dir, 'tonal')
aton_dir = os.path.join(stim_dir, 'atonal')

# zbieranie plikow audio
ton_files = [os.path.join('tonal', f) for f in os.listdir(ton_dir)
             if f.lower().endswith(('.wav', '.mp3', '.ogg'))]
aton_files = [os.path.join('atonal', f) for f in os.listdir(aton_dir)
              if f.lower().endswith(('.wav', '.mp3', '.ogg'))]

# test, czy na pewno jest 5 plikow
if len(ton_files) != 5 or len(aton_files) != 5:
    raise SystemExit(
        "Potrzebujesz dokładnie 5 plików tonalnych i 5 atonalnych w odpowiednich podfolderach.")

# losuj pliki
stimuli = [(f, 'tonal') for f in ton_files] + [(f, 'atonal') for f in aton_files]
random.shuffle(stimuli)

# przygotowanie logow - data, numer
date_str = time.strftime("%Y-%m-%d")
PARTICIPANT_NUMBER = 1
log_filename = os.path.join(data_dir, f"badany_{PARTICIPANT_NUMBER}_{date_str}.csv")

# napisz caly csv raz
with open(log_filename, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['trial_num', 'condition', 'file']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

# === init pygame ===
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((0, 0), FULLSCREEN)
pygame.display.set_caption('Badanie reakcji emocjonalnych na muzykę')
font = pygame.font.SysFont('Arial', 48)
time_font = pygame.font.SysFont('Arial', 36)
clock = pygame.time.Clock()
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# === utilsy ===
def cleanup_and_exit():
    """Zwalnia zasoby Pygame i zamyka aplikację."""
    pygame.quit()
    exit()


def wait_for_input():
    """Czeka na dowolny klawisz lub kliknięcie myszy. Esc zamyka aplikację."""
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                cleanup_and_exit()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    cleanup_and_exit()
                return
            if event.type == MOUSEBUTTONDOWN:
                return
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
    """Odtwarza fragment audio i nagrywa wideo z kamery, nakładając numer próby."""
    # inicjalizacja kamery
    cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
    if not cap.isOpened():
        print("Nie można otworzyć kamery")
        return
    # parametry nagrywania
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_filename = os.path.join(data_dir, f"badany_{PARTICIPANT_NUMBER}_{date_str}_trial{idx}.mp4")
    out = cv2.VideoWriter(video_filename, fourcc, 20.0, (frame_width, frame_height))

    # start audio
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()
    start_time = time.time()

    while pygame.mixer.music.get_busy():
        elapsed = time.time() - start_time
        # ograniczenie długości dla atonalnych
        if max_duration and elapsed >= max_duration:
            pygame.mixer.music.stop()
            break

        # capture frame
        ret, frame = cap.read()
        if not ret:
            break
        # nakładanie tekstu (numer próby)
        cv2.putText(frame, f"Fragment {idx}/{len(stimuli)}", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        out.write(frame)

        # wyświetlanie statusu w Pygame
        for event in pygame.event.get():
            if event.type == QUIT:
                cap.release()
                out.release()
                cleanup_and_exit()
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                cap.release()
                out.release()
                cleanup_and_exit()

        screen.fill(BLACK)
        msg = f"Odtwarzanie {idx}/{len(stimuli)}"
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

    # zwolnienie zasobów
    cap.release()
    out.release()

# === cały flow eksperymentu ===
def main():
    show_message(
        "Witaj w badaniu reakcji emocjonalnych na muzykę!\n\n"
        "Będziesz słuchał/a 10 fragmentów muzycznych.\n\n"
        "Naciśnij dowolny klawisz, aby zakończyć."
    )

    total_trials = len(stimuli)
    for idx, (rel_path, cond) in enumerate(stimuli, start=1):
        show_message(
            f"Fragment {idx} z {total_trials}\n\n"
            "Naciśnij dowolny klawisz, aby rozpocząć odtwarzanie."
        )
        full_path = os.path.join(stim_dir, rel_path)
        limit = 30 if cond == 'atonal' else None
        play_fragment(full_path, idx, max_duration=limit)

        show_message(
            f"Fragment {idx} z {total_trials}\n\n"
            "Uzupełnij kwestionariusz na papierze.\n\n"
            "Po zakończeniu naciśnij dowolny klawisz, aby kontynuować."
        )

        with open(log_filename, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['trial_num', 'condition', 'file'])
            writer.writerow({'trial_num': idx, 'condition': cond, 'file': rel_path})

        if idx < total_trials:
            show_message(
                f"Przygotowanie do fragmentu {idx+1} z {total_trials}\n\n"
                "Naciśnij dowolny klawisz, aby kontynuować."
            )

    show_message(
        "Dziękujemy za udział w badaniu!\n\n"
        "Naciśnij dowolny klawisz, aby zakończyć."
    )
    cleanup_and_exit()

if __name__ == '__main__':
    main()
