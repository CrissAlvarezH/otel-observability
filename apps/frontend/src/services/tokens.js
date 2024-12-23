import { AUTH_DOMAIN } from "../lib/config";


export async function getTokens() {
  const res = await fetch(`${AUTH_DOMAIN}/tokens`);
  if (!res.ok) {
    throw new Error("Failed to get tokens");
  }
  return res.json();
}
