import requests
from multiprocessing import Process
from threading import Thread
import time
import socket
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Server:
    def __init__(self) -> None:
        """
        Constructor for Server class.
        """
        self.port = None
        self.server_process = None
        self.server_thread = None

    def start(self, local_db_file: str, port: Optional[int] = None, use_threading: bool = False) -> int:
        """
        Start the local server.

        Args:
            local_db_file: Path to the local database file.
            port: Optional port number to use for the server. If not provided,
                an open port will be found.

        Returns:
            The port number the server is running on.
        """
        self.port = port if port else self.__find_open_port()
        if use_threading:
            self.server_thread = Thread(target=start_server, 
                                        args=(local_db_file, self.port), 
                                        daemon=True)
            self.server_thread.start()
        else:
            self.server_process = Process(target=start_server, 
                                          args=(local_db_file, self.port), 
                                          daemon=True)
            self.server_process.start()

        # Wait for the server to start
        self.__wait_for_server(f"http://127.0.0.1:{self.port}/ping")
        logger.debug(f"[LOCAL] Local server running on port {self.port}.")

        return self.port

    def __wait_for_server(self, url: str, timeout: int = 5) -> None:
        """
        Waits until the server is ready by polling the specified URL.
        :param url: The URL to poll.
        :param timeout: Maximum time to wait in seconds.
        """
        start_time = time.time()
        while True:
            try:
                response = requests.get(url, timeout=1)
                if response.status_code == 200:
                    logger.debug("[LOCAL] Server is ready.")
                    return
            except requests.ConnectionError:
                pass

            if time.time() - start_time > timeout:
                raise TimeoutError(f"[LOCAL] Server did not start within {timeout} seconds.")

            time.sleep(0.1)

    def __find_open_port(self) -> int:
        """
        Finds an open port on localhost.
        :return: An open port number.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))  # Bind to port 0 to get an open port
            return s.getsockname()[1]

def start_server(local_db_file: str, port: int) -> None:
    """
    Starts a local FastAPI server to handle REST API requests.
    :param local_db_file: The path to the local database file.
    :param port: The port to start the server on.
    """
    import uvicorn
    from .app import create_app
    logger.debug(f"[LOCAL] Starting local server on port {port}...")

    app = create_app(local_db_file)
    
    # Configure uvicorn to be quiet
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=port, 
        log_level="error",  # Minimize logging
        access_log=False    # Disable access logs
    )

