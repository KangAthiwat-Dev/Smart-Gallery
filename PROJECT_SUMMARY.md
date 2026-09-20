# สรุปโครงการ Best Shot

> สถานะโครงการ ณ วันที่ 20 กันยายน 2026  
> เวอร์ชันปัจจุบัน: `0.1.0` — Frontend Prototype

## 1. ภาพรวมโครงการ

Best Shot เป็นต้นแบบแอปพลิเคชันบนมือถือสำหรับช่วยผู้ใช้ตรวจสอบและจัดระเบียบ
คลังรูปภาพ โดยระบบมีเป้าหมายที่จะวิเคราะห์คุณภาพของรูป ตรวจจับรูปที่คล้ายกัน
เลือกรูปที่ดีที่สุดในแต่ละกลุ่ม และเสนอรูปที่ควรเก็บ ตรวจสอบ หรือลบ

แนวคิดสำคัญของโครงการคือระบบทำหน้าที่เป็นผู้ช่วยตัดสินใจเท่านั้น
และจะไม่ลบรูปของผู้ใช้โดยอัตโนมัติ

ในสถานะปัจจุบันโครงการเป็น frontend prototype ยังไม่มี backend และยังไม่มี
กระบวนการวิเคราะห์ภาพจริง ข้อมูลผลวิเคราะห์ทั้งหมดมาจาก mock data ที่กำหนดไว้
ล่วงหน้า เพื่อใช้ทดสอบหน้าจอ user flow และรูปแบบการนำเสนอข้อมูล

## 2. วัตถุประสงค์

- ออกแบบ user flow สำหรับการเลือกรูปและตรวจสอบผลวิเคราะห์
- แสดงคะแนนคุณภาพ ความคมชัด และแสงของแต่ละรูป
- แสดงกลุ่มรูปภาพที่มีความคล้ายกัน
- ระบุ Best Shot ภายในกลุ่มรูปที่คล้ายกัน
- แบ่งคำแนะนำเป็น Keep, Review และ Recommend Delete
- สรุปพื้นที่จัดเก็บที่อาจประหยัดได้
- ยืนยันแนวทาง UX ก่อนเชื่อมต่อระบบประมวลผลภาพจริง

## 3. User flow ปัจจุบัน

1. ผู้ใช้เลือกรูปหลายไฟล์หรือ drag and drop ลงใน upload area
2. ระบบแสดง preview ชื่อไฟล์ ขนาดไฟล์ และจำนวนรูปภายใน browser
3. ผู้ใช้สามารถลบรูปบางรูปออกจากรายการหรือล้างรายการทั้งหมดได้
4. ผู้ใช้เลือก **View sample analysis** เพื่อเปิดผลวิเคราะห์ตัวอย่าง
5. ผู้ใช้ตรวจสอบผลผ่าน Gallery, Similar Photos, Photo Detail และ Summary

ไฟล์ที่ผู้ใช้เลือกจะถูกใช้สำหรับ preview ภายใน browser เท่านั้น ไม่มีการ upload
ออกจากเครื่อง และยังไม่ได้ถูกเชื่อมกับผลวิเคราะห์ใน mock data

## 4. หน้าจอและเส้นทาง

| Route | หน้าที่ |
| --- | --- |
| `/` | เลือกรูป แสดง preview และเข้าสู่ผลวิเคราะห์ตัวอย่าง |
| `/gallery` | แสดงรูปทั้งหมดและกรองตามประเภทคำแนะนำ |
| `/groups` | แสดงกลุ่มรูปที่คล้ายกันและ Best Shot ของแต่ละกลุ่ม |
| `/photo/[id]` | แสดงรายละเอียด คะแนน และเหตุผลของคำแนะนำรายรูป |
| `/summary` | สรุปจำนวนรูปแต่ละประเภทและพื้นที่ที่อาจประหยัดได้ |
| Not-found fallback | แสดงหน้า Photo not found สำหรับ route หรือรูปที่ไม่มีข้อมูล |

หน้า `/photo/[id]` ใช้ `generateStaticParams` เพื่อสร้างหน้าของรูปใน mock data
ล่วงหน้าในขั้นตอน production build

## 5. ฟีเจอร์ที่ทำงานแล้ว

- เลือกรูปหลายไฟล์จาก file picker
- Drag and drop รูปภาพ
- กรองไฟล์ที่ไม่ใช่รูปภาพ
- ป้องกันการเพิ่มไฟล์เดิมซ้ำในรายการ
- แสดง local preview ผ่าน object URL
- คืนหน่วยความจำของ object URL เมื่อเอารูปออกหรือออกจากหน้า
- รองรับ mouse, keyboard และ screen reader ใน upload area
- กรอง Gallery ตาม Keep, Review และ Recommend Delete
- แสดง Similarity Group และ Best Shot
- แสดง Quality, Sharpness และ Exposure score
- แสดงเหตุผลของคำแนะนำรายรูป
- คำนวณพื้นที่จัดเก็บที่อาจประหยัดได้จาก mock data
- Responsive layout สำหรับหน้าจอมือถือและเดสก์ท็อป
- ใช้ Next Image optimization กับรูปตัวอย่างจาก Picsum
- มี branded favicon และหน้า not-found ของโครงการ

## 6. สถานะข้อมูลและโมเดล

Mock data อยู่ใน `data/mock-data.ts` และ type definitions อยู่ใน
`types/analysis.ts`

