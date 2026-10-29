"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  useEffect,
  useRef,
  useState,
  type ChangeEvent,
  type DragEvent,
} from "react";
import {
  ArrowRight,
  FolderOpen,
  ImagePlus,
  Images,
  LoaderCircle,
  Trash2,
  X,
} from "lucide-react";

import { Button, buttonVariants } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useAnalysis } from "@/contexts/analysis-context";
import {
  analyzePhotos,
  MAX_FILES,
  MAX_FILE_BYTES,
  MAX_TOTAL_BYTES,
  SUPPORTED_EXTENSIONS,
} from "@/lib/api";
import type { AnalysisInput } from "@/lib/api";
import { formatBytes } from "@/lib/locale-th";

type SelectedPhoto = AnalysisInput & { previewUrl: string };

function fileKey(file: File) {
  return `${file.webkitRelativePath || file.name}:${file.size}:${file.lastModified}`;
}
export function PhotoUpload() {
  const router = useRouter();
  const { analysis, isRestoring, setAnalysis, storageWarning } = useAnalysis();
  const inputRef = useRef<HTMLInputElement>(null);
  const folderRef = useRef<HTMLInputElement>(null);
  const selectedRef = useRef<SelectedPhoto[]>([]);
  const requestRef = useRef<AbortController | null>(null);
  const busyRef = useRef(false);
  const [photos, setPhotos] = useState<SelectedPhoto[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(
    () => () => {
      requestRef.current?.abort();
      selectedRef.current.forEach((photo) =>
        URL.revokeObjectURL(photo.previewUrl),
      );
    },
    [],
  );

  function addFiles(files: File[]) {
    if (busyRef.current) return;
    const next = [...selectedRef.current];
    const seen = new Set(next.map((photo) => fileKey(photo.file)));
    let total = next.reduce((sum, photo) => sum + photo.file.size, 0);
    let skipped = 0;
    for (const file of [...files].sort((a, b) =>
      (a.webkitRelativePath || a.name).localeCompare(
        b.webkitRelativePath || b.name,
      ),
    )) {
      if (!SUPPORTED_EXTENSIONS.test(file.name) || seen.has(fileKey(file))) {
        skipped += 1;
        continue;
      }
      if (
        file.size > MAX_FILE_BYTES ||
        next.length >= MAX_FILES ||
        total + file.size > MAX_TOTAL_BYTES
      ) {
        skipped += 1;
        continue;
      }
      seen.add(fileKey(file));
      total += file.size;
      next.push({
        id: crypto.randomUUID(),
        file,
        relativePath: file.webkitRelativePath || file.name,
        previewUrl: URL.createObjectURL(file),
      });
    }
    selectedRef.current = next;
    setPhotos(next);
    setMessage(
      skipped
        ? `ข้าม ${skipped} ไฟล์ เนื่องจากไม่รองรับ ไฟล์ซ้ำ หรือเกินขีดจำกัดที่กำหนด`
        : null,
    );
    setError(null);
  }

  function handleInputChange(event: ChangeEvent<HTMLInputElement>) {
    if (event.target.files) addFiles(Array.from(event.target.files));
    event.target.value = "";
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragging(false);
    if (busyRef.current) return;
    if (
      Array.from(event.dataTransfer.items).some(
        (item) => item.webkitGetAsEntry?.()?.isDirectory,
      )
    ) {
      setMessage(
        "หากต้องการเลือกรูปในโฟลเดอร์และโฟลเดอร์ย่อย ให้ใช้ปุ่มเลือกโฟลเดอร์",
      );
      return;
    }
    addFiles(Array.from(event.dataTransfer.files));
  }

  function removePhoto(id: string) {
    if (busyRef.current) return;
    const target = selectedRef.current.find((photo) => photo.id === id);
    const next = selectedRef.current.filter((photo) => photo.id !== id);
    selectedRef.current = next;
    setPhotos(next);
    if (target) URL.revokeObjectURL(target.previewUrl);
  }

  function clearPhotos() {
    if (busyRef.current) return;
    selectedRef.current.forEach((photo) =>
      URL.revokeObjectURL(photo.previewUrl),
    );
    selectedRef.current = [];
    setPhotos([]);
    setMessage(null);
    setError(null);
  }

  async function handleAnalyze() {
    if (!selectedRef.current.length || busyRef.current || isRestoring) return;
    busyRef.current = true;
    setIsAnalyzing(true);
    setError(null);
    const controller = new AbortController();
    requestRef.current = controller;
    try {
      const result = await analyzePhotos(
        [...selectedRef.current],
        controller.signal,
      );
      if (controller.signal.aborted) return;
      await setAnalysis({ ...result, completedAt: new Date().toISOString() });
      if (!controller.signal.aborted) router.push("/gallery");
    } catch (error) {
      if (!controller.signal.aborted) {
        setError(
          error instanceof Error
            ? error.message
            : "วิเคราะห์รูปไม่สำเร็จ กรุณาลองอีกครั้ง",
        );
      }
    } finally {
      if (!controller.signal.aborted) {
        busyRef.current = false;
        setIsAnalyzing(false);
      }
    }
  }

  const totalSize = photos.reduce((sum, photo) => sum + photo.file.size, 0);

  return (
    <div className="space-y-6 pb-28" aria-busy={isAnalyzing}>
      <input
        ref={inputRef}
        type="file"
        accept=".jpg,.jpeg,.png,.bmp,.webp,.heic,.heif"
        multiple
        hidden
        aria-label="เลือกไฟล์รูป"
        onChange={handleInputChange}
        disabled={isAnalyzing}
      />
      <input
        ref={(element) => {
          folderRef.current = element;
          element?.setAttribute("webkitdirectory", "");
        }}
        type="file"
        multiple
        hidden
        aria-label="เลือกโฟลเดอร์รูป"
        onChange={handleInputChange}
        disabled={isAnalyzing}
      />

      <Card
        onDragEnter={(event) => {
          event.preventDefault();
          if (!isAnalyzing) setIsDragging(true);
        }}
        onDragOver={(event) => {
          event.preventDefault();
          event.dataTransfer.dropEffect = isAnalyzing ? "none" : "copy";
        }}
        onDragLeave={(event) => {
          if (
            !(event.relatedTarget instanceof Node) ||
            !event.currentTarget.contains(event.relatedTarget)
          ) {
            setIsDragging(false);
          }
        }}
        onDrop={handleDrop}
        className={`border-2 border-dashed p-8 transition-colors ${isDragging ? "border-primary bg-primary/5" : ""}`}
      >
        <div className="flex flex-col items-center text-center">
          <div className="mb-4 flex size-14 items-center justify-center rounded-full bg-muted">
            <ImagePlus className="size-6" />
          </div>
          <h2 className="font-semibold">เลือกรูปที่ต้องการวิเคราะห์</h2>
          <p className="mt-1 max-w-md text-sm text-muted-foreground">
            เลือกทีละหลายรูป หรือเลือกโฟลเดอร์พร้อมโฟลเดอร์ย่อย
            และลากไฟล์รูปมาวางที่นี่ได้
          </p>
          <div className="mt-5 flex flex-wrap justify-center gap-3">
            <Button
              type="button"
              onClick={() => inputRef.current?.click()}
              disabled={isAnalyzing}
              className="min-h-11"
            >
              <Images /> เลือกรูป
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => folderRef.current?.click()}
              disabled={isAnalyzing}
              className="min-h-11"
            >
              <FolderOpen /> เลือกโฟลเดอร์
            </Button>
          </div>
          <p className="mt-4 text-xs text-muted-foreground">
            รองรับ JPG, PNG, BMP, WebP และ HEIC/HEIF · สูงสุด 200 รูป · ไม่เกิน
            30 MB ต่อไฟล์ และรวมไม่เกิน 200 MB
          </p>
        </div>
      </Card>

      {analysis && (
        <Link
          href="/gallery"
          className={buttonVariants({ variant: "outline" })}
        >
          ดูผลวิเคราะห์ล่าสุด
        </Link>
      )}
      {storageWarning && (
        <p role="status" className="text-sm text-muted-foreground">
          {storageWarning}
        </p>
      )}
      {message && (
        <p role="status" className="text-sm text-muted-foreground">
          {message}
        </p>
      )}
      {error && (
        <p
          role="alert"
          className="rounded-xl border border-destructive/30 p-4 text-sm text-destructive"
        >
          {error}
        </p>
      )}

      {photos.length > 0 && (
        <>
          <div className="flex items-center justify-between gap-4">
            <div>
              <h2 className="flex items-center gap-2 font-semibold">
                <Images className="size-4" /> รูปที่เลือก
              </h2>
              <p
                className="mt-1 text-sm text-muted-foreground"
                aria-live="polite"
              >
                {photos.length} รูป · {formatBytes(totalSize)}
              </p>
            </div>
            <Button
              variant="outline"
              type="button"
              onClick={clearPhotos}
              disabled={isAnalyzing}
            >
              <Trash2 /> ล้างรายการ
            </Button>
          </div>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
            {photos.map((photo) => (
              <SelectedPhotoCard
                key={photo.id}
                photo={photo}
                disabled={isAnalyzing}
                onRemove={() => removePhoto(photo.id)}
              />
            ))}
          </div>
          <p className="text-sm text-muted-foreground">
            รูปจะถูกส่งไปยังระบบวิเคราะห์ โดยไม่แก้ไขไฟล์ต้นฉบับ
            ผลวิเคราะห์และรูปตัวอย่างจะบันทึกไว้ในเบราว์เซอร์นี้เพื่อเปิดดูต่อหลังรีเฟรช
          </p>
          <div className="fixed right-4 bottom-[max(1rem,env(safe-area-inset-bottom))] z-40 max-w-[calc(100vw-2rem)] rounded-2xl border bg-background/95 p-3 shadow-xl backdrop-blur sm:right-6">
            <Button
              type="button"
              size="lg"
              className="min-h-12 px-5"
              onClick={handleAnalyze}
              disabled={isAnalyzing || isRestoring}
            >
              {isAnalyzing ? (
                <LoaderCircle className="animate-spin" />
              ) : (
                <ArrowRight />
              )}
              {isAnalyzing
                ? "กำลังวิเคราะห์รูป…"
                : `วิเคราะห์ ${photos.length} รูป`}
            </Button>
            <p
              role="status"
              className="mt-1 text-center text-xs text-muted-foreground"
            >
              {isAnalyzing
                ? "กรุณารอสักครู่ จำนวนรูปมากจะใช้เวลานานขึ้น"
                : formatBytes(totalSize)}
            </p>
          </div>
        </>
      )}
    </div>
  );
}

