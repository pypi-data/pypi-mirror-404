# flask_flare/flare.py
import re
from flask import Blueprint
from .extensions import FlareExtension


class Flare:
    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def init_app(self, app):
        # Store extension config if needed
        app.extensions["flask_flare"] = {}

        # Register blueprint for templates/static
        bp = Blueprint(
            "flask_flare",
            __name__,
            template_folder="templates",
            static_folder="static",
            static_url_path="/flask_flare_static"
        )
        app.register_blueprint(bp)

        # Add the Jinja extension
        app.jinja_env.add_extension(FlareExtension)

        # Patch preprocess to support <flare:button> syntax
        original_preprocess = app.jinja_env.preprocess

        def flare_preprocess(source, name, filename=None):
            # Convert <flare:button> -> {% flarebutton %}
            source = re.sub(r"<flare:(\w+)>", r"{% flare\1 %}", source)
            source = re.sub(r"</flare:(\w+)>", r"{% endflare\1 %}", source)
            return original_preprocess(source, name, filename)

        app.jinja_env.preprocess = flare_preprocess

        # Automatically inject CSS into every HTML response
        @app.after_request
        def inject_flare_css(response):
            # Only inject into HTML responses
            content_type = response.headers.get("Content-Type", "")
            if content_type.startswith("text/html"):
                css_link = '<link rel="stylesheet" href="{}">'.format(
                    app.url_for('flask_flare.static', filename='flask_flare.min.css')
                )
                # Inject before </head>
                response.set_data(
                    response.get_data(as_text=True).replace(
                        "</head>", f"{css_link}</head>"
                    )
                )
            return response

        print("🔥 FlareExtension registered with <flare:*> support")
