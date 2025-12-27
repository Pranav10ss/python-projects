# Multiplayer Snake Game
## Description
A real-time **multiplayer Snake game** built with **Python, Pygame**, and **websockets**.
- One player is the **Snake**
- One player is the **Controller**
- Both players connect to the same server on a local network

The Snake must score enough points **within the time limit** to win.  
The Controller moves the food and spawns walls to stop the Snake from winning.

---

## 🎮 Game Roles

### 🐍 Snake
- Controlled using **W A S D**
- Goal: **Score 5 points within the time limit**
- Avoid walls spawned by the controller

### 🎮 Controller
- Move food using **Arrow Keys**
- Spawn walls using **SPACE**
- Goal: **Stop the Snake from winning**

> Roles are **assigned randomly** when players join.

---

## 🧰 Requirements

### ✅ System Requirements
- **Python 3.10 – 3.12**  
  ❗ Python **3.14 is NOT supported** (Pygame font module breaks)

- Both players must be on the **same local network**
- macOS / Linux / Windows supported

---
## 📦 Installation
### 1️⃣ Clone the repository
**macOS / Linux**
```bash
git clone https://github.com/Pranav10R/test-snake.git
```
### 2️⃣ Create a virtual environment
**Windows**
```bash
python3.12 -m venv venv
source venv/bin/activate
```

### 3️⃣ Install dependencies
```bash
pip install pygame
```
```bash
pip install websockets
```
---
## 🚀 Running the Game
### 🖥️ Start the Server (Host Machine)
```bash
cd server
python server.py
```
You should see:
```bash
Server running on 0.0.0.0:5050
```

### 🎮 Start the Client (Each Player)
```bash
cd client
python client.py
```
When prompted, enter the server IP address to start the game.