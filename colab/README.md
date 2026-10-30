# Smart Gallery — Colab presentation

ชุดนี้ใช้ flow ปัจจุบันของแอปสำหรับอธิบายและทดลองก่อนแสดงผลบนเว็บ
ไม่ต้องเปิด backend และไม่มี custom UI: เลือกโฟลเดอร์ → ประมวลผล → รูปพร้อมข้อความสั้น ๆ

## ไฟล์

- `presentation_results.ipynb`: โค้ดพร้อมคำอธิบายตาม flow และตัวทดลองโฟลเดอร์
- `best_parameters.json`: สำเนาค่าจาก `backend/config/best_parameters.json` ณ วันที่จัดทำ

Notebook ต้นฉบับใน Downloads เก็บไว้ตามเดิม ไม่มีการนำผลเก่ามาปะปนเป็นผลของ flow ใหม่

## วางใน Google Drive และเปิด Colab

1. อัปโหลดโฟลเดอร์ `colab/` นี้ไปไว้ที่ `MyDrive/Mini-Project-Image/colab/`
2. วางภาพในโฟลเดอร์ที่เลือกได้ เช่น `MyDrive/Mini-Project-Image/dataset/similarity/`
   ใช้โฟลเดอร์อื่นบน Drive ก็ได้ ไม่ต้องมี labels สำหรับ demo
3. เปิด notebook ด้วย Google Colab แล้วรัน cell ตามลำดับ หรือ Run all
4. อนุญาต Mount Drive และแก้ `PROJECT_ROOT` ในส่วน 2 ถ้าใช้ path อื่น
5. เมื่อถึงส่วน 8 พิมพ์หมายเลขโฟลเดอร์หรือวาง path ที่ Copy จาก sidebar ของ Colab
   หรือกำหนด `IMAGE_FOLDER` ในส่วน 2 ไว้ก่อนเพื่อไม่ต้องตอบคำถาม
6. ดูรูปและคะแนนใน output ธรรมดา ปรับ `MAX_PREVIEW_IMAGES` เพื่อเพิ่ม/ลดรูปที่แสดง

หาก JSON หาย ระบบจะบอก path ที่ต้องแก้ ไม่แอบใช้พารามิเตอร์เก่าจาก module_outputs
การ Run all ค่าเริ่มต้นไม่เขียนทับ JSON หรือผลทดลองเดิม

## Output ทดลองภาพ

แต่ละรูปแสดงชื่อ, Quality, Sharpness, สถานะแสง, Best Shot ถ้ามี และคำแนะนำสั้น ๆ
จัดแสดงตามกลุ่ม มีตารางสรุปทั้งหมดและรายการไฟล์เสียที่ข้าม
คะแนน Exposure ไม่ถูกแสดงเป็นระดับความสว่าง เพราะ 100 คะแนนอาจได้ label ต่างกัน

- Demo: ไม่เกิน 200 ภาพ, 30 MiB ต่อไฟล์, 200 MiB รวม เหมือนหน้าอัปโหลดของแอป
- ประมวลผลชื่อไฟล์ซ้ำคนละ subfolder ได้ โดยยึด path
- `MAX_PREVIEW_IMAGES` จำกัดเฉพาะการแสดงผล ไม่ตัดภาพออกจากการประมวลผล
- ดูกลุ่มเดียว: `show_photo_results(demo_results, group_id='G001')`
- เปลี่ยนโฟลเดอร์: แก้ `IMAGE_FOLDER` แล้วรัน cell demo ส่วน 8 ซ้ำ
- บันทึกผล: `EXPORT_DEMO_RESULTS=True` สร้าง CSV/JSON ในโฟลเดอร์ผลใหม่ที่มี timestamp

## Flow และพารามิเตอร์

รูปมีเวลาใช้ Complete-link จากเวลาถ่ายก่อน คงกลุ่มเดิมไว้แล้วรวมทั้งกลุ่ม/รูปเดี่ยว
ได้เมื่อทุกคู่ข้ามกลุ่มผ่านเวลา OR `timed_phash_threshold` โดยใช้ Complete-link
รูปไม่มีเวลาใช้ `phash_threshold` กับ `linkage` ของตัวเอง และไม่รวมข้ามชุดกับรูปมีเวลา
Best Shot / near-tie / quality-gap ใช้ฟังก์ชันจากแอป ไม่ใช้ SSIM หรือ legacy Rescue/Merge

ส่วน 10 ให้แก้ `TEST_PARAMS` แล้วเปิด `RUN_FOLDER_PARAMETER_TEST` เพื่อดูผลเทียบโฟลเดอร์เดิม
การบันทึกผลทดสอบสร้างไฟล์ใหม่ ไม่เปลี่ยน JSON ของแอป
หากปรับค่าในแอปภายหลัง ให้คัดลอก JSON ล่าสุดมาแทนไฟล์ในชุดนี้อย่างชัดเจนก่อนใช้งาน

