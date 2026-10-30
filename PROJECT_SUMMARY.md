# สรุปโครงการ Smart Gallery / Best Shot

สถานะ ณ วันที่ 30 ตุลาคม 2026: ต้นแบบสำหรับ demo ที่เชื่อม Next.js กับ FastAPI
เพื่อประมวลผลรูปจริง โดยใช้ค่าที่เลือกจากการทดลองใน `best_parameters.json`

## เป้าหมายและสถานะ

โครงการช่วยตรวจคุณภาพรูป จัดกลุ่มรูปคล้าย เลือก Best Shot และแนะนำ
KEEP / REVIEW / RECOMMEND_DELETE พร้อมเหตุผล ระบบไม่ลบหรือแก้ไขต้นฉบับ

ทุกหน้าผลลัพธ์ใช้ข้อมูลจากการวิเคราะห์จริงชุดเดียวกันผ่าน AnalysisProvider
แทนการอ่าน mock data แยกตามหน้า ข้อมูล mock เดิมเก็บไว้เป็น reference เท่านั้น

## Flow ที่ใช้งานได้

1. เลือกรูปหลายใบหรือเลือกโฟลเดอร์รวมโฟลเดอร์ย่อย
2. ตรวจ preview จำนวนรูปและขนาดรวม เพิ่ม/เอารูปออกได้
3. กด Analyze ที่ลอยมุมขวาล่าง แม้เลื่อนดูรูปจำนวนมาก
4. ส่งไฟล์และ stable ID ไปยัง FastAPI
5. วิเคราะห์ภาพและแสดงผลที่ Gallery
6. เปิด Groups, Photo Detail และ Summary จากผลชุดเดียวกัน
7. Refresh แล้วคืนผลล่าสุดพร้อม JPEG preview จาก IndexedDB
8. เลือกรูปชุดใหม่เพื่อแทนที่ผลเดิมได้

ระหว่างวิเคราะห์จะล็อกรายการที่เลือก ป้องกันผลกับรูปไม่ตรงกัน หากบางไฟล์เสีย
จะข้ามพร้อมแจ้งเหตุผล หากทุกไฟล์เสียหรือ API เชื่อมต่อไม่ได้จะแสดง error
และเก็บผลเดิมไว้

## Algorithm ปัจจุบัน

- แก้ EXIF orientation, แปลง RGB และ resize ด้านยาวสุดไม่เกิน 1024 px
- Sharpness ใช้ Variance of Laplacian ตาม method ที่เลือกใน JSON
- Exposure ใช้ Y luminance, brightness mean และ dark/highlight clipping
- Underexposed มีลำดับก่อน overexposed ตาม notebook
- ใช้ strategy `exif_time_or_phash` โดยไม่มี SSIM
- รูปมีเวลาใช้ช่วงเวลาถ่ายจัดกลุ่มก่อน โดยคู่ที่ผ่านเวลาไม่ต้องผ่าน pHash
- กลุ่มรูปมีเวลาใช้ complete-link จากระยะเวลาเป็นวินาที
  ช่วงเวลาของกลุ่มตั้งต้นไม่เกิน `exif_time_window_seconds`
- เพิ่ม `timed_phash_threshold` สำหรับรูปมีเวลาที่ห่างเกินกรอบ เริ่มที่ 29
  แยกจาก `phash_threshold` ของรูปไม่มีเวลา (ค่าปัจจุบันให้ยึด JSON)
- คงกลุ่มเวลาเดิมไว้ แล้วรวมทั้งกลุ่ม/รูปเดี่ยวได้เมื่อทุกคู่ข้ามกลุ่มผ่าน
  เวลา หรือเกณฑ์ pHash ของรูปมีเวลา โดยใช้ complete-link ไม่ดึงรูปผ่านลูกโซ่
- เกณฑ์ใหม่ไม่มีเพดานเวลาเพิ่ม ตั้งเป็น `null` หรือลบ key เพื่อกลับไปใช้เวลาอย่างเดียว
- ถ้าทั้งสองรูปไม่มีเวลาหรืออ่านเวลาไม่ได้ ใช้ pHash อย่างเดียวเพื่อจัดกลุ่ม
  เมื่อ `similarity.missing_exif_policy` เป็น `"phash"` โดยใช้ threshold เดิม
- รูปที่มีเวลาจะไม่รวมกลุ่มกับรูปที่ไม่มีเวลา แม้ภาพจะเหมือนกัน
- เปลี่ยน policy เป็น `"strict"` เพื่อกลับไปบังคับเวลาตาม notebook ได้
- รูปไม่มีเวลาใช้ complete-link หรือ average-link ตาม `similarity.linkage`
- ปรับ `phash_threshold` มีผลเฉพาะรูปไม่มีเวลา ส่วนกรอบเวลาและ
  `timed_phash_threshold` มีผลเฉพาะรูปมีเวลา
