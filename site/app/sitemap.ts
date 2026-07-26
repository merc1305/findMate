import type { MetadataRoute } from "next";

const SITE_URL = "https://findmate-owner-network.xvwbgtt855.chatgpt.site";

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: SITE_URL,
      changeFrequency: "weekly",
      priority: 1,
    },
  ];
}
