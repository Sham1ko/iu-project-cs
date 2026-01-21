const rawBaseUrl = import.meta.env.VITE_API_BASE_URL;

if (!rawBaseUrl) {
  throw new Error("VITE_API_BASE_URL is required. Set it in frontend/.env.");
}

const isAbsolute = /^https?:\/\//i.test(rawBaseUrl);
const isRelative = rawBaseUrl.startsWith("/");
const useProxy = import.meta.env.DEV && isAbsolute;

export const API_BASE_URL = useProxy ? "/api" : rawBaseUrl;
export const API_PREFIX = useProxy || isRelative ? "/v1" : "/api/v1";
