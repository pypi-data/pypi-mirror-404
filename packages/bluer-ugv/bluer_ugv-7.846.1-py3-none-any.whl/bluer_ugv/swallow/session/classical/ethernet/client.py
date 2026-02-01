import json
from queue import Empty, SimpleQueue
import socket
from typing import Tuple, Dict, Optional
import struct
import threading
import time

from bluer_ugv.logger import logger
from bluer_ugv.swallow.session.classical.ethernet.command import EthernetCommand
from bluer_ugv.logger import logger


class EthernetClient:
    def __init__(
        self,
        host: str,
        port: int,
        is_server: bool = False,
        reconnect_sec: float = 1.0,
    ):
        self.host = host
        self.port = port
        self.is_server = is_server
        self.reconnect_sec = reconnect_sec

        self._send_queue: SimpleQueue[EthernetCommand] = SimpleQueue()
        self._receive_queue: SimpleQueue[EthernetCommand] = SimpleQueue()

        self._lock = threading.Lock()
        self._sock: Optional[socket.socket] = None
        self._listener: Optional[socket.socket] = None

        logger.info(
            "{} created: host={}, port={}{}.".format(
                self.__class__.__name__,
                self.host,
                self.port,
                ", server" if is_server else "",
            )
        )

    def _close_sockets(self):
        with self._lock:
            if self._sock:
                try:
                    self._sock.close()
                    logger.info(f"{self.__class__.__name__}._sock closed.")
                except Exception as e:
                    logger.warning(e)
                self._sock = None

            if self._listener:
                try:
                    self._listener.close()
                    logger.info(f"{self.__class__.__name__}._listener closed.")
                except Exception as e:
                    logger.warning(e)
                self._listener = None

    def _drain_send_queue(self) -> bool:
        with self._lock:
            sock = self._sock
        if sock is None:
            return False

        while True:
            try:
                cmd = self._send_queue.get_nowait()
            except Empty:
                return True

            try:
                payload = cmd.to_dict()
                # Sending can block; keep it short and safe
                sock.setblocking(True)
                try:
                    self._send_dict(sock, payload)
                finally:
                    sock.setblocking(False)

                logger.info(f"{self.__class__.__name__}: sent {cmd.as_str()}")

            except (ConnectionError, OSError) as e:
                logger.warning(f"{self.__class__.__name__}: send error: {e}")
                self._close_sockets()
                # put back? your choice; here we drop to avoid infinite resend
                return False
            except Exception as e:
                logger.error(e)
                return False

            return True

    def _ensure_connection(self) -> bool:
        """
        Ensure self._sock is a connected TCP socket.
        Returns True if connected.
        """
        with self._lock:
            if self._sock is not None:
                return True

        try:
            if self.is_server:
                # Lazy-create listener
                with self._lock:
                    if self._listener is None:
                        lst = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        lst.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        lst.bind((self.host, self.port))
                        lst.listen(1)
                        lst.settimeout(1.0)  # so thread can exit cleanly
                        self._listener = lst
                        logger.info(
                            f"{self.__class__.__name__}: listening on {self.host}:{self.port}"
                        )

                # Accept
                try:
                    conn, addr = self._listener.accept()
                except socket.timeout:
                    logger.warning("socket timeout.")
                    return False
                except Exception as e:
                    logger.error(e)
                    return False

                conn.setblocking(False)
                with self._lock:
                    self._sock = conn
                logger.info(f"{self.__class__.__name__}: accepted {addr}")

            else:
                # Client connect
                sock = socket.create_connection((self.host, self.port), timeout=2.0)
                sock.setblocking(False)
                with self._lock:
                    self._sock = sock
                logger.info(
                    f"{self.__class__.__name__}: connected to {self.host}:{self.port}"
                )

            return True

        except Exception as e:
            logger.warning(f"{self.__class__.__name__}: connection failed: {e}")
            self._close_sockets()
            return False

    def _recv_dict_blocking(
        self,
        sock: socket.socket,
    ) -> Dict:
        header = self._recv_exact(sock, 4)
        msg_len = struct.unpack("!I", header)[0]
        raw = self._recv_exact(sock, msg_len)
        return json.loads(raw.decode("utf-8"))

    @staticmethod
    def _recv_exact(
        sock: socket.socket,
        n: int,
    ) -> bytes:
        buf = b""
        while len(buf) < n:
            chunk = sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("socket closed")
            buf += chunk
        return buf

    @staticmethod
    def _send_dict(
        sock: socket.socket,
        payload: Dict,
    ) -> None:
        raw = json.dumps(payload).encode("utf-8")
        header = struct.pack("!I", len(raw))
        sock.sendall(header + raw)

    def _try_recv_one(self) -> Tuple[bool, EthernetCommand]:
        """
        Non-blocking receive of exactly one command.
        Uses a small state machine via MSG_PEEK not needed: instead we temporarily
        switch to blocking only when we know bytes are ready.
        """
        with self._lock:
            sock = self._sock
        if sock is None:
            return False, EthernetCommand()

        try:
            # Peek header availability (4 bytes)
            try:
                hdr = sock.recv(4, socket.MSG_PEEK)
            except BlockingIOError:
                return False, EthernetCommand()

            if len(hdr) < 4:
                return False, EthernetCommand()

            msg_len = struct.unpack("!I", hdr)[0]
            total = 4 + msg_len

            try:
                blob = sock.recv(total, socket.MSG_PEEK)
            except BlockingIOError:
                return False, EthernetCommand()

            if len(blob) < total:
                return False, EthernetCommand()

            # Now actually read for real (blocking reads are safe because we already peeked)
            sock.setblocking(True)
            try:
                d = self._recv_dict_blocking(sock)
            finally:
                sock.setblocking(False)

            return True, EthernetCommand.from_dict(d)

        except (ConnectionError, OSError) as e:
            logger.warning(f"{self.__class__.__name__}: recv error: {e}")
            self._close_sockets()
            return False, EthernetCommand()
        except Exception as e:
            logger.warning(f"{self.__class__.__name__}: recv parse error: {e}")
            return False, EthernetCommand()

    def close(self):
        self._close_sockets()

    def process(self):
        connected = self._ensure_connection()
        if not connected:
            time.sleep(self.reconnect_sec)
            return

        # 1) receive at most one per tick (cheap + predictable)
        received, command = self._try_recv_one()
        if received:
            logger.info(
                "{} received {}".format(
                    self.__class__.__name__,
                    command.as_str(),
                )
            )

            self._receive_queue.put(command)

        # 2) drain outbound queue
        self._drain_send_queue()

        time.sleep(0.1)

    def send(
        self,
        command: EthernetCommand,
        drain: bool = False,
    ):
        self._send_queue.put(command)

        logger.info(
            "{}.send: queue += {}".format(
                self.__class__.__name__,
                command.as_str(),
            )
        )

        if drain:
            self._drain_send_queue()