- โหมดนี้ข้าม Singleton Rescue, Group Merge และ guards เดิมที่พึ่ง pHash
  และใช้ขั้นตอน timed pHash แยกตามกฎข้างต้น
- โหมดเก่า `exif_phash` พร้อม refinements/guards ยังเก็บสำหรับเทียบ notebook
- Quality score normalize ความคมและแสงแล้วถ่วงน้ำหนัก
- เลือกคะแนนสูงสุดเป็น Best Shot เฉพาะรูปในกลุ่ม
- คะแนนใกล้กันน้อยกว่า `best_shot_tie_margin` ให้รูปที่อยู่ใน margin เป็น REVIEW
  และมี `bestShotNeedsReview` ตามฟังก์ชันจริง ไม่ได้ REVIEW ทั้งกลุ่มเสมอไป
- ใช้ quality gap เพื่อให้คำแนะนำสมาชิกที่เหลือในกลุ่ม
- เหตุผลระบุว่ากลุ่มได้จากเวลาอย่างเดียว หรือรวมเพิ่มเติมด้วย timed pHash
- รูปเดี่ยวที่คมและแสงปกติเป็น KEEP นอกนั้น REVIEW

เพิ่มการอ่าน DateTimeOriginal จาก nested Exif IFD เพื่อรองรับไฟล์กล้อง/มือถือจริง

การปรับครั้งล่าสุดเพิ่มเฉพาะ `similarity.timed_phash_threshold` เริ่มต้นที่ 29
โดยรักษาค่า threshold และน้ำหนักที่ผู้ใช้ปรับไว้ ค่าตัวเลขปัจจุบันให้ยึด JSON
หรือหน้าสรุปผล เนื่องจากผู้ใช้ปรับทดสอบได้:

| รายการ                      | ค่า               |
| --------------------------- | ----------------- |
| Sharpness method            | laplacian_score   |
| Sharpness threshold         | 574.4107330939421 |
| Brightness low / high       | 80 / 145          |
| Dark / highlight clipping   | 0.15 / 0.03       |
| Similarity strategy         | exif_time_or_phash |
| Missing EXIF policy         | phash             |
| pHash distance threshold    | ดูค่าปัจจุบันใน JSON |
| Timed pHash threshold       | 29 (ปรับแยกได้)     |
| EXIF time window            | ดูค่าปัจจุบันใน JSON |
| Sharpness / Exposure weight | ดูค่าปัจจุบันใน JSON |
| Duplicate quality gap       | ดูค่าปัจจุบันใน JSON |
| Best Shot tie margin        | ดูค่าปัจจุบันใน JSON |

ถ้า JSON ไม่ระบุ `linkage` จะใช้ `complete` และถ้าไม่ระบุ
`best_shot_tie_margin` จะใช้ `2.0` ตาม default ใน notebook
ค่าที่แสดงเป็น selected ใน notebook ล่าสุดคือ pHash 29, EXIF 30 วินาที,
`linkage: "average"`, น้ำหนัก 0.2/0.8 และ tie margin 0.25
ต้องเปลี่ยนค่าใน `backend/config/best_parameters.json` เองแล้ว restart backend

ถ้าไม่ระบุ `missing_exif_policy` จะใช้ `"strict"` เพื่อรองรับ JSON จาก notebook เดิม
การใช้เวลาก่อน ตามด้วย timed pHash และ fallback เป็นส่วนที่เพิ่มจาก notebook ตามคำขอทดลอง ไม่ได้ใช้ผล Group F1 เดิม
มายืนยันความแม่นยำของโหมดนี้ ส่วน `selection.similarity_policy` เก็บประวัติ
การทดลองเดิม ไม่ใช่ตัวเลือกควบคุม runtime

JSON เป็นแหล่งค่าหลักและถูก validate เมื่อ backend เริ่มทำงาน
หลังเปลี่ยน JSON ต้อง restart backend และวิเคราะห์รูปใหม่ ส่วน development metrics เป็นข้อมูลผลทดลอง
ไม่ใช่คะแนนของรูปที่ผู้ใช้ upload และไม่ใช่ Final Test metrics

## ประเภทภาพใน dataset และผลทำนาย

| โมดูล | Dataset ทั้งชุด | ผลทำนายของแอป |
| --- | --- | --- |
| Sharpness | Sharp, Slight Blur, Motion Blur, Defocus Blur อย่างละ 30 ภาพ รวม 120 | `sharp` / `blur` |
| Exposure | Normal, Underexposed, Overexposed อย่างละ 30 ภาพ รวม 90 | `normal` / `underexposed` / `overexposed` |
| Similarity | 20 กลุ่ม กลุ่มละ 5 ภาพ รวม 100 | Group ID ที่ระบบจัดได้ |

