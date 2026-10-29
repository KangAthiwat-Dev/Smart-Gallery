import type { AnalysisSession } from "@/types/analysis";

const DATABASE = "smart-gallery";
const STORE = "sessions";
// Reanalyze stored time-only groups after adding the separate timed-pHash rule.
const STORAGE_VERSION = 6;

function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DATABASE, 1);
    request.onupgradeneeded = () => request.result.createObjectStore(STORE);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
    request.onblocked = () => reject(new Error("Session storage is blocked."));
  });
}

async function transaction<T>(
  mode: IDBTransactionMode,
  operation: (store: IDBObjectStore) => IDBRequest<T>,
): Promise<T> {
  const database = await openDatabase();
  return new Promise((resolve, reject) => {
    const tx = database.transaction(STORE, mode);
    const request = operation(tx.objectStore(STORE));
    tx.oncomplete = () => {
      database.close();
      resolve(request.result);
    };
    tx.onerror = () => {
      database.close();
      reject(tx.error);
    };
    tx.onabort = () => {
      database.close();
      reject(tx.error);
    };
  });
}

export async function restoreAnalysis(): Promise<AnalysisSession | null> {
  const value = await transaction("readonly", (store) => store.get("latest"));
  return value?.storageVersion === STORAGE_VERSION ? value.analysis : null;
}

export async function persistAnalysis(
  analysis: AnalysisSession,
): Promise<void> {
  await transaction("readwrite", (store) =>
    store.put({ storageVersion: STORAGE_VERSION, analysis }, "latest"),
  );
}

export async function deleteAnalysis(): Promise<void> {
  await transaction("readwrite", (store) => store.delete("latest"));
}
