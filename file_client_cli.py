import socket
import json
import base64
import logging
import os
import sys
import time
from threading import Thread

# Konfigurasi logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Konfigurasi server
SERVER_HOST = '172.16.16.101'
SERVER_PORT = 7777

class FileClientApplication:
    """Kelas utama aplikasi client file server"""
    
    def __init__(self, server_host=SERVER_HOST, server_port=SERVER_PORT):
        self.server_address = (server_host, server_port)
        self.ensure_dirs_exist()
        
    def ensure_dirs_exist(self):
        """Memastikan direktori yang dibutuhkan sudah ada"""
        if not os.path.exists('files'):
            os.makedirs('files')
            logging.info("Direktori files/ dibuat")
    
    def establish_connection(self):
        """Membuat koneksi ke server"""
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            connection.connect(self.server_address)
            logging.info(f"Terhubung ke server {self.server_address[0]}:{self.server_address[1]}")
            return connection
        except Exception as e:
            logging.error(f"Gagal terhubung ke server: {e}")
            print(f"Error koneksi: {e}")
            return None
    
    def transmit_request(self, request_content):
        """Mengirim request ke server dan mendapatkan respons"""
        connection = self.establish_connection()
        if not connection:
            return None
            
        try:
            # Pastikan request diakhiri dengan marker
            if not request_content.endswith("\r\n\r\n"):
                request_content += "\r\n\r\n"
                
            # Kirim request
            logging.info(f"Mengirim request: {request_content.strip()}")
            connection.sendall(request_content.encode())
            
            # Terima respons
            buffer = bytearray()
            while True:
                chunk = connection.recv(1024)
                if not chunk:
                    break
                    
                buffer.extend(chunk)
                if b"\r\n\r\n" in buffer:
                    break
            
            # Proses respons
            response_data = buffer.decode()
            if "\r\n\r\n" in response_data:
                response_data = response_data.split("\r\n\r\n")[0]
                
            response = json.loads(response_data)
            logging.info("Respons diterima dari server")
            return response
            
        except Exception as e:
            logging.error(f"Error selama komunikasi: {e}")
            print(f"Terjadi kesalahan: {e}")
            return None
        finally:
            connection.close()
    
    def display_files(self):
        """Menampilkan daftar file di server"""
        print("\nMengambil daftar file dari server...")
        request = "LIST"
        response = self.transmit_request(request)
        
        if not response:
            print("Tidak dapat mengambil daftar file.")
            return
            
        if response.get('status') == 'OK':
            files = response.get('data', [])
            print("\n=== Daftar File di Server ===")
            if not files:
                print("Tidak ada file di server.")
            else:
                for index, filename in enumerate(files, 1):
                    print(f"{index}. {filename}")
            print("============================")
        else:
            print(f"Gagal mendapatkan daftar file: {response.get('data', 'Unknown error')}")
    
    def download_file(self):
        """Mengunduh file dari server"""
        filename = input("\nMasukkan nama file yang ingin diunduh: ").strip()
        if not filename:
            print("Nama file tidak boleh kosong.")
            return
            
        print(f"Mengunduh file {filename}...")
        request = f"GET {filename}"
        response = self.transmit_request(request)
        
        if not response:
            print("Tidak dapat mengunduh file.")
            return
            
        if response.get('status') == 'OK':
            try:
                file_content_base64 = response.get('data_file', '')
                file_content = base64.b64decode(file_content_base64)
                
                save_path = os.path.join('files', filename)
                with open(save_path, 'wb') as file:
                    file.write(file_content)
                
                print(f"File '{filename}' berhasil disimpan ke direktori files/")
            except Exception as e:
                logging.error(f"Error menyimpan file: {e}")
                print(f"Gagal menyimpan file: {e}")
        else:
            print(f"Gagal mengunduh file: {response.get('data', 'Unknown error')}")
    
    def upload_file(self):
        """Mengunggah file ke server"""
        file_path = input("\nMasukkan path file yang ingin diunggah: ").strip()
        
        if not file_path:
            print("Path file tidak boleh kosong.")
            return
            
        if not os.path.exists(file_path):
            print(f"File {file_path} tidak ditemukan.")
            return
            
        try:
            filename = os.path.basename(file_path)
            
            # Baca file dan encode ke base64
            with open(file_path, 'rb') as file:
                file_content = file.read()
                file_content_base64 = base64.b64encode(file_content).decode()
            
            # Siapkan data untuk upload
            upload_data = {
                "command": "upload",
                "filename": filename,
                "filedata": file_content_base64
            }
            
            request = json.dumps(upload_data)
            print(f"Mengunggah file {filename}...")
            response = self.transmit_request(request)
            
            if not response:
                print("Tidak dapat mengunggah file.")
                return
                
            if response.get('status') == 'OK':
                print(f"File '{filename}' berhasil diunggah ke server.")
            else:
                print(f"Gagal mengunggah file: {response.get('data', 'Unknown error')}")
                
        except Exception as e:
            logging.error(f"Error dalam upload file: {e}")
            print(f"Terjadi kesalahan saat upload: {e}")
    
    def delete_file(self):
        """Menghapus file di server"""
        filename = input("\nMasukkan nama file yang ingin dihapus: ").strip()
        
        if not filename:
            print("Nama file tidak boleh kosong.")
            return
            
        confirm = input(f"Apakah Anda yakin ingin menghapus file '{filename}'? (y/n): ").lower()
        if confirm != 'y':
            print("Penghapusan dibatalkan.")
            return
            
        print(f"Menghapus file {filename}...")
        request = f"DELETE {filename}"
        response = self.transmit_request(request)
        
        if not response:
            print("Tidak dapat menghapus file.")
            return
            
        if response.get('status') == 'OK':
            print(f"File '{filename}' berhasil dihapus dari server.")
        else:
            print(f"Gagal menghapus file: {response.get('data', 'Unknown error')}")
    
    def show_main_menu(self):
        """Menampilkan menu utama aplikasi"""
        print("\n===== File Client Application =====")
        print(f"Server: {self.server_address[0]}:{self.server_address[1]}")
        
        while True:
            print("\nMenu:")
            print("1. Lihat daftar file di server")
            print("2. Unduh file dari server")
            print("3. Unggah file ke server")
            print("4. Hapus file di server")
            print("5. Keluar aplikasi")
            
            choice = input("\nPilihan Anda (1-5): ")
            
            if choice == '1':
                self.display_files()
            elif choice == '2':
                self.download_file()
            elif choice == '3':
                self.upload_file()
            elif choice == '4':
                self.delete_file()
            elif choice == '5':
                print("\nTerima kasih telah menggunakan aplikasi. Sampai jumpa!")
                break
            else:
                print("Pilihan tidak valid. Silakan pilih 1-5.")


if __name__ == '__main__':
    # Jika ada argumen command line, gunakan sebagai alamat server
    if len(sys.argv) > 2:
        try:
            host = sys.argv[1]
            port = int(sys.argv[2])
            client_app = FileClientApplication(host, port)
        except ValueError:
            print("Format port tidak valid. Menggunakan pengaturan default.")
            client_app = FileClientApplication()
    else:
        client_app = FileClientApplication()
    
    try:
        client_app.show_main_menu()
    except KeyboardInterrupt:
        print("\nProgram dihentikan oleh pengguna.")
    except Exception as e:
        logging.error(f"Error tidak terduga: {e}")
        print(f"Terjadi kesalahan: {e}")