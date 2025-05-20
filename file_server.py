import socket
import threading
import logging
import time
import sys
import json
from file_protocol import FileProtocol

# Konfigurasi logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

fp = FileProtocol()

class ProcessTheClient(threading.Thread):
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address
        threading.Thread.__init__(self)
        
    def run(self):
        buffer = bytearray()
        is_data_complete = False
        try:
            while True:
                data = self.connection.recv(4096)  # Memperbesar buffer untuk menerima file besar
                if data:
                    buffer.extend(data)
                    # Cek apakah data sudah selesai (baik untuk format command atau JSON)
                    if b"\r\n\r\n" in buffer:
                        is_data_complete = True
                        break
                    # Deteksi JSON request (untuk upload file yang mungkin lebih besar)
                    try:
                        test_data = buffer.decode('utf-8')
                        if '{' in test_data and '}' in test_data:
                            json_start = test_data.find('{')
                            json_end = test_data.rfind('}') + 1
                            if json_start >= 0 and json_end > json_start:
                                test_json = test_data[json_start:json_end]
                                json.loads(test_json)  # Coba parse sebagai JSON
                                is_data_complete = True
                                break
                    except:
                        # Jika gagal parse, mungkin data belum lengkap, lanjutkan menerima
                        pass
                else:
                    # Tidak ada data lagi
                    break
                    
            if is_data_complete:
                # Proses data yang sudah lengkap
                d = buffer.decode('utf-8')
                
                # Bersihkan terminasi jika ada
                if "\r\n\r\n" in d:
                    d = d.split("\r\n\r\n")[0]
                
                logging.info(f"Menerima data dari {self.address}: Command/data size {len(d)} bytes")
                
                # Proses string menggunakan FileProtocol
                hasil = fp.proses_string(d)
                
                # Pastikan hasil diakhiri dengan marker
                if not hasil.endswith("\r\n\r\n"):
                    hasil = hasil + "\r\n\r\n"
                    
                logging.info(f"Mengirim respons ke {self.address}: Hasil size {len(hasil)} bytes")
                self.connection.sendall(hasil.encode())
                
        except Exception as e:
            logging.error(f"Error saat memproses client {self.address}: {str(e)}")
        finally:
            logging.info(f"Koneksi dari {self.address} ditutup")
            self.connection.close()

class Server(threading.Thread):
    def __init__(self, ipaddress='0.0.0.0', port=7777):
        self.ipinfo = (ipaddress, port)
        self.the_clients = []
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        threading.Thread.__init__(self)
        
    def run(self):
        logging.info(f"Server berjalan di ip address {self.ipinfo}")
        self.my_socket.bind(self.ipinfo)
        self.my_socket.listen(5)  # Meningkatkan backlog untuk mendukung lebih banyak koneksi
        while True:
            try:
                self.connection, self.client_address = self.my_socket.accept()
                logging.info(f"Koneksi baru dari {self.client_address}")
                
                # Set timeout untuk koneksi klien
                self.connection.settimeout(60)  # 60 detik timeout
                
                # Buat thread untuk memproses klien
                clt = ProcessTheClient(self.connection, self.client_address)
                clt.start()
                self.the_clients.append(clt)
                
                # Bersihkan thread klien yang sudah selesai
                self.clean_finished_threads()
                
            except Exception as e:
                logging.error(f"Error dalam server loop: {str(e)}")
    
    def clean_finished_threads(self):
        """Membersihkan thread klien yang sudah selesai"""
        self.the_clients = [c for c in self.the_clients if c.is_alive()]

def main():
    # Ambil port dari argument jika ada
    port = 7777  # Default port sesuai dengan client
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Format port tidak valid. Menggunakan port default 7777")
    
    # Jalankan server
    svr = Server(ipaddress='0.0.0.0', port=port)
    logging.info(f"File Server akan berjalan di port {port}")
    
    try:
        svr.start()
        # Simpan main thread tetap hidup
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        logging.info("Server dihentikan oleh pengguna")
    except Exception as e:
        logging.error(f"Error tidak terduga: {str(e)}")

if __name__ == "__main__":
    main()