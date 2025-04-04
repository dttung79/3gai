import pygame
import math
import sys

# --- Khởi tạo Pygame ---
pygame.init()

# --- Hằng số ---
WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GRAY = (200, 200, 200)
FPS = 60 # Khung hình trên giây

# --- Cài đặt màn hình ---
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mô phỏng Con lắc đơn Tắt dần")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36) # Font chữ để hiển thị thông tin

# --- Thông số con lắc ---
pivot_pos = (WIDTH // 2, 100) # Vị trí điểm treo
length = 250          # Chiều dài dây treo (pixels)
bob_radius = 20       # Bán kính vật nặng
gravity = 9.81        # Gia tốc trọng trường (mô phỏng) - điều chỉnh để có tốc độ hợp lý
damping = 0.998       # Hệ số tắt dần (nhỏ hơn 1 để dao động giảm dần) - càng gần 1 càng lâu tắt
angle_deg = 0.0       # Góc ban đầu (độ)
angle_rad = math.radians(angle_deg) # Góc ban đầu (radian)
angular_velocity = 0.0 # Vận tốc góc ban đầu
angular_acceleration = 0.0 # Gia tốc góc ban đầu
max_angle_achieved_deg = 0.0 # Góc lớn nhất đạt được (sẽ cập nhật)

# --- Trạng thái mô phỏng ---
is_swinging = False  # Ban đầu con lắc đứng yên, chờ người dùng kéo
stop_threshold_angle = 0.1  # Ngưỡng góc (độ) để coi là dừng
stop_threshold_velocity = 0.01 # Ngưỡng vận tốc góc để coi là dừng

# --- Biến phụ trợ theo dõi đỉnh dao động ---
previous_velocity_sign = 0

# --- Hàm vẽ con lắc ---
def draw_pendulum(surface, angle):
    # Tính toán vị trí vật nặng (x, y)
    x = pivot_pos[0] + length * math.sin(angle)
    y = pivot_pos[1] + length * math.cos(angle)

    # Vẽ dây treo
    pygame.draw.line(surface, BLACK, pivot_pos, (int(x), int(y)), 2)
    # Vẽ điểm treo
    pygame.draw.circle(surface, GRAY, pivot_pos, 5)
    # Vẽ vật nặng
    pygame.draw.circle(surface, RED, (int(x), int(y)), bob_radius)

# --- Hàm hiển thị thông tin ---
def display_info(surface):
    # Hiển thị góc hiện tại
    angle_text = font.render(f"Góc: {math.degrees(angle_rad):.2f}°", True, BLACK)
    surface.blit(angle_text, (10, 10))

    # Hiển thị vận tốc góc (có thể ẩn nếu không cần)
    vel_text = font.render(f"Vận tốc góc: {angular_velocity:.2f} rad/s", True, BLACK)
    surface.blit(vel_text, (10, 50))

    # Hiển thị góc lớn nhất đạt được
    max_angle_text = font.render(f"Góc cực đại: {max_angle_achieved_deg:.2f}°", True, BLACK)
    surface.blit(max_angle_text, (10, 90))

    # Hiển thị hướng dẫn
    if not is_swinging:
        instruction_text = font.render("Dùng mũi tên Trái/Phải để kéo. Nhấn SPACE để thả.", True, BLACK)
        screen.blit(instruction_text, (WIDTH // 2 - instruction_text.get_width() // 2, HEIGHT - 50))
    else:
        instruction_text = font.render("Nhấn R để Reset.", True, BLACK) 
        screen.blit(instruction_text, (WIDTH // 2 - instruction_text.get_width() // 2, HEIGHT - 50))


# --- Vòng lặp chính ---
running = True
while running:
    # --- Xử lý sự kiện ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if not is_swinging: # Chỉ cho phép kéo khi chưa dao động
                if event.key == pygame.K_LEFT:
                    angle_deg -= 2.0 # Giảm góc 2 độ mỗi lần nhấn
                    angle_deg = max(-85.0, angle_deg) # Giới hạn góc kéo
                    angle_rad = math.radians(angle_deg)
                    max_angle_achieved_deg = abs(angle_deg) # Cập nhật góc max ban đầu
                elif event.key == pygame.K_RIGHT:
                    angle_deg += 2.0 # Tăng góc 2 độ
                    angle_deg = min(85.0, angle_deg) # Giới hạn góc kéo
                    angle_rad = math.radians(angle_deg)
                    max_angle_achieved_deg = abs(angle_deg) # Cập nhật góc max ban đầu
                elif event.key == pygame.K_SPACE:
                    is_swinging = True
                    angular_velocity = 0.0 # Đảm bảo vận tốc ban đầu là 0 khi thả
                    angular_acceleration = 0.0
                    previous_velocity_sign = 0 # Reset theo dõi đỉnh
                    # max_angle_achieved_deg đã được set khi kéo
            else: # Khi đang dao động
                if event.key == pygame.K_r: # Nhấn R để Reset
                    is_swinging = False
                    angle_deg = 0.0
                    angle_rad = math.radians(angle_deg)
                    angular_velocity = 0.0
                    angular_acceleration = 0.0
                    max_angle_achieved_deg = 0.0
                    previous_velocity_sign = 0


    # --- Cập nhật trạng thái (Physics) ---
    if is_swinging:
        # Tính thời gian trôi qua mỗi khung hình (delta time)
        dt = clock.tick(FPS) / 1000.0 # Chuyển mili giây sang giây
        if dt > 0.1: dt = 0.1 # Giới hạn dt để tránh lỗi khi cửa sổ bị treo

        # Công thức tính gia tốc góc của con lắc đơn (có thể thêm lực cản phức tạp hơn)
        # angular_acceleration = -(gravity / length) * math.sin(angle_rad)
        # Đơn giản hóa công thức khi có tắt dần:
        # 1. Tính gia tốc do trọng lực
        accel_gravity = -(gravity / (length / 10.0)) * math.sin(angle_rad) # Chia length cho 10 để trông "thật" hơn với pixel

        # 2. Cập nhật vận tốc góc (Euler integration)
        angular_velocity += accel_gravity * dt

        # 3. Áp dụng hệ số tắt dần vào vận tốc
        angular_velocity *= damping

        # 4. Cập nhật góc (Euler integration)
        angle_rad += angular_velocity * dt

        # --- Cập nhật góc cực đại ---
        current_velocity_sign = math.copysign(1, angular_velocity) if angular_velocity != 0 else 0
        # Kiểm tra nếu vận tốc đổi dấu (vượt qua điểm cực đại/cực tiểu)
        # và vận tốc không quá gần 0 (tránh cập nhật liên tục khi gần dừng)
        if previous_velocity_sign != 0 and current_velocity_sign != previous_velocity_sign and abs(angular_velocity) > stop_threshold_velocity:
            max_angle_achieved_deg = abs(math.degrees(angle_rad)) # Cập nhật góc cực đại mới

        # Cập nhật dấu vận tốc trước đó
        if current_velocity_sign != 0 : # Chỉ cập nhật nếu có vận tốc
            previous_velocity_sign = current_velocity_sign

        # --- Kiểm tra điều kiện dừng ---
        if abs(math.degrees(angle_rad)) < stop_threshold_angle and abs(angular_velocity) < stop_threshold_velocity:
            # Dừng hẳn khi góc và vận tốc đủ nhỏ
            is_swinging = False
            angle_rad = 0.0 # Đặt về đúng vị trí cân bằng
            angular_velocity = 0.0
            angular_acceleration = 0.0
            max_angle_achieved_deg = 0.0 # Reset góc max khi dừng hẳn
            print("Pendulum stopped.") # In ra console khi dừng (tùy chọn)

    else: # Nếu không dao động (đang thiết lập hoặc đã dừng)
        # Giữ nguyên trạng thái hoặc vị trí thiết lập
        angle_rad = math.radians(angle_deg)
        angular_velocity = 0.0
        angular_acceleration = 0.0
        # Đảm bảo clock.tick vẫn được gọi để duy trì FPS và xử lý sự kiện mượt mà
        clock.tick(FPS)


    # --- Vẽ lên màn hình ---
    screen.fill(WHITE) # Xóa màn hình bằng màu trắng
    draw_pendulum(screen, angle_rad)
    display_info(screen)

    # --- Cập nhật màn hình ---
    pygame.display.flip()

# --- Kết thúc Pygame ---
pygame.quit()
sys.exit()