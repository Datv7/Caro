import customtkinter as ctk
import tkinter as tk
import timeit
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool, Value
import os
from datetime import datetime
import utils
# ai:1(o)
#algorithm
real_state=[]
sequence_end_row=0
sequence_end_col=0
direction=(0,0)
center_score=[]
n=0
history_moves=[]
#algorithm
k=0
def init():
    global real_state,center_score
    real_state=np.zeros((n,n),dtype=int)
    center=n//2
    center_score =np.zeros((n,n),dtype=int) 
    for i in range(n):
        for j in range(n):
            center_score[i][j]=n - max(abs(i - center), abs(j - center))  

def available_move(state):
    n=len(state[0])
    moves = []
    for row in range(n):
        for col in range(n):
            if state[row][col] == 0: 
                moves.append((row, col))
    return moves

def make_move(state,move,player):
    row,col=move
    new_state=state.copy()
    new_state[row][col]=1 if player==1 else -1
    return new_state

def valid(row,col):
    return (row>=0 and row<n) and (col>=0 and col<n)

def winner(state,move,player,test):
    row,col=move
    directions=[(1,1),(1,-1),(1,0),(0,-1)]

    for x,y in directions:
        rowi=row-4*y
        coli=col-4*x
        current_count=0
        end_row=rowi
        end_col=coli
        for i in range(0,9):
            if(valid(rowi,coli)):
                end_row=rowi
                end_col=coli
                value=state[rowi][coli]
                if(value!=player): current_count=0
                else:current_count+=1
                if((current_count+(9-i))<5 or current_count==5):break
            rowi+=y
            coli+=x

        if(current_count!=5):continue    
        if(not test):
            global sequence_end_row,sequence_end_col,direction
            sequence_end_row=end_row
            sequence_end_col=end_col
            direction=(x,y)
        return 1 if player==1 else -1

    return 0 

def evaluate_heuristic(state,center_score,player):
    n=len(state)
    score = 0   
    s=score_state(state,center_score)
    if(player==1): s[-1]*=4
    else: s[1]*=4
    score =score+s[1]+s[2]
    score =score-s[-1]-s[-2]
    return score


def score_direction(state,row,col,direction,player,range_line):
    row0=row
    col0=col
    left=1
    right=1
    count=0
    end_left=None
    end_right=None
    space1=False
    space2=False
    n=len(state[0])
    if(range_line[1]+range_line[0]+1<5): return 0
    for i in range(range_line[0]):
        row-=direction[0]
        col-=direction[1]
        value=state[row][col]
        if (value==0):
            if space1: break
            else:
                srow=row-direction[0]
                scol=col-direction[1]
                if(i==range_line[0]-1):break
                if(srow>=0 and scol>=0 and scol<n and srow<n and state[srow][scol]==player ):
                    space1=True
                    continue
                break
        elif(value!=player):
            end_left=(i,)
            break
        
        count+=1
    row=row0
    col=col0
    for i in range(range_line[1]):
        row+=direction[0]
        col+=direction[1]
        value=state[row][col]
        if (value==0):
            if space2: break
            else:
                srow=row+direction[0]
                scol=col+direction[1]
                if(i==range_line[1]-1):break
                if(srow>=0 and scol>=0 and scol<n and srow<n and state[srow][scol]==player ):
                    space2=True
                    continue
                break
        elif(value!=player):
            end_right=(i,)
            break
        count+=1
    percent=0.75 if(space2 or space1) else 1 
    if(end_left and end_right ):
        if( (end_right[0]+end_left[0] +1)<5): return 0
    if(end_left): 
        left=0
        if(range_line[1]+end_left[0]+1<5):right=0
    if(end_right): 
        right=0
        if(end_right[0]+range_line[0]+1<5): left=0
    return 4**count*(left+right)*percent
