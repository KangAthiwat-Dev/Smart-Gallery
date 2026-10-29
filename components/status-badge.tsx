import { Badge } from "@/components/ui/badge";
import type { Recommendation } from "@/types/analysis";

type Props = {
  status: Recommendation;
};

export function StatusBadge({ status }: Props) {
  if (status === "KEEP") {
    return (
      <Badge className="bg-emerald-600 text-white hover:bg-emerald-600">
        แนะนำให้เก็บ
      </Badge>
    );
  }

  if (status === "REVIEW") {
    return (
      <Badge className="bg-amber-500 text-white hover:bg-amber-500">
        ควรตรวจสอบ
      </Badge>
    );
  }

  return (
    <Badge className="bg-red-600 text-white hover:bg-red-600">แนะนำให้ลบ</Badge>
  );
}
