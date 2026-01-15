import sys
import os

# Add your project directory to the sys.path
project_home = '/home/SEU_USERNAME/ipva'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Set environment variable
os.environ['PORT'] = '8080'

# Import Flask app
from server import app as application