def score_state(state,center_score):
    n=len(state[0])
    real_length=5
    length=real_length-1
    directions=[(-1,1),(1,1),(1,0),(0,1)] # diag_anti, diag_main, row, col
    score={1:0,2:0,-1:0,-2:0}
    
    
    for row in range(n):
        for col in range(n):
            value=state[row][col]
            if (value!=0):
                range_row=(min(length, row),min(length,n-1-row))
                range_col=(min(length, col),min(length,n-1-col))
                range_diag_main=(min(length,row,col),min(length,n-1-row,n-1-col))
                range_diag_anti=(min(length,col,n-1-row),min(length,row,n-1-col))
                score[value]+=score_direction(state,row,col,directions[0],value,range_diag_anti)
                score[value]+=score_direction(state,row,col,directions[1],value,range_diag_main)
                score[value]+=score_direction(state,row,col,directions[2],value,range_row)
                score[value]+=score_direction(state,row,col,directions[3],value,range_col)
                score[value*2]+= center_score[row][col]  

    # chain_points = {2: 2, 3: 10, 4: 100,5:1000}
    # # chain_points2 = {2: 2, 3: 11, 4: 101,5:1002}
    # chains=count_chain(state,5)
    # # print(f'{chains.get(1)}:{chains.get(-1)}')
    # score1=sum(chain_points.get(count) for count in chains.get(1))
    # score2=sum(chain_points.get(count) for count in chains.get(-1))
    # score=(score1,score2)

    return score

def count_chain(state,length):
    k=0
    n=len(state[0])
    chains = {1:[],-1:[]}
    # index 0:count, index 1: current_value, index 3: length, index 4:first time
    row_count=np.zeros((4,n),dtype=int)
    col_count=np.zeros((4,n),dtype=int)
    diag_main_count=np.zeros((4,2*n-1),dtype=int)
    diag_anti_count=np.zeros((4,2*n-1),dtype=int)

    for i in range(n):
        for j in range(n):
            value=state[i][j]
            diag_main_index=i-j+n-1
            diag_anti_index=i+j
            
            if(value==0):
                # if row_count[0][i] > 1: chains.get(row_count[1][i]).append(row_count[0][i])
                # if col_count[0][j] > 1: chains.get(col_count[1][j]).append(col_count[0][j])
                # if diag_main_count[0][diag_main_index] > 1: chains.get(diag_main_count[1][diag_main_index]).append(diag_main_count[0][diag_main_index])
                # if diag_anti_count[0][diag_anti_index] > 1: chains.get(diag_anti_count[1][diag_anti_index]).append(diag_anti_count[0][diag_anti_index])

                row_count[2][i]+=1
                col_count[2][j]+=1
                diag_main_count[2][diag_main_index]+=1
                diag_anti_count[2][diag_anti_index]+=1
            else:
                # first time
                if(not row_count[3][i]):
                    row_count[3][i]=1
                    row_count[1][i]=value
                if(not col_count[3][j]):
                    col_count[3][j]=1
                    col_count[1][j]=value
                if(not diag_main_count[3][diag_main_index]):
                    diag_main_count[3][diag_main_index]=1
                    diag_main_count[1][diag_main_index]=value
                if(not diag_anti_count[3][diag_anti_index]):
                    diag_anti_count[3][diag_anti_index]=1
                    diag_anti_count[1][diag_anti_index]=value

                # ////
                if(value!=row_count[1][i]):
                    if (row_count[0][i] > 1 and row_count[2][i] >= length): chains.get(row_count[1][i]).append(row_count[0][i])
                    row_count[0][i]=1
                    row_count[1][i]=value
                    row_count[2][i]=1
                else: 
                    row_count[0][i]+=1
                    row_count[2][i]+=1

                if(value!=col_count[1][j]):
                    if (col_count[0][j] > 1 and col_count[2][j] >= length): chains.get(col_count[1][j]).append(col_count[0][j])
                    col_count[0][j]=1
                    col_count[1][j]=value
                    col_count[2][j]=1
                    
                else: 
                    col_count[0][j]+=1
                    col_count[2][j]+=1

                if(value!=diag_main_count[1][diag_main_index]):
                    if (diag_main_count[0][diag_main_index] > 1 and diag_main_count[2][diag_main_index] >= length): chains.get(diag_main_count[1][diag_main_index]).append(diag_main_count[0][diag_main_index])
                    diag_main_count[0][diag_main_index]=1
                    diag_main_count[1][diag_main_index]=value
                    diag_main_count[2][diag_main_index]=1
                else: 
                    diag_main_count[0][diag_main_index]+=1
                    diag_main_count[2][diag_main_index]+=1

                if(value!=diag_anti_count[1][diag_anti_index]):
                    if (diag_anti_count[0][diag_anti_index] > 1 and diag_anti_count[2][diag_anti_index] >= length): chains.get(diag_anti_count[1][diag_anti_index]).append(diag_anti_count[0][diag_anti_index])
                    diag_anti_count[0][diag_anti_index]=1
                    diag_anti_count[1][diag_anti_index]=value
                    diag_anti_count[2][diag_anti_index]=1
                else: 
                    diag_anti_count[0][diag_anti_index]+=1
                    diag_anti_count[2][diag_anti_index]+=1

    # xử lý biên
    for i in range(n):
        if (row_count[0][i] > 1 and row_count[2][i] >= length): chains.get(row_count[1][i]).append(row_count[0][i])
        if (col_count[0][i] > 1 and col_count[2][i] >= length): chains.get(col_count[1][i]).append(col_count[0][i])
    for i in range(2*n-1):
        if (diag_main_count[0][i] > 1 and diag_main_count[2][i] >= length): chains.get(diag_main_count[1][i]).append(diag_main_count[0][i])
        if (diag_anti_count[0][i] > 1 and diag_anti_count[2][i] >= length): chains.get(diag_anti_count[1][i]).append(diag_anti_count[0][i])

    return chains

