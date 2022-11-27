import sys
import pygame
import time
from pygame.locals import *
from collections import deque, defaultdict
import random
from clues import rgb_to_color_clue, clue_to_rgb
from rgb_matrix import board_rgb_matrix, flattened_board_rgb_matrix

class Cell:            # of top left corner
    def __init__(self, posx, posy, rgb):
        self.posx = posx
        self.posy = posy
        self.rgb = rgb

class Board:
    def __init__(self, cell_matrix):
        self.cell_matrix = cell_matrix

def partition(player_seq_list, left, right):
  pivot = left
  pivot_value = player_seq_list[pivot][1]
  for i in range(left + 1, right + 1):
    if player_seq_list[i][1] > pivot_value:
        pivot += 1
        player_seq_list[i], player_seq_list[pivot] = player_seq_list[pivot], player_seq_list[i]
  player_seq_list[left], player_seq_list[pivot] = player_seq_list[pivot], player_seq_list[left]
  return pivot

def quicksort_inplace(player_seq_list, left, right):
    if left > right:
        return
    pivot = partition(player_seq_list, left, right)
    quicksort_inplace(player_seq_list, left, pivot - 1)
    quicksort_inplace(player_seq_list, pivot + 1, right)

def binary_search(rgb_tuple, left, right, sorting_color):
    while right >= left:
        mid = (left+right)//2
        print(" l, r, m - " ,left, right, mid)
        print(" left " , flattened_board_rgb_matrix[left], " right - ", flattened_board_rgb_matrix[right], " middle - ", flattened_board_rgb_matrix[mid], " Sorting color ", sorting_color)
        #compare if we found the whole tuple
        if flattened_board_rgb_matrix[mid][0][0] == rgb_tuple[0] and flattened_board_rgb_matrix[mid][0][1] == rgb_tuple[1] and flattened_board_rgb_matrix[mid][0][2] == rgb_tuple[2]:
            print("Found")
            return (mid, mid)
        # if we found that r indexes are the same, we stop and continue with iterative search
        if flattened_board_rgb_matrix[mid][0][sorting_color] == rgb_tuple[sorting_color]:
            if flattened_board_rgb_matrix[mid][0][sorting_color+1] >= rgb_tuple[sorting_color+1]:
                return (left, mid)
            else:
                return (mid, right)
        if flattened_board_rgb_matrix[mid][0][sorting_color] < rgb_tuple[sorting_color]:
            left = mid + 1  # search on the right subarray
        elif flattened_board_rgb_matrix[mid][0][sorting_color] > rgb_tuple[sorting_color]:
            right = mid - 1  # otherwise search in the left subarray
    print("Could not find", rgb_tuple)
    return (7, 15)
def from_rgb_to_Board(CELL_SIZE):
    board_cell_matrix = [[0 for _ in range(len(board_rgb_matrix[0]))] for _ in range(len(board_rgb_matrix))]
    # transform each cell in matrix into a Cell object and create board_cell_matrix
    for i in range(len(board_rgb_matrix)):
        for j in range(len(board_rgb_matrix[0])):
            board_cell_matrix[i][j] = Cell(CELL_SIZE * i, CELL_SIZE * j, board_rgb_matrix[i][j])

    # put all these Cell objects into a Board class's cell_matrix
    board = Board(board_cell_matrix)
    return board

def introduce_players():
    N_PLAYERS = 0
    while N_PLAYERS < 1 or N_PLAYERS > 9:
        try:
            N_PLAYERS = int(input("Enter the number of players (1-9) >> "))
        except ValueError:
            print("The input was not a valid integer.")

    PLAYER_NAMES_SCORES = {}
    for i in range(1, N_PLAYERS+1):
        keep_trying = True
        while keep_trying:
            name = input("Enter a 4 letter nickname for player N{} >> ".format(i))
            if len(name) <= 4 and name not in PLAYER_NAMES_SCORES.keys():
                PLAYER_NAMES_SCORES[name] = 0
                keep_trying = False
            else:
                print("Invalid name! Make sure that it has maximum 4 characters.")

    print("\nLets Begin the Game Now!")
    # adding a bot
    PLAYER_NAMES_SCORES['Bot'] = 0
    return N_PLAYERS+1, PLAYER_NAMES_SCORES

