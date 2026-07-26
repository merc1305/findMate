import type { MetadataRoute } from "next";

const SITE_URL = "https://findmate-owner-network.xvwbgtt855.chatgpt.site";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
    },
    sitemap: `${SITE_URL}/sitemap.xml`,
    host: SITE_URL,
  };
}
