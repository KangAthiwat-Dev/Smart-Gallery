import { Badge } from "@/components/ui/badge";
import type { Recommendation } from "@/types/analysis";

type Props = {
  status: Recommendation;
};

export function StatusBadge({ status }: Props) {
  if (status === "KEEP") {
    return (
      <Badge className="bg-emerald-600 hover:bg-emerald-600">
        Keep
      </Badge>
    );
  }

  if (status === "REVIEW") {
    return (
      <Badge className="bg-amber-500 hover:bg-amber-500">
        Review
      </Badge>
    );
  }

  return <Badge variant="destructive">Recommend Delete</Badge>;
}
