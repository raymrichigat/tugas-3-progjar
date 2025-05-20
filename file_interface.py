import os
import json
import base64
import logging
from glob import glob

class FileInterface:
    def __init__(self):
        # Pastikan direktori files/ ada
        if not os.path.exists('files/'):
            os.makedirs('files/')
        os.chdir('files/')
        logging.info("FileInterface: Working directory set to files/")

    def list(self, params=[]):
        """
        Menampilkan daftar file di direktori files/
        """
        try:
            # Ambil semua file di direktori files/
            filelist = glob('*.*')
            logging.info(f"FileInterface: Found {len(filelist)} files")
            return dict(status='OK', data=filelist)
        except Exception as e:
            logging.error(f"FileInterface: Error listing files: {str(e)}")
            return dict(status='ERROR', data=str(e))

    def get(self, params=[]):
        """
        Mengambil file dari direktori files/
        Parameter:
        - params[0]: nama file yang akan diambil
        """
        try:
            if not params or len(params) == 0:
                return dict(status='ERROR', data='Nama file tidak disebutkan')
            
            filename = params[0]
            if not os.path.isfile(filename):
                return dict(status='ERROR', data=f'File {filename} tidak ditemukan')
            
            logging.info(f"FileInterface: Retrieving file {filename}")
            
            # Baca file dalam mode binary
            with open(filename, 'rb') as fp:
                file_content = fp.read()
                
            # Untuk kompatibilitas dengan protokol, kita berikan file content langsung
            # dan di file_protocol.py akan di-encode ke base64
            return dict(status='OK', data=f'File {filename} berhasil diambil', file_content=file_content)
            
        except Exception as e:
            logging.error(f"FileInterface: Error retrieving file: {str(e)}")
            return dict(status='ERROR', data=str(e))

    def upload(self, params=[]):
        """
        Menyimpan file ke direktori files/
        Parameter:
        - params[0]: nama file
        - params[1]: konten file dalam bentuk bytes
        """
        try:
            if len(params) < 2:
                return dict(status='ERROR', data='Parameter tidak lengkap')
            
            filename = params[0]
            file_content = params[1]  # Sudah dalam bentuk bytes
            
            # Cek apakah nama file valid
            if not filename or '/' in filename or '\\' in filename:
                return dict(status='ERROR', data='Nama file tidak valid')
            
            logging.info(f"FileInterface: Uploading file {filename} ({len(file_content)} bytes)")
            
            # Tulis file ke disk
            with open(filename, 'wb') as fp:
                fp.write(file_content)
                
            return dict(status='OK', data=f'File {filename} berhasil disimpan')
            
        except Exception as e:
            logging.error(f"FileInterface: Error uploading file: {str(e)}")
            return dict(status='ERROR', data=str(e))

    def delete(self, params=[]):
        """
        Menghapus file dari direktori files/
        Parameter:
        - params[0]: nama file yang akan dihapus
        """
        try:
            if not params or len(params) == 0:
                return dict(status='ERROR', data='Nama file tidak disebutkan')
            
            filename = params[0]
            if not os.path.isfile(filename):
                return dict(status='ERROR', data=f'File {filename} tidak ditemukan')
            
            logging.info(f"FileInterface: Deleting file {filename}")
            
            # Hapus file
            os.remove(filename)
            
            return dict(status='OK', data=f'File {filename} berhasil dihapus')
            
        except Exception as e:
            logging.error(f"FileInterface: Error deleting file: {str(e)}")
            return dict(status='ERROR', data=str(e))

if __name__=='__main__':
    # Konfigurasi logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Contoh penggunaan
    f = FileInterface()
    print(f.list())
    
    # # Contoh get file
    # result = f.get(['example.txt'])
    # print(f"Get result status: {result['status']}")
    
    # # Contoh upload file
    # content = b"Hello, this is a test file!"
    # upload_result = f.upload(['test_upload.txt', content])
    # print(f"Upload result: {upload_result}")
    
    # # Memastikan file terupload dengan baik
    # print(f.list())
    
    # # Contoh delete file
    # delete_result = f.delete(['test_upload.txt'])
    # print(f"Delete result: {delete_result}")
    
    # # Memastikan file terhapus
    # print(f.list())