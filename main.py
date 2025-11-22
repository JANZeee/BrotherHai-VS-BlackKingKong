import pygame
import sys
import random
import time

# --- 配置与常量 ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# 颜色定义 (RGB)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
RED = (220, 50, 50)
GREEN = (50, 220, 50)
BLUE = (50, 50, 220)
YELLOW = (255, 220, 0)
TATAMI_COLOR = (245, 245, 220)  # 米色背景
TATAMI_LINE = (200, 200, 180)
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER = (100, 160, 210)


# --- 辅助类：按钮 ---
class Button:
    def __init__(self, text, x, y, width, height, font, callback, bg_color=BUTTON_COLOR):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.callback = callback
        self.bg_color = bg_color
        self.hovered = False

    def draw(self, surface):
        color = BUTTON_HOVER if self.hovered else self.bg_color
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=10)

        text_surf = self.font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def check_hover(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.hovered:
            if self.callback:
                self.callback()


# --- 核心类：格斗家 (角色) ---
class Fighter:
    def __init__(self, name, is_player, max_hp, color):
        self.name = name
        self.is_player = is_player
        self.max_hp = max_hp
        self.current_hp = max_hp
        self.color = color  # 皮肤颜色
        self.pants_color = BLUE if is_player else BLACK

        # 状态
        self.is_defending = False
        self.is_dead = False

        # 动画相关
        self.shake_timer = 0
        self.start_pos_x = 150 if is_player else 650
        self.y = 300

    def take_damage(self, amount):
        if self.is_defending:
            amount = int(amount * 0.5)  # 防御减半伤害

        self.current_hp -= amount
        if self.current_hp <= 0:
            self.current_hp = 0
            self.is_dead = True

        # 触发受伤震动动画
        self.shake_timer = 10
        return amount

    def heal(self, amount):
        self.current_hp += amount
        if self.current_hp > self.max_hp:
            self.current_hp = self.max_hp

    def draw(self, surface):
        # 计算震动偏移
        offset_x = 0
        if self.shake_timer > 0:
            offset_x = random.randint(-5, 5)
            self.shake_timer -= 1

        cx = self.start_pos_x + offset_x
        cy = self.y

        # --- 简单的几何图形绘制角色 ---
        # 1. 身体 (圆角矩形) - 肌肉感
        body_rect = pygame.Rect(cx - 40, cy - 60, 80, 100)
        pygame.draw.rect(surface, self.color, body_rect, border_radius=10)

        # 2. 头部 (圆形)
        pygame.draw.circle(surface, self.color, (cx, cy - 80), 30)

        # 3. 表情 (简单线条)
        eye_y = cy - 85
        pygame.draw.circle(surface, BLACK, (cx - 10, eye_y), 3)
        pygame.draw.circle(surface, BLACK, (cx + 10, eye_y), 3)
        # 嘴巴
        if self.is_dead:
            pygame.draw.line(surface, BLACK, (cx - 5, cy - 70), (cx + 5, cy - 70), 2)  # 死鱼眼/平嘴
        else:
            pygame.draw.arc(surface, BLACK, (cx - 10, cy - 75, 20, 10), 3.14, 0, 2)  # 微笑

        # 4. 手臂 (简单的椭圆表示肌肉)
        pygame.draw.ellipse(surface, self.color, (cx - 70, cy - 60, 30, 60))  # 左臂
        pygame.draw.ellipse(surface, self.color, (cx + 40, cy - 60, 30, 60))  # 右臂
        # 拳头
        pygame.draw.circle(surface, self.color, (cx - 55, cy - 10), 15)
        pygame.draw.circle(surface, self.color, (cx + 55, cy - 10), 15)

        # 5. 短裤
        pants_rect = pygame.Rect(cx - 42, cy + 10, 84, 50)
        pygame.draw.rect(surface, self.pants_color, pants_rect, border_radius=5)

        # 6. 腿
        pygame.draw.rect(surface, self.color, (cx - 30, cy + 60, 20, 60))  # 左腿
        pygame.draw.rect(surface, self.color, (cx + 10, cy + 60, 20, 60))  # 右腿

        # --- 防御状态标识 ---
        if self.is_defending:
            shield_rect = pygame.Rect(cx - 50, cy - 90, 100, 220)
            pygame.draw.rect(surface, (100, 200, 255), shield_rect, 3, border_radius=15)

        # --- 血条 ---
        bar_width = 150
        bar_height = 20
        ratio = self.current_hp / self.max_hp

        bar_x = cx - bar_width // 2
        bar_y = cy - 130

        # 血条背景
        pygame.draw.rect(surface, GRAY, (bar_x, bar_y, bar_width, bar_height))
        # 血量
        color_hp = GREEN if ratio > 0.5 else (YELLOW if ratio > 0.2 else RED)
        pygame.draw.rect(surface, color_hp, (bar_x, bar_y, bar_width * ratio, bar_height))
        # 边框
        pygame.draw.rect(surface, BLACK, (bar_x, bar_y, bar_width, bar_height), 2)


# --- 游戏主逻辑类 ---
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("海哥大战黑金刚")
        self.clock = pygame.time.Clock()

        # 尝试加载中文字体，如果失败则使用系统默认
        self.font_path = None
        possible_fonts = ["SimHei", "Microsoft YaHei", "PingFang SC", "Arial Unicode MS"]
        for f in possible_fonts:
            try:
                self.font_path = pygame.font.match_font(f)
                if self.font_path: break
            except:
                pass

        self.title_font = pygame.font.Font(self.font_path, 60) if self.font_path else pygame.font.SysFont(None, 60)
        self.ui_font = pygame.font.Font(self.font_path, 24) if self.font_path else pygame.font.SysFont(None, 24)

        self.state = "MENU"  # MENU, BATTLE, GAMEOVER
        self.turn_count = 1
        self.combat_log = []
        self.max_log_lines = 5

        # 初始化角色
        self.init_characters()

        # 初始化按钮
        self.init_menu_buttons()
        self.init_battle_buttons()
        self.init_gameover_buttons()

        self.ai_action_timer = 0  # AI 思考延迟

    def init_characters(self):
        # 角色重置
        # 海哥：肉色皮肤
        self.player = Fighter("海哥", True, 100, (255, 200, 180))
        # 黑金刚：深色皮肤
        self.enemy = Fighter("黑金刚", False, 120, (100, 70, 50))
        self.turn_owner = "PLAYER"  # PLAYER or ENEMY
        self.turn_count = 1
        self.combat_log = ["战斗开始！海哥 VS 黑金刚"]

    def log(self, text):
        self.combat_log.append(text)
        if len(self.combat_log) > self.max_log_lines:
            self.combat_log.pop(0)

    # --- 按钮回调函数 ---
    def start_game(self):
        self.init_characters()
        self.state = "BATTLE"

    def exit_game(self):
        pygame.quit()
        sys.exit()

    def return_menu(self):
        self.state = "MENU"

    # --- 战斗动作 ---
    def player_attack(self, type):
        if self.turn_owner != "PLAYER": return

        dmg = 0
        if type == "NORMAL":
            # 普通攻击：命中率 95%，伤害 10-15
            if random.random() < 0.95:
                dmg = random.randint(10, 15)
                real_dmg = self.enemy.take_damage(dmg)
                self.log(f"海哥使用王八拳！黑金刚受到 {real_dmg} 点伤害。")
            else:
                self.log("海哥一拳挥空了！好尴尬。")

        elif type == "HEAVY":
            # 重击：命中率 70%，伤害 20-30
            if random.random() < 0.70:
                dmg = random.randint(20, 30)
                real_dmg = self.enemy.take_damage(dmg)
                self.log(f"海哥使用泰山压顶！黑金刚受到 {real_dmg} 点暴击伤害！")
            else:
                self.log("海哥用力过猛摔倒了，攻击失效！")

        self.end_player_turn()

    def player_defend(self):
        if self.turn_owner != "PLAYER": return
        self.player.is_defending = True
        self.log("海哥抱头蹲防，准备承受冲击。")
        self.end_player_turn()

    def end_player_turn(self):
        if self.check_game_over(): return
        self.turn_owner = "ENEMY"
        self.ai_action_timer = pygame.time.get_ticks() + 1000  # AI 思考 1 秒

    # --- AI 逻辑 ---
    def ai_turn(self):
        # 解除 AI 上回合的防御
        self.enemy.is_defending = False

        action = random.choice(["NORMAL", "NORMAL", "HEAVY", "DEFEND"])

        if action == "NORMAL":
            dmg = random.randint(8, 14)
            real_dmg = self.player.take_damage(dmg)
            self.log(f"黑金刚猛推海哥！海哥受到 {real_dmg} 点伤害。")

        elif action == "HEAVY":
            if random.random() < 0.6:  # AI 重击命中率稍低
                dmg = random.randint(18, 25)
                real_dmg = self.player.take_damage(dmg)
                self.log(f"黑金刚使出野蛮冲撞！海哥受到 {real_dmg} 点重伤！")
            else:
                self.log("黑金刚冲过头了，海哥躲过一劫。")

        elif action == "DEFEND":
            self.enemy.is_defending = True
            self.log("黑金刚展示肌肉，进入防御姿态。")

        if not self.check_game_over():
            self.turn_owner = "PLAYER"
            self.player.is_defending = False  # 解除玩家防御
            self.turn_count += 1

    def check_game_over(self):
        if self.enemy.is_dead:
            self.log("黑金刚倒下了！海哥获胜！")
            self.state = "GAMEOVER"
            self.game_result = "VICTORY"
            return True
        if self.player.is_dead:
            self.log("海哥没力气了... 游戏结束。")
            self.state = "GAMEOVER"
            self.game_result = "DEFEAT"
            return True
        return False

    # --- 初始化各界面按钮 ---
    def init_menu_buttons(self):
        cx = SCREEN_WIDTH // 2
        self.btn_start = Button("开始游戏", cx - 100, 300, 200, 50, self.ui_font, self.start_game)
        self.btn_exit = Button("退出游戏", cx - 100, 380, 200, 50, self.ui_font, self.exit_game)

    def init_battle_buttons(self):
        y_pos = 500
        w = 120
        gap = 20
        start_x = (SCREEN_WIDTH - (3 * w + 2 * gap)) // 2

        self.btn_atk = Button("普通攻击", start_x, y_pos, w, 50, self.ui_font, lambda: self.player_attack("NORMAL"))
        self.btn_hvy = Button("蓄力重击", start_x + w + gap, y_pos, w, 50, self.ui_font,
                              lambda: self.player_attack("HEAVY"), bg_color=(200, 100, 50))
        self.btn_def = Button("防御", start_x + 2 * (w + gap), y_pos, w, 50, self.ui_font, self.player_defend,
                              bg_color=(100, 180, 100))

        self.battle_buttons = [self.btn_atk, self.btn_hvy, self.btn_def]

    def init_gameover_buttons(self):
        cx = SCREEN_WIDTH // 2
        self.btn_retry = Button("再来一局", cx - 100, 350, 200, 50, self.ui_font, self.start_game)
        self.btn_menu = Button("返回主菜单", cx - 100, 430, 200, 50, self.ui_font, self.return_menu)

    # --- 绘图与更新 ---
    def draw_background(self):
        self.screen.fill(TATAMI_COLOR)
        # 画一些榻榻米的线条
        for i in range(0, SCREEN_HEIGHT, 100):
            pygame.draw.line(self.screen, TATAMI_LINE, (0, i), (SCREEN_WIDTH, i), 3)
        pygame.draw.line(self.screen, TATAMI_LINE, (SCREEN_WIDTH // 2, 0), (SCREEN_WIDTH // 2, SCREEN_HEIGHT), 5)

    def run(self):
        while True:
            mouse_pos = pygame.mouse.get_pos()

            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.exit_game()

                if self.state == "MENU":
                    self.btn_start.handle_event(event)
                    self.btn_exit.handle_event(event)
                elif self.state == "BATTLE":
                    if self.turn_owner == "PLAYER":
                        for btn in self.battle_buttons:
                            btn.handle_event(event)
                elif self.state == "GAMEOVER":
                    self.btn_retry.handle_event(event)
                    self.btn_menu.handle_event(event)

            # 逻辑更新 & 渲染
            self.draw_background()

            if self.state == "MENU":
                title = self.title_font.render("海哥大战黑金刚", True, BLACK)
                title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
                self.screen.blit(title, title_rect)

                self.btn_start.check_hover(mouse_pos)
                self.btn_start.draw(self.screen)
                self.btn_exit.check_hover(mouse_pos)
                self.btn_exit.draw(self.screen)

            elif self.state == "BATTLE":
                # AI 逻辑处理
                if self.turn_owner == "ENEMY" and not self.enemy.is_dead and not self.player.is_dead:
                    if pygame.time.get_ticks() > self.ai_action_timer:
                        self.ai_turn()

                # 绘制角色
                self.player.draw(self.screen)
                self.enemy.draw(self.screen)

                # 绘制UI信息
                turn_text = self.ui_font.render(f"第 {self.turn_count} 回合", True, BLACK)
                self.screen.blit(turn_text, (20, 20))

                # 绘制战斗日志
                log_y = 400
                for line in self.combat_log:
                    txt = self.ui_font.render(line, True, (50, 50, 50))
                    txt_rect = txt.get_rect(center=(SCREEN_WIDTH // 2, log_y))
                    self.screen.blit(txt, txt_rect)
                    log_y += 25

                # 玩家操作按钮
                if self.turn_owner == "PLAYER":
                    for btn in self.battle_buttons:
                        btn.check_hover(mouse_pos)
                        btn.draw(self.screen)
                else:
                    # 敌方回合提示
                    wait_text = self.ui_font.render("黑金刚正在思考...", True, RED)
                    wait_rect = wait_text.get_rect(center=(SCREEN_WIDTH // 2, 525))
                    self.screen.blit(wait_text, wait_rect)

            elif self.state == "GAMEOVER":
                result_text = "胜利！" if self.game_result == "VICTORY" else "失败..."
                color = RED if self.game_result == "VICTORY" else BLUE
                res_surf = self.title_font.render(result_text, True, color)
                res_rect = res_surf.get_rect(center=(SCREEN_WIDTH // 2, 200))
                self.screen.blit(res_surf, res_rect)

                if self.game_result == "VICTORY":
                    msg = "海哥不仅赢了，还保持了发型！"
                else:
                    msg = "海哥被黑金刚压制了，下次再战！"

                msg_surf = self.ui_font.render(msg, True, BLACK)
                msg_rect = msg_surf.get_rect(center=(SCREEN_WIDTH // 2, 280))
                self.screen.blit(msg_surf, msg_rect)

                self.btn_retry.check_hover(mouse_pos)
                self.btn_retry.draw(self.screen)
                self.btn_menu.check_hover(mouse_pos)
                self.btn_menu.draw(self.screen)

            pygame.display.flip()
            self.clock.tick(FPS)


if __name__ == "__main__":
    game = Game()
    game.run()