def is_full(state):
    for rowi in state:
        if 0 in rowi:  
            return False
    return True

def minimax(state,center_score,depth,move,alpha,beta,player):

    global k
    winner_player=winner(state,move,player*-1,True)
    if winner_player==1: return 10000
    if winner_player==-1: return -10000
    if(depth==0 or is_full(state)):
        return evaluate_heuristic(state,center_score,player*1)
    reverse=True if player==1 else False
    moves = available_move(state)
    # print(len(moves))
    moves = sorted(moves, key=lambda m: evaluate_heuristic(make_move(state, m, player),center_score,player), reverse=reverse)
    if(player==1):
        for i in moves:
            new_state=make_move(state,i,1)
            value=minimax(new_state,center_score,depth-1,i,alpha,beta,-1)
            alpha=max(alpha,value)
            if(alpha>=beta): break
        return alpha
    elif(player==-1):
        for i in moves:
            new_state=make_move(state,i,-1)
            value=minimax(new_state,center_score,depth-1,i,alpha,beta,1)
            beta=min(beta,value)
            if(alpha>=beta): break
        return beta

def process_score(move,state,center_score,player):
    score=evaluate_heuristic(state,center_score,player)
    return (move,score)    

def best_move():
    alpha=-999999
    best_move=None
    moves = available_move(real_state)
    s=len(real_state)
    quantity=s*s- len(moves)
    if(quantity<=25):
        print('single')
        moves = sorted(moves, key=lambda move: evaluate_heuristic(make_move(real_state, move, 1),center_score,1), reverse=True)
        best_move= moves[0]
    else:
        inputs=[]
        for move in moves: 
            new_state=make_move(real_state, move, 1)
            inputs.append((move,new_state,center_score,1))
        with Pool(os.cpu_count()) as pool:
            results = pool.starmap(process_score, inputs)
        moves=sorted(results,key=lambda x:x[1],reverse=True)
        x=len(moves)
        if(x>80 or s==9):
            print("process_1")
            best_move= moves[0][0]
        else:
            if(x<30): depth=3
            elif(x<50): depth=2
            elif(x<=80): depth=1
            print('process_2')
            size=20
            start=0
            n=len(real_state)
            while start< len(moves):
                end=min(start+size,len(moves))
                inputs=[]
                for move,score in moves[start:end]:            
                    new_state=make_move(real_state,move,1)
                    inputs.append((new_state,center_score,depth,move,alpha,999999,-1))
                if(not inputs): break 
                with Pool(os.cpu_count()) as pool:
                    results = pool.starmap(minimax, inputs)
                print(results) # in kết quả
                value=max(results)
                if(value>alpha):
                    alpha=value
                    best_move,score=moves[start + results.index(max(results))]
                start=end
                # count=9 if n== 9 else 6
                count=1
                size=size*count
    return best_move
  
