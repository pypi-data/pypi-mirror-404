# http://127.0.0.1:5000 
import webview
from threading import Thread
import logging
from flask import Flask, request, send_file
import flask_cors
import flask
import random
from datetime import datetime
from threading import Thread
import json
from typing import Literal

TYPE_SIZE = {
    "Samsung Galaxy A14": (420, 940),
    "Samsung Galaxy A34": (430, 930),
    "Samsung Galaxy S21": (430, 960),
    "Samsung Galaxy S22 Ultra": (460, 1000),
    "Samsung Galaxy S23 Ultra": (460, 1000),
    "Xiaomi Redmi Note 10": (430, 960),
    "Xiaomi Redmi Note 12": (440, 980),
    "Xiaomi Poco X5 Pro": (440, 980),
    "Motorola Moto G52": (435, 985),
    "Motorola Moto G84": (435, 970),
    "Asus ROG Phone 6": (450, 1020),
    "Realme 11 Pro": (445, 990),
    "iPhone SE (2022)": (380, 670),
    "iPhone XR": (410, 890),
    "iPhone 11": (410, 890),
    "iPhone 12": (420, 920),
    "iPhone 13": (420, 920),
    "iPhone 14": (420, 920),
    "iPhone 14 Pro": (430, 940),
    "iPhone 15 Pro": (430, 940),
    "Notebook HD 14": (1100, 620),
    "Notebook Full HD 14": (1250, 700),
    "Notebook Full HD 15.6": (1400, 800),
    "Notebook Gamer QHD": (1600, 900),
    "Notebook Gamer 4K": (1900, 1080),
    "MacBook Air M1": (1400, 900),
    "MacBook Air M2": (1450, 950),
    "MacBook Pro 14": (1550, 1000),
    "MacBook Pro 16": (1800, 1150),
    "Monitor HD": (1400, 800),
    "Monitor Full HD": (1600, 900),
    "Monitor Ultrawide FHD": (2000, 850),
    "Monitor QHD (2K)": (1800, 1000),
    "Monitor Ultrawide QHD": (2400, 1000),
    "Monitor 4K": (2600, 1450),
    "Monitor 5K": (3000, 1700),
    "Nintendo Switch Dock": (1600, 900),
    "Nintendo Switch Portátil": (720, 400),
    "Steam Deck": (900, 560),
    "TV HD": (2200, 1250),
    "TV Full HD": (2600, 1450),
    "TV 4K": (3200, 1800),
    "TV 8K": (4200, 2400),
    "Meta Quest 2 (por olho)": (1000, 1050),
    "Meta Quest 3 (por olho)": (1150, 1200),
    "PlayStation VR2 (por olho)": (1100, 1150),
}

DISP_LITERAL = Literal[
    'Asus ROG Phone 6',
    'MacBook Air M1',
    'MacBook Air M2',
    'MacBook Pro 14',
    'MacBook Pro 16',
    'Meta Quest 2',
    'Meta Quest 3',
    'Monitor 4K',
    'Monitor 5K',
    'Monitor Full HD',
    'Monitor HD',
    'Monitor QHD (2K)',
    'Monitor Ultrawide FHD',
    'Monitor Ultrawide QHD',
    'Motorola Moto G52',
    'Motorola Moto G84',
    'Nintendo Switch Dock',
    'Nintendo Switch Portátil',
    'Notebook Full HD 14',
    'Notebook Full HD 15.6',
    'Notebook Gamer 4K',
    'Notebook Gamer QHD',
    'Notebook HD 14',
    'PlayStation 3',
    'PlayStation 4',
    'PlayStation 4 Pro',
    'PlayStation 5',
    'PlayStation VR2',
    'Realme 11 Pro',
    'Samsung Galaxy A14',
    'Samsung Galaxy A34',
    'Samsung Galaxy S21',
    'Samsung Galaxy S22 Ultra',
    'Samsung Galaxy S23 Ultra',
    'Steam Deck',
    'TV 4K',
    'TV 8K',
    'TV Full HD',
    'TV HD',
    'Xiaomi Poco X5 Pro',
    'Xiaomi Redmi Note 10',
    'Xiaomi Redmi Note 12',
    'Xbox One',
    'Xbox One X',
    'Xbox Series S',
    'Xbox Series X',
    'iPhone 11',
    'iPhone 12',
    'iPhone 13',
    'iPhone 14',
    'iPhone 14 Pro',
    'iPhone 15 Pro',
    'iPhone SE (2022)',
    'iPhone XR'
]

