import os, requests, h5py, io
import numpy as np

class H5VirtualDrive:

    def __init__(self, h5_filename, url=None, overwrite=False):
        self.h5_filename = h5_filename
        self.url = url
        self.overwrite = overwrite
        self._prepare_and_open()

    def _download_file(self,filename, url, overwrite=False):
        # ตรรกะจัดการชื่อไฟล์ซ้ำ
        if not overwrite and os.path.exists(filename):
            base, extension = os.path.splitext(filename)
            counter = 1
            # วนลูปหาชื่อไฟล์ที่ไม่ซ้ำ
            while os.path.exists(f"{base}({counter}){extension}"):
                counter += 1
            filename = f"{base}({counter}){extension}"
            print(f"พบไฟล์ชื่อซ้ำ... เปลี่ยนชื่อไฟล์เป็น: {filename}")
        print(f"กำลังดาวน์โหลดไฟล์จาก: {url}...")
        
        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            print(f"ดาวน์โหลดเสร็จสิ้น: {filename}")
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการดาวน์โหลด: {e}")
            return None
            
        return filename
    def _prepare_and_open(self):
        if not os.path.exists(self.h5_filename):
            print(f"ไม่พบไฟล์ {self.h5_filename} กำลังเริ่มดาวน์โหลดอัตโนมัติ...")
            self._download_file(self.h5_filename, self.url)
        elif not self.overwrite and (self.url != None) :            
            self.h5_filename = self._download_file(self.h5_filename,self.url, self.overwrite)
            
        try:
            self.hdf = h5py.File(self.h5_filename, 'r')
            print(f"Virtual Drive พร้อมใช้งาน: {self.h5_filename}")
        except Exception as e:
            print(f"ไม่สามารถเปิดไฟล์ได้ [{self.h5_filename}] : {e} ")
    
    def get_data(self, internal_path):
        """
        ดึงข้อมูลจาก H5 ตาม Path:
        - ถ้าเป็นไฟล์เสียง (.wav, .mp3, .ogg) คืนค่าเป็น bytes ดิบ (ใช้ .getvalue())
        - ถ้าเป็นไฟล์อื่นๆ คืนค่าเป็น io.BytesIO (buffer)
        """
        if internal_path not in self.hdf:
            print(f"ไม่พบ Path: {internal_path}")
            return None

        item = self.hdf[internal_path]
        if isinstance(item, h5py.Dataset):
            # 1. ดึงข้อมูลจาก Dataset ออกมาเป็น Bytes
            data = item[()]
            if isinstance(data, np.ndarray):
                # ถ้าข้อมูลใน H5 ถูกเก็บเป็นเลข 0-255 (uint8) อยู่แล้ว
                if data.dtype == np.uint8: raw_bytes = data.tobytes() # ใช้แบบเร็วได้เลย
                else: raw_bytes = data.astype('uint8').tobytes() # ถ้าถูกเก็บมาเป็นประเภทอื่น ให้แปลงก่อนเพื่อไม่ให้โครงสร้างไฟล์เสีย
            else: raw_bytes = bytes(data)
            
            # 2. สร้าง Buffer
            buffer = io.BytesIO(raw_bytes)     
            
            # 3. ตรวจสอบนามสกุลไฟล์
            audio_extensions = ('.wav', '.mp3', '.ogg')
            if internal_path.lower().endswith(audio_extensions):
                # ส่งกลับเป็น bytes ดิบ (สำหรับ Audio() หรือ tf.audio.decode_wav)
                return buffer.getvalue()
            
            # ส่งกลับเป็น buffer (สำหรับ pd.read_csv)
            return buffer
            
        return None