Sharpness ใช้ threshold แยกคม–เบลอ และรวมภาพเบลอทั้ง 3 ประเภทเป็น `blur`
จึงยังไม่ทำนายชนิด Motion Blur หรือ Defocus Blur โดยตรง
Notebook ใน `colab/` เก็บ label เดิมทั้ง 4 ประเภทไว้รายงานผลแยกประเภท
พร้อม Confusion Matrix 2×2 สำหรับคม–เบลอ และ 3×3 สำหรับแสง
ส่วนประเมินตรวจ label และนับภาพครบใน split ที่เลือก ไม่ตัดชนิดเบลอที่ไม่ใช่คำว่า `blur` ทิ้ง

Similarity ใช้ Group ID เพื่อบอกสมาชิกกลุ่ม ไม่ใช่ class แบบ Sharpness/Exposure
ประเมินด้วยคู่ภาพ Same/Different group และ ARI โดยไม่บังคับเลขกลุ่มให้ตรงกับ GT
จำนวนกลุ่มใน dataset เป็นข้อมูลการทดลอง แอปจัดกลุ่มตามรูปที่อัปโหลดจริง

## หน้าจอ

| หน้า         | การทำงาน                                                     |
| ------------ | ------------------------------------------------------------ |
| Upload       | เลือกรูป/โฟลเดอร์ ตรวจรายการ และกดปุ่ม Analyze แบบ floating  |
| Gallery      | รูปจริง filter คำแนะนำ สรุปเบื้องต้น และแจ้งไฟล์ที่ข้าม      |
| Groups       | กลุ่มจริง Best Shot และ empty state เมื่อไม่พบกลุ่ม          |
| Photo Detail | รูปจริง คะแนนคุณภาพ/ความคมชัด ระดับแสง เหตุผล เวลาถ่าย และขนาดภาพ |
| Summary      | จำนวนแต่ละคำแนะนำ พื้นที่ที่อาจประหยัด และค่าที่ใช้วิเคราะห์ |

มีสถานะกำลังคืน session, ยังไม่มีผล และ photo ID ที่ไม่อยู่ใน session ปัจจุบัน

ข้อความหน้าทั่วไปเป็นภาษาไทยที่อ่านง่าย โดยเก็บศัพท์เทคนิค เช่น EXIF, pHash
และชื่อ method ไว้ในส่วนค่าที่ใช้วิเคราะห์ คงชื่อโลโก้ Smart Gallery ไว้
ปุ่มกลับแสดงไอคอนลูกศรพร้อมชื่อสำหรับโปรแกรมอ่านหน้าจอ และกลับไปหน้าต้นทาง
พร้อมตัวกรองและตำแหน่งรูปเดิม และยังใช้ได้หลังรีเฟรชหน้ารายละเอียด
การแปลทำเฉพาะส่วนแสดงผล โดยไม่เปลี่ยน algorithm หรือค่าที่ API ใช้ตัดสิน

แสงแสดงเป็นแถบเทา–เขียว–ส้ม–แดง พร้อมสามเหลี่ยมคว่ำชี้ตำแหน่งและสถานะ
มืด/ปกติ/สว่างเกิน โดยใช้ classification และค่าความสว่าง/พื้นที่มืดหรือสว่างจัด
ที่คำนวณอยู่แล้ว แทนการนำ exposureScore มาแสดงเป็นความเข้มแสง
ตำแหน่งเป็นระดับความรุนแรงภายในแต่ละสถานะ ไม่ใช่เปอร์เซ็นต์หรือแกน luminance ดิบ
ผลเก่าที่ยังไม่มีค่ารายละเอียดใช้ตัวชี้ตามสถานะ และวิเคราะห์ใหม่เพื่อดูตำแหน่งละเอียดได้
ป้ายแนะนำลบใช้พื้นแดงทึบและตัวอักษรขาวเหมือนป้ายคำแนะนำอื่น

## การจัดการไฟล์และ session