# UI
root=ctk.CTk()
root.title('Caro')
root.config(background='white')
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
current_cell_tag='0:0'
turn='x'
board=ctk.CTkCanvas(root)
turn_label=ctk.CTkLabel(root)
board_size=ctk.IntVar(value=15)
cell_size=27
game_mode='AI'
def on_ai_click():
    global turn,game_mode
    turn='x'
    game_mode='AI'
    draw()

def on_friend_click():
    global turn,game_mode
    turn='x'
    game_mode='Friend'
    draw()

def menu(save):
    for i in root.winfo_children():
        i.destroy()
    if(save):
        utils.save_to_txt('./history',datetime.now().strftime("game_%Y-%m-%d_%H-%M-%S.txt"),board_size.get(),game_mode,history_moves)
        save=False
    root.geometry(f'600x400+{(int)((screen_width-600)/2)}+{(int)((screen_height-400)/2)}')  

    title = ctk.CTkLabel(root, text="Game Mode",bg_color='white', font=('Consolas',19))
    friend_button = ctk.CTkButton(root, text="Friend", font=('Consolas',17),bg_color='white', fg_color="#28a745", hover_color="#218838", text_color="white", corner_radius=10, command=on_friend_click)
    ai_button = ctk.CTkButton(root, text="AI", font=('Consolas',17),bg_color='white', fg_color="#007bff", hover_color="#0056b3", text_color="white", corner_radius=10, command=on_ai_click)
    board_9=ctk.CTkRadioButton(root,text='9x9',bg_color='white',variable=board_size,value=9,font=('Consolas',15))
    board_15=ctk.CTkRadioButton(root,text='15x15',bg_color='white',variable=board_size,value=15,font=('Consolas',15))
    board_19=ctk.CTkRadioButton(root,text='19x19',bg_color='white',variable=board_size,value=19,font=('Consolas',15))
    history_button=ctk.CTkButton(root,height=15,width=10, text="+", font=('Consolas',28),bg_color='white', fg_color="gray",hover_color="gray",  text_color="black", corner_radius=10, command=lambda:draw_menu_history())

    title.place(relx=0.5, rely=0.2, anchor="center")
    ai_button.place(relx=0.5, rely=0.38, anchor="center")
    friend_button.place(relx=0.5, rely=0.5, anchor="center")
    board_9.place(relx=0.3, rely=0.65, anchor="center")
    board_15.place(relx=0.5, rely=0.65, anchor="center")
    board_19.place(relx=0.7, rely=0.65, anchor="center")
    history_button.place(relx=0.05, rely=0.5, anchor="center")
def draw_chain():
    row=sequence_end_row
    col=sequence_end_col
    x,y=direction
    color='#ed9c87' if turn=='x' else '#99d0f0'
    for i in range(0,5):
        tag=f'{row}:{col}'
        row-=y
        col-=x
        board.itemconfig(board.find_withtag(tag),fill=color)
    board.update_idletasks()

def draw_menu_history():
    box=ctk.CTkToplevel(root)
    box.transient(root)
    box.title('History')
    box.geometry(f'600x400+{(screen_width-600)//2}+{(screen_height-400)//2}')
    for file in os.listdir('./history'):
        file_button = ctk.CTkButton(box, text=file,bg_color='white',  hover_color="gray", text_color="black", command=lambda file=file:draw_history(file,box))
        file_button.pack(fill="both", expand=True, padx=20, pady=10)

