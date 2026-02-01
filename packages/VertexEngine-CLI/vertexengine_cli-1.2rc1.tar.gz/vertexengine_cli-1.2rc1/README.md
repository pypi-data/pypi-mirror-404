# VertexEngine-CLI
VertexEngine CLI adds CLI support to VertexEngine.
Commands:
`python -m vertex init game` - provides a game template 
`python -m vertex build [path]` - build an exe with 2 flags:
`--onefile, --windowed`

### Change Logs (1.1), NEW!
1.1:
 - Added 2 new commands!:
    vertex remove {filepath}
    vertex upload {flags}
## How to install Pyinstaller
Step 1. Type in:
pip install pyinstaller

Step 2. Wait a few min, don't worry if it takes 1 hr or more, it will finish

Step 3. How to use pyinstaller
type:
python -m PyInstaller --onefile *.py

There are flags:
--noconsole > disables the console when you run the app
--onefile > compress all of the code into one file
--icon > the *.ico file after you type it will be set as the app icon.

## How to install VertexEngine/Vertex:

Step 1:
Type in
pip install VertexEngine-CLI

Step 2: Wait a few min, don't worry if it takes 1 hr or more, it will finish

Step 3: Where to start?
Read the documentations. Also copy the following template:
-------------------------------------------------------
from VertexEngine.engine import GameEngine
from VertexEngine import VertexScreen
from VertexEngine.audio import AudioManager
from VertexEngine.scenes import Scene
import pygame
import sys
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

class Main(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self.width = engine.width
        self.height = engine.height

    def update(self):
        pass

    def draw(self, surface):
        VertexScreen.Draw.rect(VertexScreen.Draw, surface, (0, 255, 0), (-570, 350, 5000, 500))

if __name__ == '__main__':
    app = QApplication(sys.argv) # <- create app
    engine = GameEngine(fps=60, width=1920, height=1080, title="Screen.com/totally-not-virus") # <- initialize a1080p window at 60 FPS

    engine.setWindowTitle('Screen.com/totally-not-virus') # <- name the app
    engine.setWindowIcon(QIcon('snake.ico')) # <- icon
    engine.show() # <- show window

    main_scene = Main(engine) # <- intialize the scene
    engine.scene_manager.add_scene('main', main_scene) # <- name scene
    engine.scene_manager.switch_to('main') # <- switch to the main scene pls

    app.exec()

The following template creates a window with a green rectangle (the ground.)

Pygame or PyQt6 systems are compatible with Vertex so you can use pygame collision system or PyQt6's UI system in VertexEngine.

## Help
The documentation is in the following link:
[Project Documentation](https://vertexenginedocs.netlify.app/) for help.

## Dependencies
Vertex obviously has heavy dependencies since it's a game engine, the following requirements are:

| Dependency       | Version                              |
|------------------|--------------------------------------|
| PyQt6            | >=6.7                                |   
| Pygame           | >=2.0                                |
| Python           | >=3.10                               |

## About Me ❔
I Am a solo developer in Diliman, Quezon City that makes things for fun :)
77 Rd 1, 53 Rd 3 Bg-Asa QC
Email:
FinalFacility0828@gmail.com
## 📄 License
VertexEngine/Vertex is Managed by the MIT License. This license allows others to tweak the code. However, I would like my name be in the credits if you choose this as your starting ground for your next library.