#!/usr/bin/env python3
"""NICE: FINE-FM Pygame Visualization.
A deadpan engineering visualization layer for BAGUS: FINE-FM.
Consumes FINE-FM domain calculations directly. Does not modify BLOON 
or BLOON_MACHINE, and does not pretend to invoke them if unwired.
"""
import sys
import math
import argparse
from pathlib import Path

# -----------------------------------------------------------------------------
# Path setup to import FINE-FM modules regardless of execution directory
# -----------------------------------------------------------------------------
# Add E:\ to sys.path so the 'bloon_bagus' package can be found
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from bloon_bagus import problems
from bloon_bagus.backends import PureBackend

# -----------------------------------------------------------------------------
# Graceful Pygame handling
# -----------------------------------------------------------------------------
try:
    import pygame
except ImportError:
    print("=" * 50)
    print("ERROR: Pygame is not installed.")
    print("Please install it using: pip install pygame")
    print("=" * 50)
    sys.exit(1)

# -----------------------------------------------------------------------------
# Pygame Initialization & Constants
# -----------------------------------------------------------------------------
pygame.init()
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NICE: FINE-FM Visualization")

font = pygame.font.SysFont("consolas", 20)
small_font = pygame.font.SysFont("consolas", 16)
title_font = pygame.font.SysFont("consolas", 32, bold=True)

BG_COLOR = (240, 240, 240)
TEXT_COLOR = (30, 30, 30)
WATER_COLOR = (70, 130, 180)
WATER_DARK = (20, 50, 100)
BUCKET_COLOR = (150, 150, 150)
ARROW_UP = (0, 180, 0)
ARROW_DOWN = (200, 0, 0)
PANEL_BG = (255, 255, 255)
BORDER_COLOR = (100, 100, 100)

backend = PureBackend()

# -----------------------------------------------------------------------------
# Helper Rendering Functions
# -----------------------------------------------------------------------------
def draw_text(surface, text, pos, color=TEXT_COLOR, f=font, center=False):
    lines = text.split('\n')
    y = pos[1]
    for line in lines:
        rendered = f.render(line, True, color)
        rect = rendered.get_rect()
        if center:
            rect.centerx = pos[0]
            rect.y = y
        else:
            rect.topleft = (pos[0], y)
        surface.blit(rendered, rect)
        y += f.get_height() + 2

def draw_panel(surface, rect):
    pygame.draw.rect(surface, PANEL_BG, rect)
    pygame.draw.rect(surface, BORDER_COLOR, rect, 2)

