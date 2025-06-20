import signal
import logging
from datetime import datetime
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from spiders.gouv_spider import GouvSpider

def run_spiders():
    """Lance les spiders SeLoger et Bien'ici"""
    start_time = datetime.now()
    logging.info("Démarrage du scraping...")
    settings = get_project_settings()
    process = CrawlerProcess(settings)
    
    def signal_handler(signum, frame):
        """Gestionnaire pour l'interruption Ctrl+C"""
        logging.info("\nInterruption détectée, nettoyage en cours...")
        process.stop()
    
    # Enregistre le gestionnaire pour SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Ajoute les spiders au processus
    process.crawl(GouvSpider)
    
    # Lance le processus
    try:
        process.start()
    except Exception as e:
        logging.error(f"Erreur lors du scraping: {str(e)}")
    finally:
        duration = datetime.now() - start_time
        logging.info(f"Scraping terminé en {duration}")

if __name__ == "__main__":
    run_spiders()