def action(history_board,game_history,action_number):
    if(action_number==2):
        for i in range(len(game_history[2])-2-game_history[1]):
            action(history_board,game_history,1)
    else:
        row=None
        col=None
        t=''
        if(action_number==1 and (game_history[1] <len(game_history[2])-1)):
            game_history[1]+=1
            player,row,col= game_history[2][game_history[1]]
            player=int(player)
            print(f'{player}:{type(player)}')
            if(player==1): t='o'
            elif(player==-1): t='x'
        elif(action_number==-1 and game_history[1]>0):
            player,row,col= game_history[2][game_history[1]]
            game_history[1]-=1
        else: return None
        text_tag=f't{row}:{col}'
        cell_tag=f'{row}:{col}'
        history_board.itemconfig(history_board.find_withtag(text_tag),fill='#6b6b6b',text=t)
        id0=history_board.find_withtag('current')
        tags = history_board.gettags(id0)  # Lấy tất cả các tag của đối tượng
        new_tags = tuple(tag for tag in tags if tag != 'current')
        history_board.itemconfig(id0,fill='white',tags=new_tags)
        id=history_board.find_withtag(cell_tag)
        history_board.itemconfig(id,fill='#adadad',tags=('current',cell_tag))
        history_board.update_idletasks()
        print(history_board.gettags(id))
    return None
def draw_history(file_name,box):
    
    history_board_window=ctk.CTkToplevel(box)
    history_board_window.transient()
    history_board_window.title('Caro')
    history_board_window.config(background='white')
    game_mode, board_size,moves=utils.load_history('./history',file_name)
    board_size=int(board_size)
    game_history={1:-1,2:moves}
    size=cell_size*board_size
    main_frame = ctk.CTkFrame(history_board_window, corner_radius=12,bg_color='white')
    main_frame.place(x=10,y=10)
    history_board=ctk.CTkCanvas(main_frame,width=size,height=size,highlightbackground='black')
    history_board.pack(padx=10,pady=10)
    draw_board(history_board)
    right_frame=ctk.CTkFrame(history_board_window,width=130,height=size+20,corner_radius=12,bg_color='white',fg_color='white')
    right_frame.place(x=size+43,y=10)
    game_mode_label=ctk.CTkLabel(right_frame,width=130,text=f'Game mode: {game_mode}',font=('Consolas',16),bg_color='white')
    game_mode_label.place(relx=0.5,rely=0.2,anchor='center')
    next_button=ctk.CTkButton(right_frame,width=130,text='Next',font=('Consolas',16),bg_color='white',border_width=0.5,border_color='black')
    next_button.place(relx=0.5,rely=0.4,anchor='center')
    back_button=ctk.CTkButton(right_frame,width=130,text='Back',font=('Consolas',16),bg_color='white',border_width=0.5,border_color='black')
    back_button.place(relx=0.5,rely=0.6,anchor='center')
    end_button=ctk.CTkButton(right_frame,width=130,text='Jump to End',font=('Consolas',16),bg_color='white',border_width=0.5,border_color='black')
    end_button.place(relx=0.5,rely=0.8,anchor='center')
    window_width=size+40+10+130
    window_height=size+40
    history_board_window.geometry(f'{window_width}x{window_height}+{(int)((screen_width-window_width)/2)}+{(int)((screen_height-window_height)/2)}')
    # action(history_board,game_history,1)
    next_button.bind('<Button-1>',lambda e: action(history_board,game_history,1))
    back_button.bind('<Button-1>',lambda e: action(history_board,game_history,-1))
    end_button.bind('<Button-1>',lambda e: action(history_board,game_history,2))

def show_message(message):
    box=ctk.CTkToplevel()
    box.title('Notification')
    box.geometry(f'250x130+{(screen_width//2)+100}+{(screen_height-130)//2}')
    box.grab_set()
    box.transient()
    box.protocol("WM_DELETE_WINDOW", menu)
    message=ctk.CTkLabel(box,text=message,font=('Consolas',16))
    message.place(relx=0.5,rely=0.3,anchor='center')
    button=ctk.CTkButton(box,text='Menu',font=('Consolas',16),command=lambda :menu(True))
    button.place(relx=0.5,rely=0.65,anchor='center')

