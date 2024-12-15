import random
import os
def gen():
    size = 5
    matrix = [[random.choice([0, 1, -1]) for _ in range(size)] for _ in range(size)]
    return matrix
def read_board():
    file_path = './src/board.txt'
    board = []
    with open(file_path, 'r') as file:
        for line in file:
            # Loại bỏ ký tự xuống dòng và tách các phần tử theo khoảng trắng
            row = list(map(int, line.strip().split()))
            board.append(row)
    return board

def save_to_txt(folder_path, file_name, board_size,game_mode, moves):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    file_path = os.path.join(folder_path, file_name)
    with open(file_path, "w") as file:
        file.write(f"{game_mode} {board_size}\n")
        for move in moves:
            file.write(f"{move[0]} {move[1]} {move[2]}\n")
def load_history(folder_path, file_name):
    file_path = os.path.join(folder_path, file_name)
    with open(file_path, "r") as file:
        game_mode,board_size = file.readline().strip().split()
        moves = []
        for line in file:
            player, row, col,  = line.strip().split()
            moves.append((player,row,col))
    return game_mode, board_size, moves

