"""
*basic_usage.py*

Example code for a really basic use of the Chanina framework.

The **app** can (and should) be created in its own module.
Assigning **app.celery** to its own **celery** variable is just so we don't have to scratch our head to run the 'celery -A ... worker' command.

**backend** and **broker** are for the celery app initialization. If you don't know how to setup **celery** __go here .
"""
import os
from typing import Optional

from chanina.core.chanina import ChaninaApplication, WorkerSession

backend = os.environ.get("CELERY_BACKEND", "redis://localhost:6379/0")
broker = os.environ.get("CELERY_BROKER", "amqp://localhost:5672")

app = ChaninaApplication(
    __name__,
    headless=False,
    backend=backend,
    broker=broker,
    browser_name="firefox"
)

celery = app.celery


@app.feature('check-google')
def check_google(session: WorkerSession, args: Optional[dict]):
    """
    This is just a basic example on how your workflow using chanina would look like.
    Here we are just checking if google is accessible.
    Every feature has a 'WorkerSession' passed to it, and can also receive optional 'args'.
    """
    session.new_page()
    try:
        session.navigate.goto("https://google.com")
    except Exception as e:
        print(f"Error: could not access google.com : {e}")
