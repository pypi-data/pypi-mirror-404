import requests
import threading
from collections import deque
from typing import List
import socket
import time

class UIDManager:
    __slots__ = (
        'fetch_batch_size', 'report_batch_size', '_prefetch_threshold', 'local_ip',
        '_session', '_url_request', '_url_complete', '_base_payload',
        '_buffer', '_buffer_lock', '_is_prefetching',
        '_pending_success', '_pending_failed', '_pending_count',
        '_report_lock', '_is_reporting', 'total_uid_count',
        '_reporter_thread', '_stop_reporter', '_report_interval'
    )
    
    def __init__(self, master_ip: str, master_port: int, node_id: str, 
                 fetch_batch_size: int = 10, report_batch_size: int = 10,
                 prefetch_ratio: float = 0.2, report_interval: float = 2.0
        ):
        self.fetch_batch_size = int(fetch_batch_size)
        self.report_batch_size = int(report_batch_size)
        self._prefetch_threshold = max(1, int(prefetch_ratio * self.fetch_batch_size))
        self.local_ip = self._get_local_ip()
        self.total_uid_count = 0
        self._report_interval = report_interval
        print(f"local_ip: {self.local_ip}")
        
        # Reuse HTTP connections (avoids TCP handshake per request)
        self._session = requests.Session()
        
        # Cache URLs and base payload (avoid repeated dict/string creation)
        base_url = f"http://{master_ip}:{master_port}"
        self._url_request = f"{base_url}/request_list_of_uids"
        self._url_complete = f"{base_url}/complete_task"
        self._base_payload = {"slave_ip": self.local_ip, "node_id": node_id}
        
        # 任务获取缓存与锁 - use deque for O(1) popleft
        self._buffer: deque = deque()
        self._buffer_lock = threading.Lock()
        self._is_prefetching = False
        
        # 任务上报缓存与锁
        self._pending_success: List[str] = []
        self._pending_failed: List[str] = []
        self._pending_count = 0  # Track count to avoid len() calls
        self._report_lock = threading.Lock()
        self._is_reporting = False
        
        # Dedicated reporter thread
        self._stop_reporter = threading.Event()
        self._reporter_thread = threading.Thread(target=self._reporter_loop, daemon=True)
        self._reporter_thread.start()

    def _get_local_ip(self) -> str:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    # --- 迭代逻辑 ---
    def __iter__(self):
        return self

    def __next__(self) -> str:
        # First check if buffer has items (fast path)
        with self._buffer_lock:
            if self._buffer:
                uid = self._buffer.popleft()
                remaining = len(self._buffer)
            else:
                uid = None
                remaining = -1  # Signal to fetch
        
        if remaining >= 0:
            # Check prefetch outside lock (reduces lock hold time)
            self._maybe_prefetch(remaining)
            return uid  # type: ignore
        
        # Buffer empty - fetch synchronously (outside lock to not block other threads)
        self._fetch_uids()
        
        with self._buffer_lock:
            if not self._buffer:
                raise StopIteration
            return self._buffer.popleft()

    def _maybe_prefetch(self, buffer_len: int):
        """Trigger background prefetch when buffer is running low."""
        if buffer_len <= self._prefetch_threshold and not self._is_prefetching:
            self._is_prefetching = True
            threading.Thread(target=self._prefetch_async, daemon=True).start()

    def _prefetch_async(self):
        """Background prefetch to avoid blocking iteration."""
        try:
            self._fetch_uids()
        finally:
            self._is_prefetching = False

    def _fetch_uids(self):
        """Fetch UIDs from master. Thread-safe, can be called without holding lock."""
        payload = {**self._base_payload, "num_uids": self.fetch_batch_size}
        try:
            resp = self._session.post(self._url_request, json=payload, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                uids = data.get("uids")
                if uids:
                    with self._buffer_lock:
                        self._buffer.extend(uids)
                    print(f"✅ 拉取成功: {len(uids)} 条, Master 剩余: {data.get('remaining')}")
                    self.total_uid_count += len(uids)
            else:
                print(f"❌ 拉取失败: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"❌ 网络异常 (Refill): {e}")
        

    def mark_complete(self, success_uids: List[str], failed_uids: List[str]):
        """Non-blocking: just add to pending lists, reporter thread handles flushing."""
        added = len(success_uids) + len(failed_uids)
        if added == 0:
            return
        with self._report_lock:
            self._pending_success.extend(success_uids)
            self._pending_failed.extend(failed_uids)
            self._pending_count += added
        # Never block here - dedicated reporter thread handles all network I/O
    
    def _reporter_loop(self):
        """Dedicated background thread that periodically flushes reports."""
        while not self._stop_reporter.is_set():
            try:
                # Check if we have pending reports
                should_flush = False
                with self._report_lock:
                    should_flush = self._pending_count > 0
                
                if should_flush:
                    self._do_flush_reports()
                
                # Wait for interval or until stopped
                self._stop_reporter.wait(timeout=self._report_interval)
            except Exception as e:
                print(f"❌ Reporter loop error: {e}")
                time.sleep(1)  # Avoid tight loop on error
        
        # Final flush on shutdown
        self._do_flush_reports()
    
    def _do_flush_reports(self) -> bool:
        """Internal flush method called by reporter thread."""
        with self._report_lock:
            if self._is_reporting or self._pending_count == 0:
                return True
            
            self._is_reporting = True
            # Swap references instead of copy+clear
            success_list = self._pending_success
            failed_list = self._pending_failed
            count = self._pending_count
            self._pending_success = []
            self._pending_failed = []
            self._pending_count = 0
        
        # Perform Network IO OUTSIDE the lock
        payload = {
            **self._base_payload,
            "successful_uids": success_list,
            "failed_uids": failed_list
        }
        
        try:
            resp = self._session.post(self._url_complete, json=payload, timeout=10)
            resp.raise_for_status()
            # print(f"🚀 Batch Report Success: {len(success_list)} OK, {len(failed_list)} Failed")
            return True
        except Exception as e:
            print(f"❌ Report Failed: {e}")
            # Put them back for retry (prepend to preserve order)
            with self._report_lock:
                self._pending_success = success_list + self._pending_success
                self._pending_failed = failed_list + self._pending_failed
                self._pending_count += count
            return False
        finally:
            with self._report_lock:
                self._is_reporting = False
    
    def stop(self):
        """Stop the reporter thread gracefully."""
        self._stop_reporter.set()
        if self._reporter_thread.is_alive():
            self._reporter_thread.join(timeout=15)  # Wait for final flush

    def flush_reports(self) -> bool:
        """Public method to manually flush reports. Delegates to internal method."""
        return self._do_flush_reports()