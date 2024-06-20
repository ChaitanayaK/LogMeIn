import re
import subprocess
import customtkinter as ctk
import tkinter as tk
import cv2
import numpy as np
import mss
import socket
import pyautogui
import keyboard
import threading

ctk.set_appearance_mode("System") 
ctk.set_default_color_theme("green") 

appWidth, appHeight = 600, 300

def get_ipv4_address():
    ipconfig_output = subprocess.check_output(["ipconfig", "/all"]).decode("utf-8")
    pattern = r"Wireless LAN adapter Wi-Fi:(.*?)IPv4 Address[.\s]*:\s*([0-9.]+)"
    match = re.search(pattern, ipconfig_output, re.DOTALL)

    if match:
        ipv4_address = match.group(2)
        return ipv4_address
    else:
        return ':( Couldn\'t Find Your IP Address..'

def startHost(ipAddress):
    HOST = ipAddress
    PORT = 65432

    print(f'IP ADDRESS: {HOST}')

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_socket.bind((HOST, PORT))

    server_socket.listen(1)
    print("Waiting for a connection...")
    connection, address = server_socket.accept()
    print("Connection from:", address)

    pyautogui.FAILSAFE = False
    with mss.mss() as sct:
        while True:
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            img = np.array(screenshot)
            img_encoded = cv2.imencode('.jpg', img)[1].tobytes()
            connection.sendall(img_encoded)
            ack = connection.recv(1024)
            
            if not ack:
                break

            # if ack:
            #     ack_string = ack.decode()
            #     mouse_x, mouse_y, l_click, r_click, key_pressed = map(str, ack_string.split(','))
            #     pyautogui.moveTo(int(mouse_x), int(mouse_y))
            #     if int(l_click):
            #         pyautogui.leftClick()
            #         # pyautogui.mouseDown(button='left')
            #     # else:
            #         # pyautogui.mouseUp(button='left')
            #     if int(r_click):
            #         pyautogui.rightClick()
            #     # else:
            #     if key_pressed: 
            #         keyboard.press_and_release(key_pressed)
            # else:
            #     break

        connection.close()
    server_socket.close()

left_mouse_clicked = False
right_mouse_clicked = False

def startClient(ipAddress, left_mouse_clicked, right_mouse_clicked):
    def mouse_callback(event, x, y, flags, param):
        global left_mouse_clicked, right_mouse_clicked
        if event == cv2.EVENT_LBUTTONDOWN:
            left_mouse_clicked = True
        elif event == cv2.EVENT_RBUTTONDOWN:
            right_mouse_clicked = True

    HOST = ipAddress  
    PORT = 65432

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    client_socket.connect((HOST, PORT))

    cv2.namedWindow('Received Image', cv2.WINDOW_NORMAL)
    cv2.setMouseCallback('Received Image', mouse_callback)

    left_mouse_clicked = False
    right_mouse_clicked = False

    while True:
        img_data = client_socket.recv(1048576)  # Receive up to 1 MB of data

        if not img_data:
            break

        # Decode the image data
        img_np = np.frombuffer(img_data, dtype=np.uint8)
        img_decoded = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

        # Check if the image dimensions are valid
        if img_decoded is None or img_decoded.size == 0:
            print("Invalid image received.")
            continue

        cv2.imshow('Received Image', img_decoded)

        # Resize window to full screen
        cv2.setWindowProperty('Received Image', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)


        mouse_x, mouse_y = pyautogui.position()
        mouse_position = f"{int(mouse_x)},{int(mouse_y)}"

        current_keys = keyboard.get_hotkey_name()
        
        client_socket.sendall(f"{mouse_position},{int(left_mouse_clicked)},{int(right_mouse_clicked)},{current_keys}".encode())


        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    client_socket.close()
    cv2.destroyAllWindows()