- รองรับ JPG/JPEG, PNG, BMP, WebP, HEIC/HEIF
- จำกัด 200 รูป, 30 MiB ต่อไฟล์, 200 MiB รวม
- ใช้ relative path แยกรูปชื่อซ้ำจากคนละโฟลเดอร์
- ใช้ stable ID เชื่อมผลกับรูป แทนการอ้างตำแหน่งใน array
- Backend สร้าง JPEG preview ให้ browser แสดง HEIC/HEIF ได้หลังวิเคราะห์
- ลบไฟล์ชั่วคราวของ backend หลังจบ request
- เก็บผลและ preview ล่าสุดบน IndexedDB ของ browser
- ไม่คืนผลจาก algorithm version เก่าเพื่อป้องกันการเข้าใจผิดว่าเป็นผลใหม่
- รายการไฟล์ก่อนกด Analyze ไม่ได้เก็บข้าม refresh
- กรณี browser storage ใช้ไม่ได้จะแจ้งว่าผลอยู่เฉพาะ tab ปัจจุบัน

## โครงสร้างและเทคโนโลยี

Frontend ใช้ Next.js 16, React 19, TypeScript, Tailwind CSS 4,
Base UI/shadcn และ Lucide โดยรักษา layout และ native system font เดิม

Backend ใช้ FastAPI, Pillow/pillow-heif, OpenCV, NumPy, pandas,
ImageHash และ scikit-learn

```text
app/                 Routes และ global styles
components/          UI, upload และ shared analysis states
contexts/            Analysis session
lib/                 API client, IndexedDB และ utilities
types/               Data contracts
backend/app/         API, parameter validation และ image pipeline
backend/config/      best_parameters.json
backend/tests/       Algorithm และ API regression tests
data/                Historical mock fixtures
```

## การตรวจสอบ

- ESLint แบบ zero warnings และ TypeScript
- Production build ของ Next.js
- Backend regression tests สำหรับ thresholds, EXIF, ทั้งสอง linkage, rescue,
  merge, safety guards, tie margin, ไฟล์เสีย, IDs, orientation, limits และ HEIC
- ทดสอบ fallback เมื่อไม่มีเวลาทั้งคู่ การแยกรูปมีเวลา/ไม่มีเวลาออกจากกัน
  ภาพไม่คล้ายกัน การรักษากรอบเวลา
  การเลือก Best Shot/แนะนำลบ และ policy/เหตุผลที่ API ส่งให้หน้าจอ
- ทดสอบคู่ที่ผ่านเวลาโดยไม่อ่าน pHash และไม่เปลี่ยนเมื่อปรับเกณฑ์ของรูปไม่มีเวลา
  รวมถึงขอบกรอบเวลา 0/30 วินาที การไม่เชื่อมกลุ่มเป็นลูกโซ่ และ upload รูปจริง
- ทดสอบ timed pHash ที่ขอบ threshold, รูปเกินกรอบเวลา, การคงกลุ่มเวลาเดิม
  การแยกค่าของสองชุดรูป การปิดเกณฑ์ใหม่ และคำอธิบายที่ API ส่งกลับ
- เทียบ intermediate stages และ final results กับ core functions
  ใน notebook ล่าสุดด้วยโหมดเก่า `exif_phash` แบบ strict ผ่าน 85 ชุดเปรียบเทียบ
  โดยใช้ features/parameters เดียวกัน โหมดปัจจุบันทดสอบแยกจาก notebook
- มี `backend/tests/check_notebook_parity.py` สำหรับรันทดสอบเทียบ notebook ซ้ำ
- Test parameters แยกจาก JSON ที่ผู้ใช้เปลี่ยนเพื่อให้ทดสอบ regression ได้สม่ำเสมอ
- ตรวจ demo ด้วยรูปทดสอบ รวมถึงการเลือกโฟลเดอร์และการคืน session

คำสั่งและวิธีเปิด frontend/backend อยู่ใน README.md และ backend/README.md

## ข้อจำกัดและงานต่อไป

- ยังไม่มีบัญชีผู้ใช้หรือฐานข้อมูล session ฝั่ง server
- Similarity เปรียบเทียบเป็นคู่ O(n²) จึงจำกัด batch สำหรับ demo
- ภาพที่ไม่มี EXIF จะจัดกลุ่มจากภาพอย่างเดียวในโหมด fallback จึงอาจรวมรูปคล้าย
  ที่ถ่ายคนละเวลาได้ สามารถกลับไปใช้โหมด strict เพื่อบังคับเวลา
- คะแนนเป็น heuristic ไม่ใช่ probability; quality weights และ recommendation
  ยังเป็น provisional rules ตามการทดลอง
- รูปแสงซับซ้อน/ตั้งใจเบลอยังอาจได้คำแนะนำไม่ตรงความต้องการ
- ยังไม่มีการลบ ย้าย หรือจัดการต้นฉบับจริง

งานถัดไปคือประเมินด้วยรูปจริงและ Best Shot ground truth เพิ่มเติม
รวมถึงเพิ่ม background processing และ server-side persistence หากจะใช้งานต่อจาก demo