class Round:
    def __init__(self, true_rgb, true_indexing, screen, player_seq_list, N_PLAYERS, board, CELL_SIZE, PLAYER_NAMES_SCORES, round_scores_hidden, color_clue):
        self.true_rgb = true_rgb
        self.true_indexing = true_indexing
        self.screen = screen
        self.player_seq_list = player_seq_list
        self.N_PLAYERS = N_PLAYERS
        self.board = board
        self.CELL_SIZE = CELL_SIZE
        self.PLAYER_NAMES_SCORES = PLAYER_NAMES_SCORES
        self.circle_locations = {}
        self.round_scores_hidden = round_scores_hidden
        self.color_clue = color_clue

    def empty_circle_locations(self):
        for name in self.PLAYER_NAMES_SCORES:
            self.circle_locations[name] = -1

    def play_round(self):
        # empty circles
        self.empty_circle_locations()
        #draw board before the round starts
        self.draw_board_players_clue_circles_on_screen()
        for i in range(self.N_PLAYERS):
            current_player = self.player_seq_list[i][0]
            self.print_whos_turn(current_player)
            not_clicked_on_cell = True
            if current_player == 'Bot':
                self.bots_move()
                not_clicked_on_cell = False
            while not_clicked_on_cell:
                for event in pygame.event.get():
                    if event.type == pygame.MOUSEBUTTONUP:
                        pos = pygame.mouse.get_pos()
                        print(" Mouse click pos: ", pos)
                        if self.inside_board(pos):
                            self.circle_locations[current_player] = (pos[0]//self.CELL_SIZE, pos[1]//self.CELL_SIZE)
                            self.calculate_distance_from_real_color((pos[0]//self.CELL_SIZE, pos[1]//self.CELL_SIZE), current_player)
                            not_clicked_on_cell = False

                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()

            self.draw_board_players_clue_circles_on_screen()

        self.update_scores()

        print(self.PLAYER_NAMES_SCORES)
        self.display_actual_color()
        time.sleep(4)

    def update_scores(self):
        for key in self.round_scores_hidden.keys():
            self.PLAYER_NAMES_SCORES[key] = self.round_scores_hidden[key]

    def calculate_distance_from_real_color(self, indexes, current_player):
        print(" calculating distance from ", current_player, self.circle_locations[current_player]," to " ,self.true_indexing)
        print("difference - ", (abs(self.true_indexing[0]-indexes[0])+abs(self.true_indexing[1] - indexes[1])))
        self.round_scores_hidden[current_player] += (abs(self.true_indexing[0]-indexes[0])+abs(self.true_indexing[1] - indexes[1]))

    def display_actual_color(self):
        x = self.true_indexing[0]*self.CELL_SIZE
        y = self.true_indexing[1]*self.CELL_SIZE
        pygame.draw.rect(self.screen, "black", pygame.Rect(x, y, self.CELL_SIZE, self.CELL_SIZE), 3)
        pygame.display.flip()
        time.sleep(2)

    def bots_move(self):
        rand_rgb_index = random.randint(0, len(clue_to_rgb[self.color_clue])-1)
        bots_rgb_tuple = clue_to_rgb[self.color_clue][rand_rgb_index]
        left, right = binary_search(bots_rgb_tuple, 0, len(flattened_board_rgb_matrix)-1, 0)
        for i in range(left, right+1):
            if flattened_board_rgb_matrix[i][0] == bots_rgb_tuple:
                pos = flattened_board_rgb_matrix[i][1]
                break
        print("Bots position: ", pos)
        self.circle_locations['Bot'] = (pos[0], pos[1])
        self.calculate_distance_from_real_color((pos[0], pos[1]), 'Bot')

    def inside_board(self, pos):
        return (pos[0] >= 0 and pos[0] <= 320 and pos[1] >= 0 and pos[1] <= 600)

    def print_whos_turn(self, current_player):
        font = pygame.font.Font(pygame.font.get_default_font(), 26)
        text_surface = font.render("{}'s turn".format(current_player), True, (200, 200, 200))
        self.screen.blit(text_surface, dest=(330, 550))
        pygame.display.update()

    def draw_board_players_clue_circles_on_screen(self):
        self.screen.fill('black')
        #print(" Board cell matrix  - " ,len(self.board.cell_matrix))
        for i in range(len(self.board.cell_matrix)):
            for j in range(len(self.board.cell_matrix[0])):
                posx = self.board.cell_matrix[i][j].posx
                posy = self.board.cell_matrix[i][j].posy
                color = self.board.cell_matrix[i][j].rgb
                pygame.draw.rect(self.screen, color, pygame.Rect(posx, posy, self.CELL_SIZE, self.CELL_SIZE))
        # draw the text Clue on screen
        font = pygame.font.Font(pygame.font.get_default_font(), 26)
        text_surface = font.render('Clue N1: {}'.format(self.color_clue), True, (255, 255, 255))
        self.screen.blit(text_surface, dest=(330, 20))
        font = pygame.font.Font(pygame.font.get_default_font(), 26)
        text_surface = font.render('Clue N2: {}'.format(self.true_rgb), True, (255, 255, 255))
        self.screen.blit(text_surface, dest=(330, 50))
        pygame.display.flip()

        # print Players
        line = 100
        for name in self.PLAYER_NAMES_SCORES.keys():
            font = pygame.font.Font(pygame.font.get_default_font(), 26)
            text_surface = font.render('{} - {}'.format(name, PLAYER_NAMES_SCORES[name]), True, (255, 255, 255))
            self.screen.blit(text_surface, dest=(330, line))
            line += 40

        # draw circles
        for key in self.circle_locations.keys():
            if self.circle_locations[key] != -1:
                if key == 'Bot':
                    color = "white"
                else: color = "black"
                matrix_index = self.circle_locations[key]
                cen_pos = (matrix_index[0]*self.CELL_SIZE+self.CELL_SIZE//2, matrix_index[1]*self.CELL_SIZE+self.CELL_SIZE//2)
                pygame.draw.circle(self.screen, color, cen_pos, 10)

        # display flip
        pygame.display.flip()

def main(N_PLAYERS, PLAYER_NAMES_SCORES):
    WINDOWWIDTH, WINDOWHEIGHT = 640, 600
    CELL_SIZE = 20

    pygame.init()
    screen = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
    pygame.display.set_caption('Hues & Cues')

    #transforming a matrix of rgb into Board class (which has a cell matrix)
    board = from_rgb_to_Board(CELL_SIZE)
    round_scores_hidden = defaultdict(int)

    while True:
        #randomly choose a cell in the board
        #print(len(board.cell_matrix[0]))
        rand_col = random.randint(0, len(board.cell_matrix[0])-1) #(0-30)
        rand_row = random.randint(0, len(board.cell_matrix)-1) #(0-16)
        print("Actual position ",rand_row,"  " , rand_col)
        rand_rgb = board.cell_matrix[rand_row][rand_col]
        color_clue = rgb_to_color_clue[tuple(rand_rgb.rgb)]
        print(color_clue)
        #print([rand_row, rand_col])

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        player_seq_list = []
        for key, value in PLAYER_NAMES_SCORES.items():
            player_seq_list.append((key, value))
        quicksort_inplace(player_seq_list, 0, N_PLAYERS-1)
        one_round = Round(rand_rgb.rgb, [rand_row, rand_col], screen, player_seq_list, N_PLAYERS, board, CELL_SIZE, PLAYER_NAMES_SCORES, round_scores_hidden, color_clue)
        one_round.play_round()

if __name__ == "__main__":
    N_PLAYERS, PLAYER_NAMES_SCORES = introduce_players()
    main(N_PLAYERS, PLAYER_NAMES_SCORES)