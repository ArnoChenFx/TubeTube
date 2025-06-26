import logging
import threading
from flask import Flask, render_template
from flask_socketio import SocketIO
from settings import Settings, Config
from yt_downloader import DownloadManager


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class WebApp(Settings, DownloadManager):
    def __init__(self):
        Settings.__init__(self)
        DownloadManager.__init__(self, config_folder=self.config_folder)
        self.app = Flask(__name__)
        self.app.secret_key = Config.SECRET_KEY
        self.socketio = SocketIO(self.app, cors_allowed_origins=Config.SOCKETIO_CORS_ALLOWED_ORIGINS)

        @self.app.route("/")
        def handle_index():
            return render_template("index.html")

        @self.socketio.on("connect")
        def handle_connect():
            threading.Thread(target=self.client_connect, daemon=True).start()

        @self.socketio.on("download")
        def handle_download(item_info):
            threading.Thread(target=self.download_stuff, daemon=True, args=(item_info,)).start()

        @self.socketio.on("remove_items")
        def handle_remove_items(item_ids):
            threading.Thread(target=self.remove_items, args=(item_ids,), daemon=True).start()

        @self.socketio.on("cancel_items")
        def handle_cancel_items(item_ids):
            threading.Thread(target=self.cancel_items, args=(item_ids,), daemon=True).start()

        @self.socketio.on("retry_items")
        def handle_retry_items(item_ids):
            threading.Thread(target=self.retry_download, args=(item_ids,), daemon=True).start()

    def client_connect(self):
        self.socketio.emit(
            "update_folder_locations",
            {"audio": self.audio_locations, "video": self.video_locations},
        )
        self.socketio.emit("update_download_list", self.all_items)

    def download_stuff(self, item_info):
        folder_name = item_info.get("folder_name")
        if folder_name not in self.folder_locations:
            logging.warning(f"Invalid folder selected: {folder_name}")
            return

        download_settings = self.folder_locations.get(folder_name, {})
        item_info["download_settings"] = download_settings
        self.add_to_queue(item_info)

    def run_app(self):
        try:
            self.socketio.run(self.app, host="0.0.0.0", port=5000)
        except KeyboardInterrupt:
            logging.info("Application shutdown requested...")
        except Exception as e:
            logging.error(f"Application shutdown due to error: {e}")
        finally:
            # Ensure proper shutdown of the DownloadManager
            self.shutdown()
            logging.info("Application shutdown complete")

    def get_app(self):
        # # Register shutdown handlers for WSGI servers
        # @self.app.teardown_appcontext
        # def shutdown_session(exception=None):
        #     self.shutdown()
        #     logging.info("Application context torn down")
        return self.app


web_app = WebApp()
if __name__ == "__main__":
    web_app.run_app()
else:
    app = web_app.get_app()