ประเภทคำแนะนำที่รองรับ:

```ts
type Recommendation = "KEEP" | "REVIEW" | "RECOMMEND_DELETE";
```

ข้อมูลรูปแต่ละรายการประกอบด้วย:

- ID, ชื่อไฟล์ และ URL ของรูป
- คะแนนความคมชัด
- คะแนนแสง
- คะแนนคุณภาพรวม
- ID ของกลุ่มรูปที่คล้ายกัน
- สถานะ Best Shot
- คำแนะนำและเหตุผลประกอบ
- ขนาดไฟล์โดยประมาณ

## 7. เทคโนโลยี

- Next.js 16 App Router
- React 19
- TypeScript
- Tailwind CSS 4
- Base UI และ shadcn UI primitives
- Lucide React icons

Typography ใช้ native system font stack เพื่อให้หน้าตาใกล้เคียง mobile
application บนแต่ละระบบปฏิบัติการ และไม่ต้องดาวน์โหลด web font เพิ่มเติม

## 8. โครงสร้างโปรเจกต์

```text
app/
├── gallery/page.tsx
├── groups/page.tsx
├── photo/[id]/page.tsx
├── summary/page.tsx
├── globals.css
├── icon.svg
├── layout.tsx
├── not-found.tsx
└── page.tsx

components/
├── ui/                  # Generated UI primitives
├── upload/
│   └── photo-upload.tsx
├── app-header.tsx
├── photo-card.tsx
└── status-badge.tsx

data/
└── mock-data.ts

lib/
└── utils.ts

types/
└── analysis.ts
```

โครงสร้างยังคงเรียบง่ายให้เหมาะกับขนาดของ prototype โดยแยก routing,
application components, UI primitives, mock data และ domain types ออกจากกัน

## 9. Quality checks

คำสั่งที่เตรียมไว้:

```bash
npm run lint
npm run typecheck
npm run check
npm run build
```

สถานะการตรวจล่าสุด:

- ESLint ผ่านโดยกำหนดให้ไม่มี warning
- TypeScript typecheck ผ่าน
- Production build ผ่านด้วย webpack
- Routes ของ mock photo ถูก prerender เป็น static HTML
- Browser smoke test ผ่านสำหรับ navigation, filters, detail page และ not-found
- ไม่พบ console error หรือ warning ระหว่าง smoke test

## 10. ข้อจำกัดปัจจุบัน

- ยังไม่มี backend หรือ API
- ยังไม่มี image processing pipeline จริง
- รูปที่ผู้ใช้เลือกยังไม่เชื่อมกับผลวิเคราะห์
- ไม่มี authentication หรือ user account
- ไม่มี database หรือการบันทึก analysis session
- ไม่มีการลบ ย้าย หรือแก้ไขไฟล์จริง
- รูปตัวอย่างต้องเชื่อมต่ออินเทอร์เน็ตเพื่อโหลดจาก Picsum
- ยังไม่มี automated unit, integration หรือ end-to-end tests
- คะแนนและคำแนะนำทั้งหมดเป็นข้อมูลตัวอย่าง ไม่ควรใช้ตัดสินใจลบรูปจริง

## 11. แนวทางพัฒนาระยะถัดไป

1. กำหนด input/output contract ของ image analysis service
2. พัฒนา sharpness, blur และ exposure analysis
3. เพิ่ม similarity detection และ clustering
4. กำหนดหลักเกณฑ์เลือก Best Shot ภายในแต่ละกลุ่ม
5. เชื่อม upload flow กับ analysis session จริง
6. เพิ่มสถานะ uploading, processing, success และ error
7. เพิ่มฐานข้อมูลหรือ storage สำหรับผลวิเคราะห์
8. เพิ่ม confirmation flow ก่อนดำเนินการกับไฟล์จริง
9. เพิ่ม automated tests สำหรับ scoring, grouping และ user flow
10. ทดสอบกับรูปจริงหลายประเภทและอุปกรณ์มือถือหลายขนาด

## 12. ข้อควรระวังสำหรับการพัฒนา backend

- ต้องตรวจสอบชนิดและขนาดไฟล์ซ้ำที่ฝั่ง server
- ไม่ควรเชื่อถือ MIME type จาก browser เพียงอย่างเดียว
- การประมวลผลภาพควรทำใน background job สำหรับงานที่ใช้เวลานาน
- ต้องแยกคำว่า recommendation ออกจาก delete action อย่างชัดเจน
- การลบรูปจริงต้องได้รับการยืนยันจากผู้ใช้ทุกครั้ง
- ควรเก็บคะแนนย่อยและเหตุผลเพื่อให้ผลลัพธ์อธิบายได้
- ต้องกำหนดนโยบายจัดเก็บและลบไฟล์ที่คำนึงถึงความเป็นส่วนตัวของผู้ใช้

## 13. สถานะโดยสรุป

Frontend prototype อยู่ในสถานะพร้อมใช้สำหรับสาธิตแนวคิดและรับ feedback ด้าน
UX/UI แล้ว โครงสร้างรองรับการเปลี่ยน mock data เป็น data-access layer ในอนาคต
โดยไม่จำเป็นต้องออกแบบหน้าจอใหม่ทั้งหมด งานหลักที่ยังเหลือคือ image processing,
backend integration, persistence และการทดสอบด้วยข้อมูลจริง