function SelectedPhotoCard({
  photo,
  disabled,
  onRemove,
}: {
  photo: SelectedPhoto;
  disabled: boolean;
  onRemove: () => void;
}) {
  const [failed, setFailed] = useState(/\.(heic|heif)$/i.test(photo.file.name));
  return (
    <div className="group relative overflow-hidden rounded-xl bg-muted">
      <div className="relative aspect-4/5">
        {failed ? (
          <div className="flex size-full flex-col items-center justify-center gap-2 p-4 text-center text-xs text-muted-foreground">
            <ImagePlus className="size-7" /> จะแสดงรูปตัวอย่างหลังวิเคราะห์
          </div>
        ) : (
          <Image
            src={photo.previewUrl}
            alt=""
            fill
            unoptimized
            sizes="(min-width: 1024px) 20vw, 50vw"
            className="object-cover"
            onError={() => setFailed(true)}
          />
        )}
      </div>
      <Button
        type="button"
        variant="secondary"
        size="icon"
        disabled={disabled}
        className="absolute right-2 top-2 size-9 shadow-sm"
        onClick={onRemove}
        aria-label={`นำ ${photo.relativePath} ออกจากรายการ`}
      >
        <X className="size-4" />
      </Button>
      <div className="absolute inset-x-0 bottom-0 bg-linear-to-t from-black/80 to-transparent p-3 pt-10 text-white">
        <p className="truncate text-xs font-medium" title={photo.relativePath}>
          {photo.relativePath}
        </p>
        <p className="text-[11px] text-white/80">
          {formatBytes(photo.file.size)}
        </p>
      </div>
    </div>
  );
}
