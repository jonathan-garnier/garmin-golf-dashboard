import fs from "node:fs";
import path from "node:path";
import RoundDetailClient from "@/components/RoundDetailClient";

// Pre-render one static page per round id (required for `output: export`).
// Ids come from the JSON the Python exporter writes to public/data/.
export function generateStaticParams() {
  try {
    const p = path.join(process.cwd(), "public", "data", "round-ids.json");
    const ids = JSON.parse(fs.readFileSync(p, "utf-8")) as number[];
    return ids.map((id) => ({ id: String(id) }));
  } catch {
    return [];
  }
}

// Only the ids above exist as static pages.
export const dynamicParams = false;

export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <RoundDetailClient id={id} />;
}
