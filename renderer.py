import mazegenerator
import pygame
from itertools import cycle
import random
import os
import sys
import json
from pydantic import BaseModel, ValidationError, field_validator


class Gameconfig(BaseModel):
    width: int
    height: int
    entry: tuple[int, int]
    output_file: str
    perfect: bool
    color_wall: tuple[int, int, int]
    color_fond: tuple[int, int, int]
    high_score_filename: str
    point_per_pacgum: int
    nombre_de_pacgums: int

    @field_validator('entry', 'color_wall', 'color_fond', mode='before')
    @classmethod
    def parsing_tuple(config_de_jeu, valeur):
        if isinstance(valeur, str):
            try:
                return eval(valeur)
            except (ValueError, SyntaxError):
                raise ValueError(
                    f"Le format du texte '{valeur}' ne peut pas être converti en tuple.")
        return valeur


class render():
    def __init__(self):
        self.config_brute = self.configjson()
        self.extract_config()
        self.hauteur_hud = 50
        self.largeur_fenetre = 0
        self.hauteur_fenetre = 0
        self.new_maze(1)
        self.size_cel = self.cell_and_windows_size(self.mazze)
        self.ecran = pygame.display.set_mode(
            (self.largeur_fenetre, self.hauteur_hud + self.hauteur_fenetre))
        self.fenetre = self.ecran.subsurface(
            (0, self.hauteur_hud, self.largeur_fenetre, self.hauteur_fenetre))
        self.police = pygame.font.Font(None, 25)

    def draw_hud(self, play, rest_time, mode_triche):
        self.ecran.fill(self.color_fond,
                        (0, 0, self.largeur_fenetre, self.hauteur_hud))
        image = self.police.render(
            "Vies : " + str(play.vies), True, (255, 255, 255))
        self.ecran.blit(image, (10, 10))
        image = self.police.render(
            "Score : " + str(play.score), True, (255, 255, 255))
        self.ecran.blit(image, (112, 10))
        image = self.police.render(
            "Niveau : " + str(play.level), True, (255, 255, 255))
        self.ecran.blit(image, (225, 10))
        image = self.police.render(
            "Temps : " + str(rest_time), True, (255, 255, 255))
        self.ecran.blit(image, (340, 10))
        if mode_triche:
            retour = self.police.render("CHEAT", True, (255,0,0))
            self.ecran.blit(retour, (450,10))

    def configjson(self):
        if len(sys.argv) < 2:
            print("ERRREUR PARSING AJOUTE CONFIG.JSON")
            sys.exit(1)
        config = sys.argv[1]

        try:
            with open(config, "r", encoding='utf-8') as fichier:
                config = json.load(fichier)
                return config
        except FileNotFoundError:
            print(f"ERREUR LE ficher {config} EST INTROUVABLE")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Erreur : Le fichier '{config}' n'est pas un JSON valide.")
            sys.exit(1)

    def extract_config(self):
        try:
            config_valid = Gameconfig(**self.config_brute)
            self.width = config_valid.width
            self.height = config_valid.height
            self.entry = config_valid.entry
            self.output_file = config_valid.output_file
            self.perfect = config_valid.perfect
            self.color_wall = config_valid.color_wall
            self.color_fond = config_valid.color_fond
            self.hight_score = config_valid.high_score_filename
            self.pont_per_pacgum = config_valid.point_per_pacgum
            self.nombre_de_pacgums = config_valid.nombre_de_pacgums
        except ValidationError as e:
            print("ERREUR CONFIG")
            print(e)
            raise e

    # def extract_color(self, color: tuple) -> list[int]:
    #     new = []
    #     color = color.strip("(")
    #     color = color.strip(")")
    #     new = color.split(",")
    #     return tuple(int(morceu.strip()) for morceu in new)

    def check_bits(self, de: int) -> dict:
        result = {
            "nord": False,
            "sud": False,
            "est": False,
            "ouest": False
        }
        if de & 1:
            result["nord"] = True
        if de & 2:
            result["est"] = True
        if de & 4:
            result["sud"] = True
        if de & 8:
            result["ouest"] = True
        return result

    def cell_and_windows_size(self, mazze: list[list[int]]) -> int:
        largueur = int(self.width)
        hauteur = int(self.height) - self.hauteur_hud
        size_cell_largeur = largueur // len(mazze[0])
        size_cel_hauteur = hauteur // len(mazze)
        if size_cel_hauteur >= size_cell_largeur:
            size_cell_final = size_cell_largeur
        else:
            size_cell_final = size_cel_hauteur
        self.largeur_fenetre = int(len(mazze[0]) * size_cell_final)
        self.hauteur_fenetre = int(len(mazze) * size_cell_final)
        return size_cell_final

    def cell_to_pixel(self, cordonne: tuple[int, int]) -> None:
        row, col = cordonne
        self.size_cel = self.cell_and_windows_size(self.mazze)
        y = row * self.size_cel
        x = col * self.size_cel
        direction = self.check_bits(self.mazze[row][col])
        return (x, y, direction)

    def wall_bands(self):
        w = self.wall_epaisseur
        c = self.size_cel
        return {
            "nord": (0, 0, c, w),
            "sud": (0, c - w, c, w),
            "est": (c - w, 0, w, c),
            "ouest": (0, 0, w, c),
        }

    def draw(self, fenetre, x, y, largeur, hauteur, couleur):
        for dy in range(hauteur):
            for dx in range(largeur):
                fenetre.set_at((x + dx, y + dy), couleur)
        return fenetre

    def cremaze(self):
        self.wall_epaisseur = 1
        # self.color_fond = self.extract_color(self.color_fond)
        # self.color_wall = self.extract_color(self.color_wall)
        self.color_fond = self.color_fond
        self.color_wall = self.color_wall
        self.fenetre.fill(self.color_fond)
        bande_mur = self.wall_bands()
        for row in range(len(self.mazze)):
            for col in range(len(self.mazze[row])):
                x, y, direction = self.cell_to_pixel((row, col))
                if self.mazze[row][col] == 15:
                    self.draw(self.fenetre, x, y, self.size_cel,
                              self.size_cel, self.color_wall)
                    continue
                for key, valus in direction.items():
                    if valus is True:
                        xloca, yloca, c, w = bande_mur[key]
                        y_final = y + yloca
                        x_final = x + xloca
                        self.fenetre = self.draw(self.fenetre,
                                                 x_final, y_final,
                                                 c, w, self.color_wall)

    def new_maze(self, level):
        maze = mazegenerator.MazeGenerator()
        if level == 1:
            maze.generate(42)
        else:
            maze.generate(0)
        self.mazze = maze.maze