def get_html(html, arq=False):
    html_ = ''
    if arq == False:
        if isinstance(html, list):
            for _ in html:
                html_ += str(_) + '\n'
        else:
            html_ += html
    else:
        with open(f'{html}.html', "r", encoding="utf-8") as f:
            conteudo = f.read() 
                
        html_ += conteudo 
        
    return html_
        
def get_js(js, arq=False):
    js_ = ''
    if arq == False:
        if isinstance(js, list):
            for _ in js:
                js_ += str(_) + '\n'
        else:
            js_ += js
    else:
        with open(f'{js}.js', "r", encoding="utf-8") as f:
            conteudo = f.read() 
                
        js_ += conteudo
        
    return js_

def get_css(css, arq=False):
    css_ = ''
    if arq == False:
        if isinstance(css, list):
            for _ in css:
                css_ += str(_) + '\n'
        else:
            css_ += css
    else:
        with open(f'{css}.css', "r", encoding="utf-8") as f:
            conteudo = f.read() 
                
        css_ += conteudo
        
    return css_

class create_object_style:
    def __init__(self, name):
        self.name = f'.{name}'

    def norm(self):
        return self.name

    def focus(self):
        return self.name + ':focus'
    
    def active(self):
        return self.name + ':active'
    
    def hover(self):
        return self.name + ':hover'

    def ativo(self):
        return self.name + '.ativo'


def scale(s):
    return f'scale({s})'

def rgb(r=255, b=255, g=255):
    return f'rgb({r}, {b}, {g})'
def hex_shadow(hex_color):
    hex_color = hex_color.lstrip('#')

    if len(hex_color) == 6: 
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        a = 1  
    elif len(hex_color) == 8:  
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        a = int(hex_color[6:8], 16) / 255
    else:
        raise ValueError("Formato inválido. Use RRGGBB ou RRGGBBAA")

    return f"rgba({r},{g},{b},{a})"

def s(var):
    return f'{var}s'

def deg(var):
    return f'{var}deg'
def px(var):
    return f'{var}px'
def cm(var):
    return f'{var}cm'
def mm(var):
    return f'{var}mm'
def pt(var):
    return f'{var}pt'
def pc(var):
    return f'{var}pc'

def rel(var):
    '''var -> %var '''
    return f'{var}%'
def em(var):
    return f'{var}em'
def rem(var):
    return f'{var}rem'
def ex(var):
    return f'{var}ex'
def ch(var):
    return f'{var}ch'
def vh(var):
    return f'{var}vh'
def vw(var):
    return f'{var}vw'
def vmin(var):
    return f'{var}vmin'
def vmax(var):
    return f'{var}vmax'


def hr_shadow(size=px(2), color='#ccc', box_shadow = (0, 'low', px(5)), shadow_color = hex_shadow('#000000')):
    sh = box_shadow[1]
    if sh == 'low': sh = 2
    elif sh == 'top' : sh = -2
    sh = px(sh)
    return f'<hr style="border: none; border-top: {size} solid {color}; box-shadow: {box_shadow[0]} {sh} {box_shadow[2]} {shadow_color};">'
def hr_boder_style(size=px(2), color='#000', boder_top = 'solid'):
    return f'<hr style"border: none; border-top: {size} {boder_top} {color};">'
def br_style(style):
    return f'<br style={style}>'
def hr_style(style):
    return f'<hr style={style}>'

def translate(x, y):
    return f'translate({x}, {y})'
def custom(*values):
    return ' '.join(values)

from .server import *
from .ehtml import *
from .css import *
from .script import *
from .obj import *


    
def logObject():
  return '''
<script>
(function () {
    function formatarArgs(args) {
        return args.map(a => {
            try {
                if (typeof a === "object") {
                    return JSON.stringify(a);
                }
                return String(a);
            } catch {
                return "[objeto não serializável]";
            }
        }).join(" ");
    }

    function enviarParaFlask(tipo, dadosBrutos) {
        const mensagem = Array.isArray(dadosBrutos)
            ? formatarArgs(dadosBrutos)
            : dadosBrutos;

        fetch("/WeavexPy/events/__JSLOG__", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                tipo: tipo,
                mensagem: mensagem,
                url: window.location.href,
                userAgent: navigator.userAgent,
                timestamp: Date.now()
            })
        });
    }

    function interceptarConsole(nome) {
        const original = console[nome];
        console[nome] = function (...args) {
            enviarParaFlask(nome, args);
            original.apply(console, args);
        };
    }

    interceptarConsole("log");
    interceptarConsole("error");
    interceptarConsole("warn");
    interceptarConsole("info");

    window.onerror = function (msg, url, linha, coluna, erro) {
        enviarParaFlask("window.onerror", {
            msg, url, linha, coluna, erro: (erro || "").toString()
        });
    };

    window.addEventListener("unhandledrejection", event => {
        enviarParaFlask("unhandledrejection", {
            motivo: event.reason ? String(event.reason) : "desconhecido"
        });
    });

})();
</script>
'''

