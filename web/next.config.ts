import type { NextConfig } from "next";

// Static-export mode is used only for the hosted (GitHub Pages) build, toggled
// by NEXT_PUBLIC_STATIC=1. Local `npm run dev` stays a normal app talking to the
// FastAPI backend. BASE_PATH is the Pages project sub-path
// (https://<user>.github.io/<repo>/), passed in by the deploy workflow.
const isStatic = process.env.NEXT_PUBLIC_STATIC === "1";
const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

const nextConfig: NextConfig = {
  ...(isStatic
    ? {
        output: "export",
        basePath,
        assetPrefix: basePath ? `${basePath}/` : undefined,
      }
    : {}),
  images: { unoptimized: true },
};

export default nextConfig;
