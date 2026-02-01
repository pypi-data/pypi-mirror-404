# Flare Flare 🔥

Give a little flare to your Flask application.

Flask-Flare provides component-style Jinja tags.

## Installation

```bash
pip install flask-flare
```

## Setup
In your __init__.py file of your application
```python
from flask_flare import Flare

flare = Flare()

def create_app(config_name) -> Flask: # or something like this
    """Create a Flask application instance."""
    app = Flask(__name__)
    # initialize extensions
    flare.init_app(app)
    # ... more code
    return app
```
