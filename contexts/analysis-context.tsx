"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  deleteAnalysis,
  persistAnalysis,
  restoreAnalysis,
} from "@/lib/analysis-storage";
import type { AnalysisSession } from "@/types/analysis";

type AnalysisContextValue = {
  analysis: AnalysisSession | null;
  isRestoring: boolean;
  storageWarning: string | null;
  setAnalysis: (analysis: AnalysisSession) => Promise<void>;
  clearAnalysis: () => Promise<void>;
};

const AnalysisContext = createContext<AnalysisContextValue | null>(null);

export function AnalysisProvider({ children }: { children: ReactNode }) {
  const [analysis, setAnalysisState] = useState<AnalysisSession | null>(null);
  const [isRestoring, setIsRestoring] = useState(true);
  const [storageWarning, setStorageWarning] = useState<string | null>(null);
  const revision = useRef(0);

  useEffect(() => {
    let active = true;
    const currentRevision = revision.current;
    restoreAnalysis()
      .then((saved) => {
        if (active && revision.current === currentRevision)
          setAnalysisState(saved);
      })
      .catch(() => {
        if (active)
          setStorageWarning(
            "เรียกคืนผลที่บันทึกไว้ไม่ได้ คุณยังวิเคราะห์รูปในแท็บนี้ได้",
          );
      })
      .finally(() => {
        if (active) setIsRestoring(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const setAnalysis = useCallback(async (next: AnalysisSession) => {
    revision.current += 1;
    setAnalysisState(next);
    setStorageWarning(null);
    try {
      await persistAnalysis(next);
    } catch {
      // Remove a stale saved result so a reload cannot silently show the previous run.
      await deleteAnalysis().catch(() => {});
      setStorageWarning(
        "ดูผลในแท็บนี้ได้ แต่บันทึกไว้เปิดต่อหลังรีเฟรชไม่ได้ พื้นที่เก็บข้อมูลของเบราว์เซอร์อาจเต็ม",
      );
    }
  }, []);

  const clearAnalysis = useCallback(async () => {
    revision.current += 1;
    try {
      await deleteAnalysis();
      setAnalysisState(null);
      setStorageWarning(null);
    } catch {
      setStorageWarning(
        "ล้างผลวิเคราะห์ที่บันทึกไว้ไม่สำเร็จ กรุณาลองอีกครั้ง",
      );
    }
  }, []);

  return (
    <AnalysisContext.Provider
      value={{
        analysis,
        isRestoring,
        storageWarning,
        setAnalysis,
        clearAnalysis,
      }}
    >
      {children}
    </AnalysisContext.Provider>
  );
}

export function useAnalysis() {
  const context = useContext(AnalysisContext);
  if (!context)
    throw new Error("useAnalysis must be used inside AnalysisProvider");
  return context;
}