## Ground Truth และผลการทดลอง

ส่วน 9 ปิดไว้เริ่มต้น เปิด `RUN_GROUND_TRUTH_EVALUATION=True` เมื่อมี dataset พร้อม
`dataset/metadata/labels.csv` ตาม schema เดิม: filename, source, scene_id, group_id, split
และ blur_label / exposure_label / best_shot สำหรับโมดูลที่มี GT
`source` อ้างชื่อโฟลเดอร์ sharpness / exposure / similarity / unique ตาม dataset เดิม

### ประเภทภาพและ class ที่ประเมิน

| โมดูล | Dataset ทั้งชุด | ผลที่ระบบทำนาย |
| --- | --- | --- |
| Sharpness | Sharp, Slight Blur, Motion Blur, Defocus Blur อย่างละ 30 ภาพ รวม 120 | `sharp` / `blur` |
| Exposure | Normal, Underexposed, Overexposed อย่างละ 30 ภาพ รวม 90 | `normal` / `underexposed` / `overexposed` |
| Similarity | 20 กลุ่ม กลุ่มละ 5 ภาพ รวม 100 | Group ID ของกลุ่มที่ระบบจัดได้ |

`blur_label` เก็บชื่อประเภทเดิมได้ครบทั้ง 4 ประเภท ระบบประเมินแปลง Slight Blur,
Motion Blur และ Defocus Blur เป็น `blur` พร้อมแจกแจงผลตรวจคม–เบลอแยกตามประเภทเดิม
รองรับช่องว่าง ขีดกลาง ขีดล่าง ตัวพิมพ์เล็ก/ใหญ่ และ label เดิม `blur`
ถ้า label หายหรือไม่รู้จัก ส่วนประเมินจะหยุดพร้อมแจ้งแทนการตัดภาพนั้นออกเงียบ ๆ
ผล Sharpness เป็นการจำแนก 2 class ไม่ใช่การทำนายชนิดเบลอ 4 class

ส่วน 9 แสดง Confusion Matrix แบบจำนวนและเปอร์เซ็นต์รายแถว: Sharpness 2×2,
Exposure 3×3 พร้อม Precision/Recall/F1 และ support ราย class
จำนวนในรายงานยึด split ที่เลือก จึงอาจน้อยกว่าจำนวน dataset ทั้งชุดในตาราง
Similarity ประเมินคู่ภาพ Same/Different group และ Adjusted Rand Index (ARI)
จากกลุ่มสุดท้าย โดยหมายเลขกลุ่ม GT กับกลุ่มที่ระบบสร้างไม่จำเป็นต้องตรงกัน
ภาพ unique และภาพที่ไม่ถูกจัดกลุ่มนับเป็น singleton แยกกัน

เลือก `EVALUATION_SPLIT` เป็น development, final_test หรือ all; ใช้ development เท่านั้น
เมื่อเปิด `RUN_PARAMETER_COMPARISON` เพื่อเทียบค่าของส่วน 10
Grouping วัดจากกลุ่มสุดท้ายของ similarity+unique ไม่ใช้ pair flags เป็นตัวแทนกลุ่ม
ภาพ GT ที่หายหรืออ่านไม่ได้จะทำให้ส่วนประเมินหยุด เพื่อไม่ให้รายงานคะแนนบนข้อมูลที่ขาด
การประเมิน dataset ทั้งหมดไม่ติดขีดจำกัด upload batch ของ demo

ตัวเลขใน JSON และผลใน notebook เก่าเป็นประวัติการทดลองคนละ flow
ไม่มีการอ้าง Group F1 เดิมเป็นความแม่นยำของ flow ใหม่ ค่าจริงต้องรันใหม่กับ dataset
Final Test เดิมเคยถูกเปิดดูระหว่างพัฒนา จึงเป็น retrospective diagnostics
คำแนะนำ KEEP/REVIEW/RECOMMEND_DELETE เป็น output การทำงาน ไม่ใช่ deletion accuracy

## ตรวจผลตรงกับแอป

จาก `backend/` รัน `.venv/bin/python -m unittest discover -s tests -v`
มี tests อ่าน core functions จาก notebook ฉบับนี้แล้วเทียบผลกับแอป
ข้อมูลทดสอบอัตโนมัติเป็น regression fixtures ไม่ใช่คะแนนจาก dataset จริงของอาจารย์

เครื่องมือนี้ทำงานใน Colab แต่การตรวจในเครื่องไม่สามารถทดแทนการอนุญาต Google Drive
หรือการรัน dataset จริงในบัญชีผู้ใช้ได้
