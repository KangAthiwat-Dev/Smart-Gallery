"use client";

import Image from "next/image";
import Link from "next/link";
import type { ChangeEvent, DragEvent } from "react";
import { useEffect, useRef, useState } from "react";
import { ArrowRight, ImagePlus, Images, Trash2, X } from "lucide-react";

import { Button, buttonVariants } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

type SelectedPhoto = {
  id: string;
  file: File;
  previewUrl: string;
};

export function PhotoUpload() {
  const inputRef = useRef<HTMLInputElement>(null);

  const [photos, setPhotos] = useState<SelectedPhoto[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const photosRef = useRef<SelectedPhoto[]>([]);

  useEffect(() => {
    photosRef.current = photos;
  }, [photos]);

  useEffect(() => {
    return () => {
      photosRef.current.forEach((photo) => {
        URL.revokeObjectURL(photo.previewUrl);
      });
    };
  }, []);

  function createFileKey(file: File) {
    return `${file.name}-${file.size}-${file.lastModified}`;
  }

  function addFiles(files: File[]) {
    const imageFiles = files.filter((file) =>
      file.type.startsWith("image/")
    );

    if (imageFiles.length !== files.length) {
      setMessage("Some files were skipped because they are not images.");
    } else {
      setMessage(null);
    }

    setPhotos((currentPhotos) => {
      const existingFiles = new Set(
        currentPhotos.map((photo) => createFileKey(photo.file))
      );

      const newPhotos = imageFiles.flatMap((file) => {
        const fileKey = createFileKey(file);

        if (existingFiles.has(fileKey)) {
          return [];
        }

        existingFiles.add(fileKey);

        return [
          {
            id: crypto.randomUUID(),
            file,
            previewUrl: URL.createObjectURL(file),
          },
        ];
      });

      return [...currentPhotos, ...newPhotos];
    });
  }

  function handleInputChange(event: ChangeEvent<HTMLInputElement>) {
    if (!event.target.files) return;

    addFiles(Array.from(event.target.files));

    // Allow a removed file to be selected again.
    event.target.value = "";
  }

  function handleDrop(event: DragEvent<HTMLButtonElement>) {
    event.preventDefault();

    setIsDragging(false);

    addFiles(Array.from(event.dataTransfer.files));
  }

  function removePhoto(id: string) {
    setPhotos((currentPhotos) => {
      const target = currentPhotos.find(
        (photo) => photo.id === id
      );

      if (target) {
        URL.revokeObjectURL(target.previewUrl);
      }

      return currentPhotos.filter((photo) => photo.id !== id);
    });
  }

  function clearPhotos() {
    photos.forEach((photo) => {
      URL.revokeObjectURL(photo.previewUrl);
    });

    setPhotos([]);
    setMessage(null);
  }

  const totalSize = photos.reduce(
    (total, photo) => total + photo.file.size,
    0
  );

  return (
    <div className="space-y-6">
      <input
        ref={inputRef}
        id="photo-upload"
        type="file"
        accept="image/*"
        multiple
        className="hidden"
        onChange={handleInputChange}
        tabIndex={-1}
      />

      <Button
        type="button"
        variant="ghost"
        aria-label="Choose photos to analyze"
        aria-describedby="photo-upload-help"
        onClick={() => inputRef.current?.click()}
        onDragEnter={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={(event) => {
          const nextTarget = event.relatedTarget;

          if (
            !(nextTarget instanceof Node) ||
            !event.currentTarget.contains(nextTarget)
          ) {
            setIsDragging(false);
          }
        }}
        onDrop={handleDrop}
        className={[
          "h-auto w-full whitespace-normal rounded-xl border-2 border-dashed bg-card p-8 text-card-foreground shadow-none ring-1 ring-foreground/10 transition-colors",
          isDragging
            ? "border-primary bg-primary/5"
            : "hover:bg-muted/40",
        ].join(" ")}
      >
        <span className="flex flex-col items-center text-center">
          <span className="mb-4 flex size-14 items-center justify-center rounded-full bg-muted">
            <ImagePlus className="size-6" />
          </span>

          <span className="font-semibold">Choose your photos</span>

          <span
            id="photo-upload-help"
            className="mt-1 max-w-sm text-sm text-muted-foreground"
          >
            Select multiple photos or drag and drop them here.
          </span>
        </span>
      </Button>

      {message && (
        <p role="status" className="text-sm text-muted-foreground">
          {message}
        </p>
      )}

      {photos.length > 0 && (
        <>
          <div className="flex items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <Images className="size-4" />

                <h2 className="font-semibold">Selected photos</h2>
              </div>

              <p className="mt-1 text-sm text-muted-foreground">
                {photos.length} photos · {formatBytes(totalSize)}
              </p>
            </div>

            <Button
              variant="outline"
              size="sm"
              type="button"
              onClick={clearPhotos}
            >
              <Trash2 />
              Clear
            </Button>
          </div>

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
            {photos.map((photo) => (
              <SelectedPhotoCard
                key={photo.id}
                photo={photo}
                onRemove={() => removePhoto(photo.id)}
              />
            ))}
          </div>

          <Card className="p-4">
            <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
              <div>
                <p className="font-medium">Photos ready</p>

                <p className="text-sm text-muted-foreground">
                  Prototype mode uses sample analysis results. Your selected
                  files stay in this browser session.
                </p>
              </div>

              <Link
                href="/gallery"
                className={buttonVariants({ size: "lg" })}
              >
                View sample analysis
                <ArrowRight />
              </Link>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}

function SelectedPhotoCard({
  photo,
  onRemove,
}: {
  photo: SelectedPhoto;
  onRemove: () => void;
}) {
  return (
    <div className="group relative overflow-hidden rounded-xl bg-muted">
      <div className="relative aspect-4/5">
        <Image
          src={photo.previewUrl}
          alt=""
          fill
          unoptimized
          sizes="(min-width: 1024px) 20vw, (min-width: 640px) 25vw, 50vw"
          className="object-cover"
        />
      </div>

      <Button
        type="button"
        variant="secondary"
        size="icon"
        className="absolute right-2 top-2 size-8 opacity-100 shadow-sm sm:opacity-0 sm:group-hover:opacity-100 sm:focus-visible:opacity-100"
        onClick={onRemove}
        aria-label={`Remove ${photo.file.name}`}
      >
        <X className="size-4" />
      </Button>

      <div className="absolute inset-x-0 bottom-0 bg-linear-to-t from-black/75 to-transparent p-3 pt-10 text-white">
        <p className="truncate text-xs font-medium">{photo.file.name}</p>

        <p className="text-[11px] text-white/70">
          {formatBytes(photo.file.size)}
        </p>
      </div>
    </div>
  );
}

function formatBytes(bytes: number) {
  if (bytes === 0) return "0 B";

  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    units.length - 1
  );

  return `${(bytes / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${
    units[index]
  }`;
}