class Scope:
    def __init__(self, parent):
        '''## Scope

The **Scope** module is responsible for structuring the body of an HTML page. It acts as a layout manager, allowing you to build and organize the page hierarchy prior to rendering.

---
title -> <title>{self.title}</title>
lang -> <html lang="{self.lang}">
charset -> <meta charset="{self.charset}">
---

## Functions

### `add(element)`
Adds a new element to the page body.

- **Purpose:** Insert HTML components sequentially or hierarchically.  
- **Parameter:**  
  - `element`: object, string, or structure representing HTML.  
- **How it works:** Stores the element internally, keeping insertion order.  
- **Common uses:**  
  - Dynamic page construction  
  - Adding divs, text blocks, menus, scripts  
  - Incrementally expanding the layout  

---

### `__str__()`
Defines or replaces the entire page content.

- **Purpose:** Establish the final layout of the page.  
- **How it works:** Clears the existing structure and sets a new body.  
- **Common uses:**  
  - Template configuration  
  - Layout reset  
  - Base page setup'''
        self.scope = ''
        self.head = ''
        self.title = 'Document'
        self.charset = 'UTF-8'
        self.lang = 'en'
        self.set = self.__str__
        self.parent = parent
        self.style = ''
        
    def add_head(self, elment):
        self.head += f'{element}\n'
    def add_style(self, css):
      self.style += str(css) + '\n'
    def add(self, element) : 
        '''### `add(element)`
Adds a new element to the page body.

- **Purpose:** Insert HTML components sequentially or hierarchically.  
- **Parameter:**  
  - `element`: object, string, or structure representing HTML.  
- **How it works:** Stores the element internally, keeping insertion order.  
- **Common uses:**  
  - Dynamic page construction  
  - Adding divs, text blocks, menus, scripts  
  - Incrementally expanding the layout  '''
        self.scope += str(element) + '\n'
    def __str__(self) :
        '''### `__str__()`
Defines or replaces the entire page content.

- **Purpose:** Establish the final layout of the page.  
- **How it works:** Clears the existing structure and sets a new body.  
- **Common uses:**  
  - Template configuration  
  - Layout reset  
  - Base page setup'''
        return f'''<!DOCTYPE html>
<html lang="{self.lang}">
<head>
    <meta charset="{self.charset}">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.jsdelivr.net/npm/brython@3.11.0/brython.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/brython@3.11.0/brython_stdlib.js"></script>
    {self.head}
    <title>{self.title}</title>
{self.parent.all_style}
<style>
{self.style}
</style>
</head>
<script type="module" src="https://pyscript.net/releases/2025.11.1/core.js"></script>
<body onload="brython()">
{self.scope}
{logObject()}
</body>
</html>'''