class Player():
    def __init__(self, size_cel, row, col, direction_de_depart, point_per_pacgums):
        self.score = 0
        self.vies = 3
        self.level = 1
        self.row = row
        self.col = col
        self.base_row = row
        self.base_col = col
        self.cel_size = size_cel
        self.direction = direction_de_depart
        self.next_direction = direction_de_depart
        self.point_per_pacgums = point_per_pacgums

        self.pacman_bouche_fermer = pygame.image.load("pacman_fermer.png")
        self.pacman_bouche_fermer = pygame.transform.scale(
            self.pacman_bouche_fermer, (self.cel_size / 2, self.cel_size / 2))
        self.pacman_bouche_semiouvert = pygame.image.load(
            "pacman_semi_ouvert.png")
        self.pacman_bouche_semiouvert = pygame.transform.scale(
            self.pacman_bouche_semiouvert, (self.cel_size / 2, self.cel_size / 2))
        self.pacman_bouche_ouvert = pygame.image.load("pacman_ouvert.png")
        self.pacman_bouche_ouvert = pygame.transform.scale(
            self.pacman_bouche_ouvert, (self.cel_size / 2,
                                        self.cel_size / 2))
        self.list_position = [self.pacman_bouche_semiouvert,
                              self.pacman_bouche_semiouvert,
                              self.pacman_bouche_fermer,
                              self.pacman_bouche_fermer,
                              self.pacman_bouche_semiouvert,
                              self.pacman_bouche_semiouvert,
                              self.pacman_bouche_ouvert,
                              self.pacman_bouche_ouvert]
        self.cycle = cycle(self.list_position)
        self.decelage = ((self.cel_size - self.cel_size / 2) / 2)

        pacgums = pygame.image.load("pacgums.png")
        self.size_pacgums = self.cel_size // 6
        self.size_super = self.cel_size // 2
        self.pacgums = pygame.transform.scale(
            pacgums, (self.size_pacgums, self.size_pacgums))
        self.lis_pacgums = []
        self.lis_superpacgums = []
        self.nombre_pacgums_manger = 0
        super_pacgums = pygame.image.load("pacgums.png")
        self.ubuntu_logo = pygame.transform.scale(super_pacgums,
                                                  (self.size_super,
                                                   self.size_super))

    def at_center(self):
        return (abs(self.row - round(self.row)) < 0.001 and
                abs(self.col - round(self.col)) < 0.001)

    def update(self, maze, check_bits):
        if self.at_center():
            self.row = round(self.row)
            self.col = round(self.col)
            murs = check_bits(maze[self.row][self.col])
            if not murs[self.next_direction]:
                self.direction = self.next_direction
            if murs[self.direction]:
                return
        self.deplacement()

    def check_wall(self, maze):
        list = re.check_bits(maze[(self.row)][(self.col)])
        if list["nord"] is False and self.direction == "nord":
            return True
        if list["sud"] is False and self.direction == "sud":
            return True
        if list["ouest"] is False and self.direction == "ouest":
            return True
        if list["est"] is False and self.direction == "est":
            return True
        return False

    def rotate(self):
        if self.direction == "sud":
            image = pygame.transform.rotate(next(self.cycle), 270)
        elif self.direction == "nord":
            image = pygame.transform.rotate(next(self.cycle), 90)
        elif self.direction == "ouest":
            image = pygame.transform.rotate(next(self.cycle), 180)
        elif self.direction == "est":
            image = pygame.transform.rotate(next(self.cycle), 0)
        else:
            image = next(self.cycle)
        return image

    def draw_player(self, fenetre):
        y = self.row * self.cel_size
        x = self.col * self.cel_size
        y += self.decelage
        x += self.decelage
        image = self.rotate()
        fenetre.blit(image, (x, y))

    def deplacement(self):
        if self.direction == "sud":
            self.row += 0.05
        elif self.direction == "nord":
            self.row -= 0.05
        elif self.direction == "ouest":
            self.col -= 0.05
        elif self.direction == "est":
            self.col += 0.05

    def direction_deplacement(self, direction):
        if direction == pygame.K_UP:
            self.next_direction = "nord"
        elif direction == pygame.K_DOWN:
            self.next_direction = "sud"
        elif direction == pygame.K_LEFT:
            self.next_direction = "ouest"
        elif direction == pygame.K_RIGHT:
            self.next_direction = "est"

    def ajoute_super(self, maze: list[list[int]]):
        tailley = len(maze[0]) - 1
        taillex = len(maze) - 1
        self.lis_superpacgums.append((0, 0))
        self.lis_superpacgums.append((0, tailley))
        self.lis_superpacgums.append((taillex, 0))
        self.lis_superpacgums.append((taillex, tailley))

    def afficher_superpacgums(self, fenetre):
        for row, col in self.lis_superpacgums:
            x = col * self.cel_size
            y = row * self.cel_size
            self.decalge = (self.cel_size - self.size_super) / 2
            fenetre.blit(self.ubuntu_logo,
                         (x + self.decalge, y + self.decalge))

    def ajoute_pacgums(self, fenetre, maze: list[list[int]],
                       case: tuple[int, int], pixel):
        if ((case[0], case[1]) not in self.lis_pacgums and maze[case[0]][case[1]] < 15):
            self.lis_pacgums.append((case[0], case[1]))
            fenetre.blit(self.pacgums, (pixel[0], pixel[1]))
            return True
        return False

    def place_pacgums(self, fenetre, nombre, mazze):
        tailley = len(mazze[0])
        taillex = len(mazze)

        while len(self.lis_pacgums) < nombre:
            row = random.randint(0, taillex - 1)
            col = random.randint(0, tailley - 1)
            self.ajoute_pacgums(fenetre, mazze, (row, col),
                                (col * self.cel_size, row * self.cel_size))

    def afficher_pacgums(self, fenetre):
        for row, col in self.lis_pacgums:
            x = col * self.cel_size
            y = row * self.cel_size
            self.decalge = (self.cel_size - self.size_pacgums) / 2
            fenetre.blit(self.pacgums, (x + self.decalge, y + self.decalge))

    def sup_pacgums(self) -> bool:
        position_pacman = (round(self.row), round(self.col))
        if position_pacman in self.lis_pacgums:
            self.lis_pacgums.remove(position_pacman)
            self.nombre_pacgums_manger += 1
            self.score += self.point_per_pacgums
        if position_pacman in self.lis_superpacgums:
            self.score += 50
            self.lis_superpacgums.remove(position_pacman)
            return True
        return False


