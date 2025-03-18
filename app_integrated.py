import os
import json
import uuid
import random
import re
import copy
import time
import threading
import logging
import traceback
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_from_directory, flash, make_response
from werkzeug.utils import secure_filename
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests
from flask import Response

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ibiza-ai-secret-key-2025')
# Configurar el servidor para no usar caché en archivos estáticos
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
# Crear directorios si no existen
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data'), exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Rutas principales
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/products')
def products():
    return render_template('products.html')

# Iniciar el servidor
if __name__ == '__main__':
    app.run(debug=True)