class ObjectPage:
    def __init__(self, page_base:list) : 
        '''## ObjectPage

The **ObjectPage** module provides a simple and structured way to add elements to a page created with `@Window().add_page()`.  
It uses a base structure defined by **`page_base`**, which serves as the initial template or layout for the page.

This class behaves like a *page builder*: it collects elements and finally produces a consolidated output — typically HTML.

---

## Methods

### `add(element)`
Adds a new element to the page.

- **Purpose:** insert components into the page layout using the `page_base` model.  
- **Parameter:**  
  - `element`: HTML content, structured object, text block, or custom component.  
- **How it works:** the element is appended internally while preserving order and structure.  
- **Common uses:**  
  - Incremental page construction  
  - Adding HTML blocks, widgets, text, or scripts  
  - Modular composition of layouts

---

### `__str__()`
Finalizes and returns the page representation.

- **Purpose:** generate the final page output based on all added elements.  
- **Returns:** usually a string containing the assembled HTML.  
- **How it works:**  
  - Merges `page_base` with the collected elements  
  - Produces the final layout for rendering  
- **Common uses:**  
  - HTML generation in frameworks  
  - Rendering pages in the browser  
  - Exporting the finished layout'''
        self.page_base = page_base

    def add(self, element) : 
        '''### `add(element)`
Adds a new element to the page.

- **Purpose:** insert components into the page layout using the `page_base` model.  
- **Parameter:**  
  - `element`: HTML content, structured object, text block, or custom component.  
- **How it works:** the element is appended internally while preserving order and structure.  
- **Common uses:**  
  - Incremental page construction  
  - Adding HTML blocks, widgets, text, or scripts  
  - Modular composition of layouts'''
        self.page_base.append(element)
    def __str__(self):
        '''### `__str__()`
Finalizes and returns the page representation.

- **Purpose:** generate the final page output based on all added elements.  
- **Returns:** usually a string containing the assembled HTML.  
- **How it works:**  
  - Merges `page_base` with the collected elements  
  - Produces the final layout for rendering  
- **Common uses:**  
  - HTML generation in frameworks  
  - Rendering pages in the browser  
  - Exporting the finished layout'''
        html = ''
        for e in self.page_base:
            html += f'{e}\n'
            
        return html