class App(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title("LogMeIn")
        self.geometry(f"{appWidth}x{appHeight}+{(1920//2)-(appWidth//2)}+{(1080//2)-(appHeight//2)}")

        self.titleLabel = ctk.CTkLabel(self,
                                    text="LogMeIn",
                                    font=("Arial", 24))  
        self.titleLabel.grid(row=0, column=0, columnspan=2,
                            padx=20, pady=20,
                            sticky="ew")

        self.createHostButton = ctk.CTkButton(self,
                                        text="Create as Host",
                                        font=("Arial", 14),  
                                        command=self.create_host)
        self.createHostButton.grid(row=1, column=0,
                                    padx=20, pady=20,
                                    sticky="ew")

        self.joinClientButton = ctk.CTkButton(self,
                                        text="Join as Client",
                                        font=("Arial", 14),  
                                        command=self.join_client)
        self.joinClientButton.grid(row=1, column=1,
                                    padx=20, pady=20,
                                    sticky="ew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def create_host(self):
        self.withdraw() 
        host_page = HostPage(self)
        address = get_ipv4_address()
        print(address)
        thread = threading.Thread(target=startHost, args=(address,))
        thread.start()
        host_page.mainloop()

    def join_client(self):
        self.withdraw() 
        client_page = ClientPage(self)
        # client_page.protocol("WM_DELETE_WINDOW", self.close_app)
        client_page.mainloop()
    
    def close_app(self):
        self.destroy()

class HostPage(ctk.CTk):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent

        self.title("Host")
        self.geometry(f"{appWidth}x{appHeight}+{(1920//2)-(appWidth//2)}+{(1080//2)-(appHeight//2)}")

        self.backButton = ctk.CTkButton(self,
                                        text="Back",
                                        font=("Arial", 14),  
                                        command=self.go_back)
        self.backButton.grid(row=0, column=0,
                                    padx=20, pady=20,
                                    sticky="nw")  

        self.hostLabel = ctk.CTkLabel(self,
                                    text="Host",
                                    font=("Arial", 30))  
        self.hostLabel.grid(row=0, column=0, columnspan=2,
                            padx=20, pady=20,
                            sticky="ew")
        
        self.addressLabel = ctk.CTkLabel(self, text=get_ipv4_address(),
                                        font=("Arial", 20))
        self.addressLabel.grid(row=1, column=0, columnspan=2,rowspan=2,
                            padx=20, pady=20,
                            sticky="ew")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        

    def go_back(self):
        if self.parent:
            self.parent.deiconify() 
        self.destroy()

class ClientPage(ctk.CTk):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent

        self.title("Client")
        self.geometry(f"{appWidth}x{appHeight}+{(1920//2)-(appWidth//2)}+{(1080//2)-(appHeight//2)}")

        self.backButton = ctk.CTkButton(self,
                                        text="Back",
                                        font=("Arial", 14),  
                                        command=self.go_back)
        self.backButton.grid(row=0, column=0,
                                    padx=20, pady=20,
                                    sticky="nw")  

        self.hostLabel = ctk.CTkLabel(self,
                                    text="Client",
                                    font=("Arial", 30))  
        self.hostLabel.grid(row=0, column=0, columnspan=2,
                            padx=20, pady=20,
                            sticky="ew")
        
        self.textInput = ctk.CTkEntry(self,
                                    placeholder_text="Enter IP Address",
                                    font=("Arial", 14), 
                                    width=30)  
        self.textInput.grid(row=1, column=0, columnspan=2,
                            padx=100, pady=20,
                            sticky="ew")
        
        self.submitButton = ctk.CTkButton(self,
                                        text="Join",
                                        font=("Arial", 14),  
                                        command=self.get_input)
        self.submitButton.grid(row=2, column=0, columnspan=2,
                                    padx=200, pady=20,
                                    sticky="ew") 
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
    def get_input(self):
        ip_address = self.textInput.get()
        startClient(ip_address,left_mouse_clicked, right_mouse_clicked,)

    def go_back(self):
        if self.parent:
            self.parent.deiconify()
        self.destroy() 


if __name__ == "__main__":
    app = App()
    left_mouse_clicked = False
    right_mouse_clicked = False
    app.mainloop()
