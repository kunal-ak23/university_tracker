import logging

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # add logs here
        logger = logging.getLogger(__name__)
        logger.info("CoreConfig is ready and signals are being imported.")

        # Import signals
        import core.signals
        logger.info("Signals have been successfully imported.")