class Application:
    def __init__(self, obj, port='5000', size = DISP_LITERAL):
        '''
The **Application** class is responsible for creating and managing the main application window using **PyWebView**.  
It centralizes the configuration of visual appearance, layout, window behavior, window state, and backend–frontend integration through JavaScript APIs.

The following attributes define the initial state and capabilities of the window.

---

## Main Attributes

### 🖼️ **Visual Settings**
| Attribute | Description |
|----------|-------------|
| `title` | Window title displayed in the title bar. |
| `background_color` | Background color (hex). |
| `transparent` | Enables window transparency. |
| `vibrancy` | Enables vibrancy effect (macOS). |
| `frameless` | Removes the default window frame. |
| `text_select` | Enables or disables text selection inside the HTML. |

---

### 🧩 **Content & Integration**
| Attribute | Description |
|----------|-------------|
| `html` | Initial HTML content. |
| `js_api` | Object exposed to JavaScript for backend ↔ frontend communication. |

---

### 📏 **Dimensions**
| Attribute | Description |
|----------|-------------|
| `width` | Initial width of the window. |
| `height` | Initial height of the window. |
| `min_size` | Minimum window size (width, height). |
| `resizable` | Allows window resizing. |

---

### 📍 **Position**
| Attribute | Description |
|----------|-------------|
| `x` | Window X position (optional). |
| `y` | Window Y position (optional). |

---

### ⚙️ **Behavior & State**
| Attribute | Description |
|----------|-------------|
| `fullscreen` | Starts in fullscreen mode. |
| `hidden` | Starts with the window hidden. |
| `minimized` | Starts minimized. |
| `on_top` | Keeps the window always on top. |
| `confirm_close` | Prompts confirmation when closing. |

---

### 🖱️ **Drag & Interaction**
| Attribute | Description |
|----------|-------------|
| `easy_drag` | Allows dragging by clicking any part of the window. |
| `draggable` | Enables only specific draggable areas. |
'''
        self.all_style = ''
        self.pages = {'home.page' : ''}
        self.app = Server(f'{__name__}.{obj}:{port}', self.pages)
        self.port = port
        self.size = size
        self.title = 'WeavexPy Window'
        self.html = None
        self.js_api = None
        self.width = 800
        self.height = 600
        self.x = None
        self.y = None
        self.resizable = True
        self.fullscreen = False
        self.min_size = (200, 100)
        self.hidden = False
        self.frameless = False
        self.easy_drag = True
        self.minimized = False
        self.on_top = False
        self.confirm_close = False
        self.background_color = '#FFFFFF'
        self.text_select = False
        self.draggable = True
        self.vibrancy = None
        self.transparent = False
        self.YesWindow = False
        self.onFlaskLog = True
        
        

        
    def midia_format(self, src, mimetype='image/png'):
        return self.app.__img__(src, mimetype)
    def add_style(self, css_style) : 
        '''
## add_style(css_style)

The **add_style** method adds a global CSS style to the entire application.  
It injects CSS rules into the PyWebView window, enabling consistent theming, layout standardization, and the ability to override default styles across all rendered pages.

---

## Parameters

### `css_style`
A string containing valid CSS rules.

- **Type:** `str`
- **Example:**
  ```css
  body { background-color: #222; color: white; }
'''
        self.all_style += f'<style>\n{css_style}\n</style>'
    
    def page(self, route):
        '''## page(route)

The **page** method allows the creation of complex pages using internal application functions.  
Unlike `form_page`, which is intended for simple and static layouts, this method is suited for dynamic pages that rely on Python processing or internal logic.

A route is registered and linked to a Python callback function responsible for generating or assembling the page content.

---

## Parameters

### `route`
Name or path of the page route.

- **Type:** `str`
- **Purpose:** identifies the internal page handled by a function.

---

## How it works
- The route is associated with an internal callback function.
- When the page is accessed, the function is executed.
- The callback can:
  - build HTML dynamically  
  - query databases  
  - process application data  
  - generate components programmatically  
- Ideal for non-static, logic-driven pages.

---

## Common uses
- Dynamic pages with frequently updated data.
- Dashboards, admin panels, and logic-heavy screens.
- Programmatically generated HTML or components.
- Interfaces that react to internal application states.'''
        def dec(func):
            nonlocal route
            route = str(route) if route in ['/', 'home'] else 'home'
            self.pages[str(route)] = func  
            
        return dec
    
    def form_page(self, route):
        '''## form_page

The **form_page** method allows the creation of simple pages within the application.  
It is particularly recommended for forms, static content, or lightweight layouts that do not require complex components.

It registers a new page that can be rendered or navigated to within the main window.

---

## Parameters

### `route`
Identifier for the page.

- **Type:** `str`
- **Purpose:** route the page.

---

## How it works
- The page is stored inside the window instance.
- It can be rendered at any moment.
- Ideal for:
  - small forms
  - registration screens
  - simple static interfaces

---

## Common uses
- Creating lightweight static pages.
- Building login or registration forms.
- Organizing multiple screens inside a single window.'''
        def dec(func):
            nonlocal route
            route = str(route) if route in ['/', 'home'] else 'home'
            html = ''
            page = func(page = ObjectPage([]))
            if isinstance(page, list) :
                for pg in page :
                    html += f'{pg}\n'
            else : html = str(page)
            
            html_format = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.jsdelivr.net/npm/brython@3.11.0/brython.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/brython@3.11.0/brython_stdlib.js"></script>
    <title>Document</title>
{self.all_style}
</head>
<script type="module" src="https://pyscript.net/releases/2025.11.1/core.js"></script>
<body onload="brython()">
{html}
{logObject()}
</body>
</html>'''
            
            self.pages[str(route)] = html_format
            
        return dec
            
    def CreateWindow(self, **kwargs):
        if isinstance(self.size, tuple):
            self.width = self.size[0]
            self.height = self.size[1]
        elif isinstance(self.size, str):
            if self.size in TYPE_SIZE:
                self.width = int(TYPE_SIZE[self.size][0] / 1.3)
                self.height = int(TYPE_SIZE[self.size][1] / 1.3)
            else:
                print(f'not {self.size} in TYPE_SIZE')

        self.YesWindow = True
        window = webview.create_window(
            url = f'http://127.0.0.1:{self.port}',
            title=self.title,
            html=self.html,
            js_api=self.js_api,
            width=self.width,
            height=self.height,
            x=self.x,
            y=self.y,
            resizable=self.resizable,
            fullscreen=self.fullscreen,
            min_size=self.min_size,
            hidden=self.hidden,
            frameless=self.frameless,
            easy_drag=self.easy_drag,
            minimized=self.minimized,
            on_top=self.on_top,
            confirm_close=self.confirm_close,
            background_color=self.background_color,
            text_select=self.text_select,
            draggable=self.draggable,
            vibrancy=self.vibrancy,
            transparent=self.transparent,
            **kwargs
            )
        return window
                
    def run(self, **kwargs):
        '''Executa a aplicação, inicializando todas as páginas, estilos e rotas configuradas.'''
        if not self.onFlaskLog:
            logging.getLogger('werkzeug').setLevel(logging.ERROR)
            
        if self.YesWindow == False:
            self.app.veri().run('0.0.0.0', self.port, debug=False)
        else:
            def server():
                self.app.veri().run('0.0.0.0', self.port, debug=False)
                
            Thread(target=server, daemon=True).start()
                
            def qt():

                webview.start(**kwargs)


            qt()