def onclick_cell(move): 
    global real_state,current_cell_tag,turn,k
    k=0
    row,col=move
    player=-1 if turn=='x' else 1
    if(real_state[row][col]): return 
    real_state[row][col]=player
    history_moves.append((player,row,col))
    text_tag=f't{row}:{col}'
    cell_tag=f'{row}:{col}'
    board.itemconfig(board.find_withtag(text_tag),fill='#6b6b6b',text=turn)
    board.itemconfig(board.find_withtag(current_cell_tag),fill='white')
    board.itemconfig(board.find_withtag(cell_tag),fill='#adadad')
    
    if(winner(real_state,move,player,False)!=0):
        draw_chain()
        show_message(f'Winner: {turn.upper()}!')
        return
    if(is_full(real_state)):
        show_message('Both sides played well!')
        return
    current_cell_tag=cell_tag
    turn='x' if(turn=='o') else 'o'
    turn_label.configure(text=f'Turn: {turn.upper()}')
    board.update_idletasks()
    if(game_mode=='AI' and turn=='o'):
        move_ai=best_move()
        onclick_cell(move_ai)

def draw():
    global board,turn_label,n
    n=board_size.get()
    init()
    for i in root.winfo_children():
        i.destroy()
    
    size=cell_size*board_size.get()
    main_frame = ctk.CTkFrame(root, corner_radius=12,bg_color='white')
    main_frame.place(x=10,y=10)
    right_frame=ctk.CTkFrame(root,width=140,height=size+20,corner_radius=12,bg_color='white',fg_color='white')
    right_frame.place(x=size+43,y=10)
    turn_label=ctk.CTkLabel(right_frame,width=130,text=f'Turn: {turn.upper()}',font=('Consolas',16),bg_color='white')
    turn_label.place(relx=0.5,rely=0.2,anchor='center')
    if(game_mode=='AI'):
        you_label=ctk.CTkLabel(right_frame,width=130,text='You: X',font=('Consolas',16),bg_color='white')
        you_label.place(relx=0.5,rely=0.3,anchor='center')
    
    quit_button=ctk.CTkButton(right_frame,width=130,text='Quit',font=('Consolas',16),bg_color='white',border_width=0.5,border_color='black',command=lambda: menu(True))
    quit_button.place(relx=0.5,rely=0.4,anchor='center')
    window_width=size+40+10+130
    window_height=size+40
    root.geometry(f'{window_width}x{window_height}+{(int)((screen_width-window_width)/2)}+{(int)((screen_height-window_height)/2)}')

    board=ctk.CTkCanvas(main_frame,width=size,height=size,highlightbackground='black')
    board.pack(padx=10,pady=10)
    draw_board(board)
def draw_board(board):
    for i in range(board_size.get()):
        for j in range(board_size.get()):
            x0=j*cell_size
            y0=i*cell_size
            xi=x0+cell_size
            yi=y0+cell_size
            text_tag=f't{i}:{j}'
            cell_tag=f'{i}:{j}'
            cell=board.create_rectangle(x0,y0,xi,yi,tags=cell_tag,outline='#adadad',fill='white')
            board.create_text((x0+xi)//2, (y0+yi)//2, text='',tags=text_tag, font=('Consolas', 18),fill='#6b6b6b', anchor="center")
            board.tag_bind(text_tag,'<Button-1>',lambda e,move=(i,j): onclick_cell(move))
            board.tag_bind(cell_tag,'<Button-1>',lambda e,move=(i,j): onclick_cell(move))

# UI
def t():
    global n
    n=9
    init()
    real_state[7][2]=-1
    best_move()
    # moves = available_move(real_state)
    # moves = sorted(moves, key=lambda move: evaluate_heuristic(make_move(real_state, move, 1),center_score), reverse=True)
    # print(moves[80])

import utils 
d=98
def j():
    global n
    n=10
    init()
    print(f':ppp:{score_direction(utils.read_board(),6,2,(1,1),1,(min(4,6,2),min(4,9-1-6,9-1-2)))}')
def g():
    print(timeit.timeit(t,number=1))
if __name__ == "__main__":
    # t()

    menu(False)
    root.mainloop()
    # j()