def draw_arrow(surface, start, end, color, width=3):
    pygame.draw.line(surface, color, start, end, width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    arrow_len = 15
    arrow_angle = math.pi / 6
    p1 = (end[0] - arrow_len * math.cos(angle - arrow_angle), 
          end[1] - arrow_len * math.sin(angle - arrow_angle))
    p2 = (end[0] - arrow_len * math.cos(angle + arrow_angle), 
          end[1] - arrow_len * math.sin(angle + arrow_angle))
    pygame.draw.polygon(surface, color, [end, p1, p2])

# -----------------------------------------------------------------------------
# Demo 1: Water in a Bucket
# -----------------------------------------------------------------------------
def demo_bucket():
    h = 0.3
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: return False
                if event.key == pygame.K_UP: h = min(2.0, h + 0.05)
                if event.key == pygame.K_DOWN: h = max(0.05, h - 0.05)
                if event.key == pygame.K_m: return True

        rec = problems.bucket(backend, h=h)
        screen.fill(BG_COLOR)
        draw_text(screen, "WATER IN A BUCKET", (WIDTH//2, 30), f=title_font, center=True)
        draw_text(screen, "The deeper the water, the more seriously the bucket takes physics.", (WIDTH//2, 70), f=small_font, center=True)
        
        bucket_top_w, bucket_bot_w, bucket_h = 300, 240, 400
        cx, cy = WIDTH // 2 + 100, 350
        points = [(cx - bucket_top_w//2, cy - bucket_h//2), (cx + bucket_top_w//2, cy - bucket_h//2),
                  (cx + bucket_bot_w//2, cy + bucket_h//2), (cx - bucket_bot_w//2, cy + bucket_h//2)]
        pygame.draw.polygon(screen, BUCKET_COLOR, points, 4)
        
        max_h = 2.0
        water_y_top = cy + bucket_h//2 - int((h / max_h) * (bucket_h - 10))
        w_at_water = bucket_bot_w + (bucket_top_w - bucket_bot_w) * (1.0 - (water_y_top - (cy - bucket_h//2)) / bucket_h)
        water_points = [(cx - w_at_water//2 + 5, water_y_top), (cx + w_at_water//2 - 5, water_y_top),
                        (cx + bucket_bot_w//2 - 5, cy + bucket_h//2 - 5), (cx - bucket_bot_w//2 + 5, cy + bucket_h//2 - 5)]
        pygame.draw.polygon(screen, WATER_COLOR, water_points)
        
        panel_rect = pygame.Rect(50, 150, 300, 220)
        draw_panel(screen, panel_rect)
        info = f"Depth (h):    {h:.2f} m\nDensity (ρ):  1000.0 kg/m³\nGravity (g):  9.80665 m/s²\nP_atm (P0):   101325.0 Pa\n------------------------\nGauge P:      {rec.computed['gauge'].value:.1f} Pa\nAbsolute P:   {rec.computed['absolute'].value:.1f} Pa"
        draw_text(screen, info, (panel_rect.x + 15, panel_rect.y + 15), f=small_font)
        
        draw_text(screen, "Controls: [UP/DOWN] Depth  [M] Menu  [ESC] Quit", (WIDTH//2, HEIGHT - 40), f=small_font, center=True)
        pygame.display.flip()
        pygame.time.Clock().tick(60)
    return True

# -----------------------------------------------------------------------------
# Demo 2: Hydrostatic Pressure
# -----------------------------------------------------------------------------
def demo_hydrostatic():
    h = 10.0
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: return False
                if event.key == pygame.K_UP: h = min(50.0, h + 1.0)
                if event.key == pygame.K_DOWN: h = max(1.0, h - 1.0)
                if event.key == pygame.K_m: return True

        rec = problems.hydrostatic_pressure(backend, h=h)
        screen.fill(BG_COLOR)
        draw_text(screen, "HYDROSTATIC PRESSURE", (WIDTH//2, 30), f=title_font, center=True)
        draw_text(screen, "P = P0 + ρ·g·h", (WIDTH//2, 70), f=font, center=True)
        
        col_x, col_y, col_w, col_h = WIDTH//2 - 50, 150, 100, 450
        pygame.draw.rect(screen, BUCKET_COLOR, (col_x, col_y, col_w, col_h), 2)
        
        for i in range(col_h):
            p_frac = (i / col_h) * (h / 50.0)
            c = tuple(int(WATER_COLOR[j] * (1 - p_frac) + WATER_DARK[j] * p_frac) for j in range(3))
            pygame.draw.line(screen, c, (col_x + 2, col_y + i), (col_x + col_w - 2, col_y + i))
            
        for d in range(0, int(h)+1, max(1, int(h/5))):
            y = col_y + int((d / h) * col_h)
            pygame.draw.line(screen, TEXT_COLOR, (col_x - 10, y), (col_x, y), 2)
            draw_text(screen, f"{d}m", (col_x - 40, y - 10), f=small_font)
            
        panel_rect = pygame.Rect(50, 150, 350, 180)
        draw_panel(screen, panel_rect)
        info = f"Current Depth: {h:.1f} m\nContribution:  {rec.computed['contribution'].value:.1f} Pa\nAbsolute (P):  {rec.computed['absolute'].value:.1f} Pa\nGauge (P-P0):  {rec.computed['gauge'].value:.1f} Pa"
        draw_text(screen, info, (panel_rect.x + 15, panel_rect.y + 15), f=small_font)
        
        draw_text(screen, "Controls: [UP/DOWN] Depth  [M] Menu  [ESC] Quit", (WIDTH//2, HEIGHT - 40), f=small_font, center=True)
        pygame.display.flip()
        pygame.time.Clock().tick(60)
    return True

# -----------------------------------------------------------------------------
# Demo 3: Pascal Hydraulic System (FIXED LAYOUT)
# -----------------------------------------------------------------------------
def demo_pascal():
    a1, a2, f1 = 0.01, 0.10, 100.0
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: return False
                if event.key == pygame.K_m: return True
                if event.key == pygame.K_UP: f1 = min(1000, f1 + 10)
                if event.key == pygame.K_DOWN: f1 = max(10, f1 - 10)
                if event.key == pygame.K_RIGHT: a2 = min(1.0, a2 + 0.01)
                if event.key == pygame.K_LEFT: a1 = max(0.001, a1 - 0.001)

        rec = problems.pascal_hydraulic(backend, a1=a1, a2=a2, f1=f1)
        screen.fill(BG_COLOR)
        
        # Title
        draw_text(screen, "PASCAL HYDRAULIC SYSTEM", (WIDTH//2, 30), f=title_font, center=True)
        draw_text(screen, "F1 / A1 = F2 / A2", (WIDTH//2, 70), f=font, center=True)
        
        # Layout: panel kiri, visual tengah-kanan
        # Compact info panel (kiri)
        panel_rect = pygame.Rect(50, 100, 220, 140)
        draw_panel(screen, panel_rect)
        f2 = rec.computed['output force'].value
        pressure = rec.computed['system pressure'].value
        ratio = rec.computed['area ratio'].value
        mech_adv = rec.computed['F2/F1'].value
        
        info_lines = [
            f"F1: {f1:.0f} N",
            f"A1: {a1:.3f} m²",
            f"A2: {a2:.3f} m²",
            f"---",
            f"F2: {f2:.1f} N",
            f"Pressure: {pressure:.0f} Pa",
            f"Ratio: {ratio:.1f}x"
        ]
        draw_text(screen, '\n'.join(info_lines), (panel_rect.x + 10, panel_rect.y + 10), f=small_font)
        
        # Visual: dua piston dengan skala yang lebih masuk akal
        # Normalisasi skala untuk visualisasi
        max_area_display = 0.2  # m² untuk skala visual
        scale_factor = 200 / max_area_display  # pixels per m²
        
        # Piston 1 (kiri) - lebih kecil
        w1 = max(40, int(a1 * scale_factor))
        h1_px = 180
        x1 = 400
        y1 = 350
        
        # Piston 2 (kanan) - lebih besar
        w2 = max(80, int(a2 * scale_factor))
        h2_px = 180
        x2 = 650
        y2 = 350
        
        # Gambar piston 1
        pygame.draw.rect(screen, (180, 180, 180), (x1, y1, w1, h1_px), 2)
        pygame.draw.rect(screen, (200, 200, 200), (x1 + 5, y1 + 10, w1 - 10, 30))
        
        # Arrow F1 (ke bawah)
        arrow_start_y = y1 - 60
        draw_arrow(screen, (x1 + w1//2, arrow_start_y), (x1 + w1//2, y1 + 5), ARROW_DOWN, 4)
        draw_text(screen, f"F1={f1:.0f}N", (x1 + w1//2, arrow_start_y - 25), f=font, center=True)
        draw_text(screen, f"A1={a1:.3f}m²", (x1 + w1//2, y1 + h1_px + 10), f=small_font, center=True)
        
        # Gambar piston 2
        pygame.draw.rect(screen, (180, 180, 180), (x2, y2, w2, h2_px), 2)
        pygame.draw.rect(screen, (200, 200, 200), (x2 + 5, y2 + 10, w2 - 10, 30))
        
        # Arrow F2 (ke bawah)
        arrow_start_y2 = y2 - 60
        draw_arrow(screen, (x2 + w2//2, arrow_start_y2), (x2 + w2//2, y2 + 5), ARROW_DOWN, 4)
        draw_text(screen, f"F2={f2:.0f}N", (x2 + w2//2, arrow_start_y2 - 25), f=font, center=True)
        draw_text(screen, f"A2={a2:.3f}m²", (x2 + w2//2, y2 + h2_px + 10), f=small_font, center=True)
        
        # Gambar cairan penghubung (di antara piston, di bawah)
        fluid_y = y1 + h1_px - 20
        fluid_height = 40
        pygame.draw.rect(screen, WATER_COLOR, (x1 + w1, fluid_y, x2 - (x1 + w1), fluid_height))
        pygame.draw.rect(screen, BUCKET_COLOR, (x1 + w1, fluid_y, x2 - (x1 + w1), fluid_height), 2)
        
        # Label formula
        draw_text(screen, f"F2/A2 = F1/A1 = {pressure:.0f} Pa", (WIDTH//2, 580), f=font, center=True)
        
        draw_text(screen, "Controls: [UP/DOWN] F1  [LEFT/RIGHT] A1  [M] Menu  [ESC] Quit", (WIDTH//2, HEIGHT - 40), f=small_font, center=True)
        pygame.display.flip()
        pygame.time.Clock().tick(60)
    return True

# -----------------------------------------------------------------------------
# Demo 4: Buoyancy (COMPLETELY FIXED - FINAL VERSION)
# -----------------------------------------------------------------------------
def demo_buoyancy():
    v_disp, m_obj = 0.05, 40.0
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: return False
                if event.key == pygame.K_m: return True
                if event.key == pygame.K_UP: m_obj = min(100, m_obj + 2)
                if event.key == pygame.K_DOWN: m_obj = max(5, m_obj - 2)
                if event.key == pygame.K_RIGHT: v_disp = min(0.2, v_disp + 0.01)
                if event.key == pygame.K_LEFT: v_disp = max(0.01, v_disp - 0.01)

        rec = problems.buoyancy(backend, rho_f=1000.0, v_disp=v_disp, object_mass=m_obj)
        
        # Ambil nilai fb dan w
        fb = rec.computed['buoyant force'].value
        w = rec.computed['object weight'].value
        
        screen.fill(BG_COLOR)
        
        # Title
        draw_text(screen, "BUOYANCY (ARCHIMEDES)", (WIDTH//2, 30), f=title_font, center=True)
        draw_text(screen, "F_B = ρ_f · g · V_displaced", (WIDTH//2, 70), f=font, center=True)
        
        # Tangki air (tengah)
        tank_width = 400
        tank_height = 350
        tank_x = WIDTH//2 - tank_width//2
        tank_y = 200
        
        # Gambar tangki
        pygame.draw.rect(screen, BUCKET_COLOR, (tank_x, tank_y, tank_width, tank_height), 3)
        
        # Gambar air (isi 75% tangki)
        water_fill = 0.75
        water_level = tank_y + int(tank_height * (1 - water_fill))
        water_height = int(tank_height * water_fill)
        pygame.draw.rect(screen, WATER_COLOR, (tank_x + 5, water_level, tank_width - 10, water_height))
        
        # Water surface line
        pygame.draw.line(screen, (0, 0, 150), (tank_x + 5, water_level), 
                        (tank_x + tank_width - 5, water_level), 2)
        
        # Objek (lebih besar)
        obj_size = max(50, min(90, int(v_disp * 600)))
        obj_x = tank_x + (tank_width - obj_size) // 2
        
        # Posisi objek
        verdict = rec.notes[0] if rec.notes else ""
        if "floats" in verdict:
            obj_y = water_level - obj_size + 10
        else:
            obj_y = water_level + (water_height - obj_size) // 2
        
        pygame.draw.rect(screen, (139, 69, 19), (obj_x, obj_y, obj_size, obj_size))
        pygame.draw.rect(screen, TEXT_COLOR, (obj_x, obj_y, obj_size, obj_size), 2)
        
        # Verdict (SHORT version, di atas tank, tengah)
        verdict_color = ARROW_UP if "floats" in verdict else (ARROW_DOWN if "sinks" in verdict else TEXT_COLOR)
        if "floats" in verdict:
            verdict_short = "FLOATS (F_B > W)"
        elif "sinks" in verdict:
            verdict_short = "SINKS (F_B < W)"
        else:
            verdict_short = "NEUTRAL"
        draw_text(screen, verdict_short, (WIDTH//2, 110), f=font, center=True, color=verdict_color)
        
        # Panah gaya (di samping tank, lebih jauh dari verdict)
        max_force = max(fb, w, 1.0)
        arrow_scale = 100 / max_force
        
        # Panah F_B (kiri tank, jauh dari verdict)
        fb_arrow_len = max(40, min(150, int(fb * arrow_scale)))
        arrow_left_x = tank_x - 150  # Lebih jauh ke kiri
        arrow_center_y = obj_y + obj_size // 2
        
        draw_arrow(screen, (arrow_left_x, arrow_center_y), 
                   (arrow_left_x, arrow_center_y - fb_arrow_len), ARROW_UP, 5)
        # Label di atas panah, lebih ke kiri
        draw_text(screen, f"F_B", (arrow_left_x - 40, arrow_center_y - fb_arrow_len - 30), 
                  f=small_font, color=ARROW_UP)
        draw_text(screen, f"{fb:.1f}N", (arrow_left_x - 40, arrow_center_y - fb_arrow_len - 12), 
                  f=small_font, color=ARROW_UP)
        
        # Panah W (kanan tank)
        w_arrow_len = max(40, min(150, int(w * arrow_scale)))
        arrow_right_x = tank_x + tank_width + 80  # Lebih jauh ke kanan
        
        draw_arrow(screen, (arrow_right_x, arrow_center_y), 
                   (arrow_right_x, arrow_center_y + w_arrow_len), ARROW_DOWN, 5)
        draw_text(screen, f"W", (arrow_right_x + 20, arrow_center_y + w_arrow_len + 10), 
                  f=small_font, color=ARROW_DOWN)
        draw_text(screen, f"{w:.1f}N", (arrow_right_x + 20, arrow_center_y + w_arrow_len + 28), 
                  f=small_font, color=ARROW_DOWN)
        
        # Info panel (kiri bawah, lebih tinggi untuk hindari overlap)
        panel_rect = pygame.Rect(50, 520, 320, 100)
        draw_panel(screen, panel_rect)
        
        info_lines = [
            f"Volume: {v_disp:.3f} m³    Mass: {m_obj:.1f} kg",
            f"F_B: {fb:.2f} N          W: {w:.2f} N"
        ]
        draw_text(screen, '\n'.join(info_lines), (panel_rect.x + 10, panel_rect.y + 10), f=small_font)
        
        draw_text(screen, "Controls: [UP/DOWN] Mass  [LEFT/RIGHT] Volume  [M] Menu  [ESC] Quit", 
                  (WIDTH//2, HEIGHT - 30), f=small_font, center=True)
        pygame.display.flip()
        pygame.time.Clock().tick(60)
    return True

# -----------------------------------------------------------------------------
# Demo 5: Hydrostatic Force
# -----------------------------------------------------------------------------
def demo_hydrostatic_force():
    h_top, height, width = 1.0, 3.0, 2.0
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: return False
                if event.key == pygame.K_m: return True
                if event.key == pygame.K_UP: h_top = max(0.0, h_top - 0.5)
                if event.key == pygame.K_DOWN: h_top = min(10.0, h_top + 0.5)
                if event.key == pygame.K_LEFT: height = max(0.5, height - 0.5)
                if event.key == pygame.K_RIGHT: height = min(10.0, height + 0.5)

        rec = problems.hydrostatic_force(backend, width=width, height=height, h_top=h_top)
        screen.fill(BG_COLOR)
        draw_text(screen, "HYDROSTATIC FORCE ON SURFACE", (WIDTH//2, 30), f=title_font, center=True)
        draw_text(screen, "F = ∫ p dA", (WIDTH//2, 70), f=font, center=True)
        
        surf_y = 150
        pygame.draw.line(screen, (0, 0, 200), (WIDTH//2 - 250, surf_y), (WIDTH//2 + 250, surf_y), 3)
        draw_text(screen, "Water Surface (y=0)", (WIDTH//2 + 260, surf_y - 10), f=small_font)
        
        max_depth = 15.0
        scale = 300 / max_depth
        plate_x = WIDTH//2
        plate_y = surf_y + int(h_top * scale)
        plate_h = int(height * scale)
        
        pygame.draw.rect(screen, (100, 100, 100), (plate_x - 10, plate_y, 20, plate_h))
        pygame.draw.rect(screen, TEXT_COLOR, (plate_x - 10, plate_y, 20, plate_h), 2)
        
        for i in range(11):
            frac = i / 10
            y = plate_y + int(frac * plate_h)
            depth = h_top + frac * height
            p = 1000 * 9.80665 * depth
            arrow_len = max(5, int((p / (1000 * 9.80665 * max_depth)) * 150))
            draw_arrow(screen, (plate_x + 15, y), (plate_x + 15 + arrow_len, y), (200, 0, 0), 2)
            
        panel_rect = pygame.Rect(50, 200, 350, 250)
        draw_panel(screen, panel_rect)
        f_num = rec.computed['numerical force'].value
        f_ana = (101325 + 1000 * 9.80665 * (h_top + height/2)) * (width * height)
        err = abs(f_num - f_ana)
        
        info = f"Geometry:      Vertical Rectangle\nWidth (w):     {width:.1f} m\nHeight (H):    {height:.1f} m\nTop Depth:     {h_top:.1f} m\n-------------------------------\nAnalytical F:  {f_ana:.2f} N\nNumerical F:   {f_num:.2f} N\nAbs Error:     {err:.2e} N"
        draw_text(screen, info, (panel_rect.x + 15, panel_rect.y + 15), f=small_font)
        
        draw_text(screen, "Controls: [UP/DOWN] Top Depth  [LEFT/RIGHT] Height  [M] Menu  [ESC] Quit", (WIDTH//2, HEIGHT - 40), f=small_font, center=True)
        pygame.display.flip()
        pygame.time.Clock().tick(60)
    return True

# -----------------------------------------------------------------------------
# Main Menu & CLI Entry Point
# -----------------------------------------------------------------------------
def main_menu():
    while True:
        screen.fill(BG_COLOR)
        draw_text(screen, "================================================", (WIDTH//2, 100), f=font, center=True)
        draw_text(screen, "BAGUS: FINE-FM", (WIDTH//2, 130), f=title_font, center=True)
        draw_text(screen, "Basically A Generally Useless Solver", (WIDTH//2, 170), f=font, center=True)
        draw_text(screen, "Fluid Idiot's Numerical Engine for Fluid Mechanics", (WIDTH//2, 200), f=font, center=True)
        draw_text(screen, "================================================", (WIDTH//2, 230), f=font, center=True)
        
        menu_text = "\n[1] Water in a Bucket\n[2] Hydrostatic Pressure\n[3] Pascal Hydraulic System\n[4] Buoyancy\n[5] Hydrostatic Force\n\n[ESC] Quit"
        draw_text(screen, menu_text, (WIDTH//2, 300), f=font, center=True)
        pygame.display.flip()
        
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: return False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE: return False
                    demos = {pygame.K_1: demo_bucket, pygame.K_2: demo_hydrostatic, 
                             pygame.K_3: demo_pascal, pygame.K_4: demo_buoyancy, 
                             pygame.K_5: demo_hydrostatic_force}
                    if event.key in demos:
                        if not demos[event.key](): return False
                        waiting = False
            pygame.time.Clock().tick(30)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BAGUS: FINE-FM Pygame Visualization")
    parser.add_argument("--demo", type=int, choices=[1, 2, 3, 4, 5], help="Run a specific demo")
    parser.add_argument("--all", "--showcase", action="store_true", help="Run all demos in sequence")
    args = parser.parse_args()
    
    if args.demo:
        demos = {1: demo_bucket, 2: demo_hydrostatic, 3: demo_pascal, 4: demo_buoyancy, 5: demo_hydrostatic_force}
        demos[args.demo]()
    elif args.all:
        for d in [demo_bucket, demo_hydrostatic, demo_pascal, demo_buoyancy, demo_hydrostatic_force]:
            if not d(): break
    else:
        main_menu()
        
    pygame.quit()
    sys.exit(0)