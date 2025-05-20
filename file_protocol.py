import json
import logging
import shlex
import base64
from file_interface import FileInterface

"""
* class FileProtocol bertugas untuk memproses 
data yang masuk, dan menerjemahkannya apakah sesuai dengan
protokol/aturan yang dibuat
* data yang masuk dari client adalah dalam bentuk bytes yang 
pada akhirnya akan diproses dalam bentuk string
* class FileProtocol akan memproses data yang masuk dalam bentuk
string
"""
class FileProtocol:
    def __init__(self):
        self.file = FileInterface()
    
    def proses_string(self, string_datamasuk=''):
        logging.warning(f"string diproses: {string_datamasuk}")
        
        # Cek apakah input adalah JSON (untuk upload file)
        try:
            json_data = json.loads(string_datamasuk)
            if 'command' in json_data and json_data['command'] == 'upload':
                # Proses upload file
                filename = json_data.get('filename', '')
                filedata = json_data.get('filedata', '')
                
                # Decode file dari base64
                file_content = base64.b64decode(filedata)
                
                # Simpan file menggunakan interface
                result = self.file.upload([filename, file_content])
                return json.dumps(result)
        except ValueError:
            # Bukan JSON, lanjutkan pemrosesan command biasa
            pass
        
        try:
            # Split command dengan shlex untuk handle spasi di nama file
            c = shlex.split(string_datamasuk)
            c_request = c[0].upper()  # Standarisasi ke uppercase
            
            logging.warning(f"memproses request: {c_request}")
            
            # Proses berdasarkan tipe request
            if c_request == 'LIST':
                result = self.file.list([])
                return json.dumps(result)
            
            elif c_request == 'GET':
                if len(c) < 2:
                    return json.dumps(dict(status='ERROR', data='Nama file tidak disebutkan'))
                
                filename = c[1]
                result = self.file.get([filename])
                
                # Jika berhasil dan ada file_content dalam hasil
                if result['status'] == 'OK' and 'file_content' in result:
                    # Encode file content ke base64 dan tambahkan ke response
                    file_content_base64 = base64.b64encode(result['file_content']).decode()
                    result['data_file'] = file_content_base64
                    # Hapus file_content dari response karena sudah direpresentasikan sebagai base64
                    del result['file_content']
                
                return json.dumps(result)
            
            elif c_request == 'DELETE':
                if len(c) < 2:
                    return json.dumps(dict(status='ERROR', data='Nama file tidak disebutkan'))
                
                filename = c[1]
                result = self.file.delete([filename])
                return json.dumps(result)
            
            else:
                return json.dumps(dict(status='ERROR', data='request tidak dikenali'))
                
        except Exception as e:
            logging.error(f"Error: {str(e)}")
            return json.dumps(dict(status='ERROR', data=f'terjadi kesalahan: {str(e)}'))

if __name__=='__main__':
    # Konfigurasi logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Contoh pemakaian
    fp = FileProtocol()
    print(fp.proses_string("LIST"))
    print(fp.proses_string("GET pokijan.jpg"))
    
    # # Contoh upload (simulasi)
    # upload_json = json.dumps({
    #     "command": "upload",
    #     "filename": "test.txt",
    #     "filedata": "SGVsbG8gV29ybGQh"  # "Hello World!" dalam base64
    # })
    # print(fp.proses_string(upload_json))