class Phantom():
    def __init__(self, row, col, cel_size, image, vitesse):
        self.eat = False
        self.end_eat = 0
        self.phantom_scare = pygame.image.load("image_phantom/vulnerable.png")
        self.vulnerable = False
        self.ralenti = False
        self.fin_vulnerable = 0
        self.row = row
        self.vitesse = vitesse
        self.col = col
        self.base_row = row
        self.base_col = col
        self.cel_size = cel_size

        self.phantom_scare = pygame.transform.scale(
            self.phantom_scare, (self.cel_size // 2, self.cel_size // 2))
        self.phantom = pygame.transform.scale(image, (self.cel_size // 2,
                                                      self.cel_size // 2))
        self.decalage = (self.cel_size - self.cel_size / 2) / 2
        self.direction = "est"
        self.restart = False

    def touch(self, joueur) -> bool:
        if self.eat:
            return False
        drow = self.row - joueur.row
        dcol = self.col - joueur.col
        if drow**2 + dcol**2 < 0.5**2:
            return True
        return False

    def draw_phantom(self, fenetre):
        y = self.row * self.cel_size
        x = self.col * self.cel_size
        y += self.decalage
        x += self.decalage
        if not self.eat:
            if self.vulnerable:
                fenetre.blit(self.phantom_scare, (x, y))
            else:
                fenetre.blit(self.phantom, (x, y))

    def fuir(self, mazze, row, col, check_bits):
        neighbors = self.get_neighbors(mazze, round(
            self.row), round(self.col), check_bits)
        meilleur_distance = -1
        meilleur_voisin = None
        for (nrow, ncol) in neighbors:
            drow = nrow - row
            dcol = ncol - col
            distance = drow**2 + dcol**2
            if distance > meilleur_distance:
                meilleur_distance = distance
                meilleur_voisin = (nrow, ncol)
        if meilleur_voisin is None:
            self.direction = None
        else:
            prochain_row, prochain_col = meilleur_voisin
            self.conversion_direction(prochain_row, prochain_col)

    def update(self, mazze, row, col, check_bits):
        if self.eat:
            return
        if self.at_center():
            self.row = round(self.row)
            self.col = round(self.col)
            if self.vulnerable:
                self.fuir(mazze, row, col, check_bits)
            else:
                chemin = self.bfs(mazze, row, col, check_bits)
                if len(chemin) > 1:
                    self.deplace_vers_joueur(chemin)
                else:
                    self.direction = None
        self.deplacement()

    def conversion_direction(self, prochain_row, prochain_col):
        if prochain_row > self.row:
            self.direction = "sud"
        elif prochain_row < self.row:
            self.direction = "nord"
        elif prochain_col > self.col:
            self.direction = "est"
        elif prochain_col < self.col:
            self.direction = "ouest"

    def at_center(self):
        return (abs(self.row - round(self.row)) < 0.001 and
                abs(self.col - round(self.col)) < 0.001)

    def deplace_vers_joueur(self, chemin):
        prochain_row, prochain_col = chemin[1]
        self.conversion_direction(prochain_row, prochain_col)

    def deplacement(self):
        facteur = 0.5 if self.ralenti else 1.0
        vitesse_actuelle = self.vitesse * facteur

        if self.direction == "sud":
            self.row += vitesse_actuelle
        elif self.direction == "nord":
            self.row -= vitesse_actuelle
        elif self.direction == "est":
            self.col += vitesse_actuelle
        elif self.direction == "ouest":
            self.col -= vitesse_actuelle
        return

    def get_neighbors(self, mazze, x, y, check_bits) -> list:
        if not (0 <= x < len(mazze) and 0 <= y < len(mazze[0])):
            return []
        murs = check_bits(mazze[x][y])
        deplacements = {
            "nord": (-1, 0),
            "sud": (1, 0),
            "est": (0, 1),
            "ouest": (0, -1),
        }
        voisins = []
        for (direction, (dx, dy)) in deplacements.items():
            if not murs[direction]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < len(mazze) and 0 <= ny < len(mazze[0]):
                    voisins.append((nx, ny))
        return voisins

    def bfs(self, mazze, pacman_row, pacman_col, check_bits):
        queu = []
        dejavisit = []
        depart = (int(round(self.row)), int(round(self.col)))
        arive = (int(pacman_row), int(pacman_col))
        queu = [depart]
        dejavisit = [depart]
        dictparent = {}
        while queu:
            va = queu.pop(0)
            if va == arive:
                break
            diretiion = self.get_neighbors(mazze, va[0], va[1], check_bits)
            for (vx, vy) in diretiion:
                if (vx, vy) not in dejavisit:
                    dejavisit.append((vx, vy))
                    queu.append((vx, vy))
                    dictparent[(vx, vy)] = (va[0], va[1])
        chemin = []
        p = arive
        if arive != depart and arive not in dictparent:
            vide = []
            return vide
        while p != depart:
            chemin.append(p)
            p = dictparent[p]

        chemin.append(depart)
        chemin.reverse()

        return chemin

    def set_vulnerable(self, etat: bool):
        self.vulnerable = etat
        self.ralenti = etat


def charger_scores():
    if not os.path.exists("highscores.json"):
        return []
    try:
        with open("highscores.json", "r", encoding="utf-8") as f:
            donnees = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(donnees, list):
        return []
    resultat = []
    for entree in donnees:
        if not isinstance(entree, dict):
            continue
        nom = entree.get("name")
        score = entree.get("score")
        if not isinstance(nom, str) or not isinstance(score, int):
            continue
        if (not nom or len(nom) > 10
                or not all(c.isalnum() or c == " " for c in nom)):
            continue
        if score < 0:
            continue
        resultat.append(entree)
    resultat.sort(key=lambda e: e["score"], reverse=True)
    return resultat[:10]


def sauvegarder_score(nom, score):
    name_fichier = "highscores.json"
    scores = charger_scores()
    if os.path.exists(name_fichier):
        with open(name_fichier, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(";")
                if len(parts) == 2:
                    scores.append((parts[0], int(parts[1])))
    nom = nom.strip()
    scores.append({"name": nom if nom else "Anonyme", "score": score})
    scores.sort(key=lambda e: e["score"], reverse=True)
    scores = scores[:10]
    with open(name_fichier, "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=4)



def reset_pos(list_fantomes):
    for phanto in list_fantomes:
        phanto.row = phanto.base_row
        phanto.col = phanto.base_col
        phanto.set_vulnerable(False)
    play.row = play.base_row
    play.col = play.base_col


def nouvelle_partie(play, list_fantomes, re, nb_pacgums):
    play.score = 0
    play.vies = 3
    play.level = 1
    re.new_maze(play.level)

    re.size_cel = re.cell_and_windows_size(re.mazze)
    play.cel_size = re.size_cel
    play.decelage = ((play.cel_size - play.cel_size / 2) / 2)

    play.row = len(re.mazze) // 2
    play.col = len(re.mazze[0]) // 2
    play.base_row = play.row
    play.base_col = play.col
    play.direction = "est"
    play.next_direction = "est"

    play.lis_pacgums.clear()
    play.lis_superpacgums.clear()
    play.place_pacgums(re.fenetre, nb_pacgums, re.mazze)
    play.ajoute_super(re.mazze)

    positions_initiales = [
        (0, 0),
        (0, len(re.mazze[0]) - 1),
        (len(re.mazze) - 1, 0),
        (len(re.mazze) - 1, len(re.mazze[0]) - 1)
    ]
    for i, phanto in enumerate(list_fantomes):
        phanto.cel_size = re.size_cel
        phanto.row, phanto.col = positions_initiales[i]
        phanto.base_row, phanto.base_col = positions_initiales[i]
        phanto.eat = False
        phanto.set_vulnerable(False)


if __name__ == "__main__":
    pygame.init()
    re = render()
    state: str = "menu"
    level_max_time = 90
    vitesse_fantomes = 0.04
    nb_pacgums = re.nombre_de_pacgums
    niveau_max = 10
    nom_joueur = ""
    passer_niveau = False
    mode_triche = False
    play = Player(re.size_cel, (len(re.mazze) // 2), len(re.mazze[0]) // 2,
                  "est", re.pont_per_pacgum)
    phantom1 = Phantom(0, 0, re.size_cel, pygame.image.load(
        "image_phantom/1.png"), vitesse_fantomes)
    phantom2 = Phantom(0, len(re.mazze[0]) - 1, re.size_cel,
                       pygame.image.load("image_phantom/2.png"), vitesse_fantomes)
    phantom3 = Phantom(len(re.mazze) - 1, 0, re.size_cel,
                       pygame.image.load("image_phantom/3.png"), vitesse_fantomes)
    phantom4 = Phantom(len(re.mazze) - 1, len(re.mazze[0]) - 1, re.size_cel, pygame.image.load(
        "image_phantom/4.png"), vitesse_fantomes)
    list_fantomes = [phantom1, phantom2, phantom3, phantom4]
    play.place_pacgums(re.fenetre, nb_pacgums, re.mazze)
    play.ajoute_super(re.mazze)
    continuer = True
    clock = pygame.time.Clock()
    start = pygame.time.get_ticks()
    choix = 0
    choix_pause = 0
    options_pause = ["Resume", "Return to main menu"]
    police_titre = pygame.font.Font(None, 80)
    scores_affiches = []
    lignes_instructions = [
        "Fleches : deplacer Pac-Man",
        "Echap : pause",
        "Mange toutes les pacgums pour passer au niveau suivant",
        f"Pacgum : {re.pont_per_pacgum} points",
        "Super pacgum : 50 points, fantomes vulnerables",
        "Fantome mange : 200 points",
        "Touche par un fantome : tu perds une vie",
        f"{level_max_time} secondes par niveau, {niveau_max} niveaux au total",
        "Echap : retour au menu",
    ]
    
    while continuer:
        options = ["Start", "Highscores", "Instructions", "Exit"]

        if state == "menu":
            clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    continuer = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        choix = (choix - 1) % len(options)
                    elif event.key == pygame.K_DOWN:
                        choix = (choix + 1) % len(options)
                    elif event.key == pygame.K_RETURN:
                        if choix == 0:
                            nouvelle_partie(
                                play, list_fantomes, re, nb_pacgums)
                            state = "jeu"
                            start = pygame.time.get_ticks()
                        elif choix == 1:
                            scores_affiches = charger_scores()
                            state = "highscores"
                        elif choix == 2:
                            state = "instructions"
                        elif choix == 3:
                            continuer = False

            re.ecran.fill((0, 0, 0))
            titre = police_titre.render("Pac-Man", True, (255, 255, 0))
            x = (re.largeur_fenetre - titre.get_width()) // 2
            re.ecran.blit(titre, (x, 40))

            for i, texte in enumerate(options):
                couleur = (255, 255, 0) if i == choix else (255, 255, 255)
                image = re.police.render(texte, True, couleur)
                x = (re.largeur_fenetre - image.get_width()) // 2
                re.ecran.blit(image, (x, 150 + i * 50))
            pygame.display.flip()

        if state == "instructions":
            clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    continuer = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        state = "menu"
            re.ecran.fill((0, 0, 0))
            for i, ligne in enumerate(lignes_instructions):
                image = re.police.render(ligne, True, (255, 255, 255))
                x = (re.largeur_fenetre - image.get_width()) // 2
                re.ecran.blit(image, (x, 80 + i * 40))
            pygame.display.flip()

        if state == "highscores":
            clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    continuer = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        state = "menu"
            re.ecran.fill((0, 0, 0))
            titre_hs = police_titre.render("TOP 10", True, (255, 255, 0))
            re.ecran.blit(
                titre_hs, ((re.largeur_fenetre - titre_hs.get_width()) // 2, 30))
            if not scores_affiches:
                retour = re.police.render("Aucun score enregistré", True, (255,255,255))
                re.ecran.blit(
                    retour, ((re.largeur_fenetre - retour.get_width()) // 2, 150))
                pygame.display.flip
            for i, e in enumerate(scores_affiches):
                img_ligne = re.police.render(
                    f"{i + 1}. {e['name']} : {e['score']} pts", True, (255, 255, 255))
                x = (re.largeur_fenetre - img_ligne.get_width()) // 2
                re.ecran.blit(img_ligne, (x, 120 + i * 30))
            retour = re.police.render(
                "Appuyez sur Échap pour retourner au menu", True, (150, 150, 150))
            re.ecran.blit(
                retour, ((re.largeur_fenetre - retour.get_width()) // 2, 430))
            pygame.display.flip()

        if state == "jeu":
            clock.tick(30)
            ec_time = pygame.time.get_ticks() - start
            sec_time = ec_time // 1000
            rest_time = max(0, level_max_time - sec_time)
            if rest_time == 0:
                play.vies -= 1
                reset_pos(list_fantomes)
                start = pygame.time.get_ticks()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    continuer = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        debut_pause = pygame.time.get_ticks()
                        state = "pause"
                    elif event.key == pygame.K_n:
                        passer_niveau = True
                    elif event.key == pygame.K_c:
                        mode_triche = not mode_triche
                    if event.key == pygame.K_UP or event.key == pygame.K_DOWN or\
                            event.key == pygame.K_LEFT or\
                            event.key == pygame.K_RIGHT:
                        play.direction_deplacement(event.key)
            play.update(re.mazze, re.check_bits)
            re.cremaze()
            play.afficher_pacgums(re.fenetre)
            play.afficher_superpacgums(re.fenetre)
            for phanto in list_fantomes:
                phanto.draw_phantom(re.fenetre)
                phanto.update(re.mazze, round(play.row),
                              round(play.col), re.check_bits)
            vul = play.sup_pacgums()
            if (len(play.lis_pacgums) == 0 or passer_niveau):
                play.level += 1
                passer_niveau = False
                if play.level > niveau_max:
                    state = "victoire"
                else:
                    re.new_maze(play.level)
                    reset_pos(list_fantomes)
                    play.lis_pacgums.clear()
                    play.lis_superpacgums.clear()
                    play.place_pacgums(re.fenetre, nb_pacgums, re.mazze)
                    play.ajoute_super(re.mazze)
                    start = pygame.time.get_ticks()
            for fantome in list_fantomes:
                if fantome.eat and pygame.time.get_ticks() >= fantome.end_eat:
                    fantome.eat = False

            if vul:
                for fantome in list_fantomes:
                    fantome.vulnerable = True
                    fantome.ralenti = True
                    fantome.fin_vulnerable = pygame.time.get_ticks() + 6000

            for fantome in list_fantomes:
                if fantome.vulnerable and pygame.time.get_ticks() >= fantome.fin_vulnerable:
                    fantome.vulnerable = False
                    fantome.ralenti = False

            play.draw_player(re.fenetre)
            re.draw_hud(play, rest_time, mode_triche)
            pygame.display.flip()
            for fantomes in list_fantomes:
                iscol = fantomes.touch(play)
                if iscol:
                    if fantomes.vulnerable:
                        fantomes.eat = True
                        fantomes.end_eat = pygame.time.get_ticks() + 5000
                        play.score += 200
                        fantomes.row = fantomes.base_row
                        fantomes.col = fantomes.base_col
                        fantomes.set_vulnerable(False)
                    else:
                        play.vies -= 1
                        reset_pos(list_fantomes)
                        break
            if play.vies == 0:
                state = "game_over"

        if state in ("victoire", "game_over"):
            clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    continuer = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        state = "saisie_nom"
                        nom_joueur = ""
            re.ecran.fill((0, 0, 0))
            titre_fin = "VICTOIRE !" if state == "victoire" else "GAME OVER"
            img_fin = re.police.render(titre_fin, True, (255, 255, 255))
            scr = re.police.render(
                ("Score : " + str(play.score)), True, (255, 255, 255))
            suite = re.police.render(
                "Appuyez sur Entree pour enregistrer", True, (200, 200, 200))
            re.ecran.blit(
                img_fin, ((re.largeur_fenetre - img_fin.get_width()) // 2, 150))
            re.ecran.blit(
                scr, ((re.largeur_fenetre - scr.get_width()) // 2, 220))
            re.ecran.blit(
                suite, ((re.largeur_fenetre - suite.get_width()) // 2, 300))
            pygame.display.flip()

        if state == "saisie_nom":
            clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    continuer = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        sauvegarder_score(nom_joueur, play.score)
                        state = "menu"
                    elif event.key == pygame.K_BACKSPACE:
                        nom_joueur = nom_joueur[:-1]
                    else:
                        if len(nom_joueur) < 10 and (event.unicode.isalnum() or event.unicode == " "):
                            nom_joueur += event.unicode
            re.ecran.fill((0, 0, 0))
            titre = re.police.render(
                "Entrez votre nom :", True, (255, 255, 255))
            affichage_nom = re.police.render(
                nom_joueur + "_", True, (255, 255, 0))
            re.ecran.blit(
                titre, ((re.largeur_fenetre - titre.get_width()) // 2, 180))
            re.ecran.blit(affichage_nom, ((re.largeur_fenetre -
                          affichage_nom.get_width()) // 2, 240))
            pygame.display.flip()

        if state == "pause":
            clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    continuer = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                        choix_pause = 1 - choix_pause
                    elif event.key == pygame.K_RETURN:
                        if choix_pause == 0:
                            state = "jeu"
                            start += (pygame.time.get_ticks() - debut_pause)
                        elif choix_pause == 1:
                            state = "menu"
                            choix_pause = 0
            re.ecran.fill((0, 0, 0))
            pause = police_titre.render("PAUSE", True, (255, 255, 255))
            re.ecran.blit(
                pause, ((re.largeur_fenetre - pause.get_width()) // 2, 80))
            for i, texte in enumerate(options_pause):
                couleur = (255, 255, 0) if i == choix_pause else (
                    255, 255, 255)
                image = re.police.render(texte, True, couleur)
                x = (re.largeur_fenetre - image.get_width()) // 2
                re.ecran.blit(image, (x, 200 + i * 50))
            pygame.display.flip()

    pygame.quit()
